"""Gateway — the frontend-facing BFF on port 8000.

Fans requests out to svc-patient (8001), svc-lab (8002), svc-disease (8003)
in parallel via a lifespan-scoped ``httpx.AsyncClient`` and merges the
responses into ``PatientBundle`` objects whose shape matches the frontend's
``Patient`` TypeScript type.

* Any downstream 5xx / connection error collapses to HTTP 502 with
  ``{"error": "upstream_unavailable", "service": "<name>"}``.
* 404 from svc-patient on ``GET /patients/{id}`` is propagated as 404 with
  ``{"error": "patient_not_found", "patientId": "<id>"}`` — no fan-out.
* CORS is open only for ``http://localhost:5173`` (Vite dev server).
"""

from __future__ import annotations

import asyncio
import os
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from shared.data_loader import validate
from shared.logging import (
    configure_logging,
    install_exception_handlers,
    install_middleware,
)
from shared.schemas import PatientBundle

log = configure_logging("gateway")

SVC_PATIENT_URL = os.getenv("SVC_PATIENT_URL", "http://127.0.0.1:8001")
SVC_LAB_URL = os.getenv("SVC_LAB_URL", "http://127.0.0.1:8002")
SVC_DISEASE_URL = os.getenv("SVC_DISEASE_URL", "http://127.0.0.1:8003")

CORS_ORIGIN = os.getenv("GATEWAY_CORS_ORIGIN", "http://localhost:5173")

# Lifespan-managed httpx client (None before startup / after shutdown).
_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    global _client
    try:
        validate()
    except ValueError as e:
        log.error("%s", e)
        sys.exit(1)
    log.info("mock-data FK validation passed")

    _client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
    log.info(
        "gateway ready (patient=%s lab=%s disease=%s)",
        SVC_PATIENT_URL, SVC_LAB_URL, SVC_DISEASE_URL,
    )
    try:
        yield
    finally:
        await _client.aclose()
        _client = None


app = FastAPI(title="gateway", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

install_middleware(app, log)
install_exception_handlers(app, log)


class _Upstream502(Exception):
    """Raised when a downstream service fails; mapped to HTTP 502 below."""

    def __init__(self, service: str, reason: str):
        super().__init__(f"{service}: {reason}")
        self.service = service
        self.reason = reason


async def _get_json(
    client: httpx.AsyncClient,
    service: str,
    url: str,
    *,
    headers: dict | None = None,
) -> Any:
    try:
        resp = await client.get(url, headers=headers)
    except httpx.HTTPError as e:
        raise _Upstream502(service, f"connection error: {e}") from e
    if resp.status_code >= 500:
        raise _Upstream502(service, f"status {resp.status_code}")
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise _Upstream502(service, f"unexpected status {resp.status_code}")
    try:
        return resp.json()
    except ValueError as e:
        raise _Upstream502(service, f"invalid JSON: {e}") from e


async def _post_json(
    client: httpx.AsyncClient,
    service: str,
    url: str,
    payload: dict,
    *,
    headers: dict | None = None,
) -> Any:
    try:
        resp = await client.post(url, json=payload, headers=headers)
    except httpx.HTTPError as e:
        raise _Upstream502(service, f"connection error: {e}") from e
    if resp.status_code >= 500 or resp.status_code < 200:
        raise _Upstream502(service, f"status {resp.status_code}")
    try:
        return resp.json()
    except ValueError as e:
        raise _Upstream502(service, f"invalid JSON: {e}") from e


def _merge_bundle(patient: dict, opd: dict, labs: dict, diseases: dict) -> dict:
    """Combine patient base row + opd + lab + disease bundles into one payload."""
    return {**patient, **opd, **labs, **diseases}


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": "gateway"}


@app.get("/patients", response_model=list[PatientBundle])
async def list_patients(request: Request) -> list[dict]:
    assert _client is not None, "httpx client not initialized"
    headers = {"X-Request-ID": request.state.request_id}

    patients = await _get_json(
        _client, "svc-patient", f"{SVC_PATIENT_URL}/patients", headers=headers
    )
    if patients is None:
        raise _Upstream502("svc-patient", "unexpected 404 on /patients")

    ids = [p["patientId"] for p in patients]

    opd_task = _post_json(
        _client, "svc-patient", f"{SVC_PATIENT_URL}/opd/batch",
        {"patientIds": ids}, headers=headers,
    )
    labs_task = _post_json(
        _client, "svc-lab", f"{SVC_LAB_URL}/labs/batch",
        {"patientIds": ids}, headers=headers,
    )
    diseases_task = _post_json(
        _client, "svc-disease", f"{SVC_DISEASE_URL}/diseases/batch",
        {"patientIds": ids}, headers=headers,
    )
    opd_map, labs_map, diseases_map = await asyncio.gather(
        opd_task, labs_task, diseases_task
    )

    return [
        _merge_bundle(
            p,
            opd_map.get(p["patientId"], {}),
            labs_map.get(p["patientId"], {}),
            diseases_map.get(p["patientId"], {}),
        )
        for p in patients
    ]


@app.get("/patients/{patient_id}", response_model=PatientBundle)
async def get_patient(patient_id: str, request: Request) -> dict:
    assert _client is not None, "httpx client not initialized"
    headers = {"X-Request-ID": request.state.request_id}

    patient = await _get_json(
        _client, "svc-patient", f"{SVC_PATIENT_URL}/patients/{patient_id}",
        headers=headers,
    )
    if patient is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "patient_not_found", "patientId": patient_id},
        )

    opd_task = _get_json(
        _client, "svc-patient", f"{SVC_PATIENT_URL}/opd/{patient_id}",
        headers=headers,
    )
    labs_task = _get_json(
        _client, "svc-lab", f"{SVC_LAB_URL}/labs/{patient_id}",
        headers=headers,
    )
    diseases_task = _get_json(
        _client, "svc-disease", f"{SVC_DISEASE_URL}/diseases/{patient_id}",
        headers=headers,
    )
    opd, labs, diseases = await asyncio.gather(opd_task, labs_task, diseases_task)
    if opd is None:
        raise _Upstream502("svc-patient", "unexpected 404 on /opd")
    if labs is None:
        raise _Upstream502("svc-lab", "unexpected 404")
    if diseases is None:
        raise _Upstream502("svc-disease", "unexpected 404")

    return _merge_bundle(patient, opd, labs, diseases)


@app.exception_handler(_Upstream502)
async def _upstream_handler(request: Request, exc: _Upstream502) -> JSONResponse:
    rid = getattr(request.state, "request_id", None) or "-"
    log.warning(
        "upstream failure request_id=%s service=%s reason=%s",
        rid, exc.service, exc.reason,
    )
    return JSONResponse(
        status_code=502,
        content={"error": "upstream_unavailable", "service": exc.service},
    )


@app.exception_handler(StarletteHTTPException)
async def _http_exc(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
