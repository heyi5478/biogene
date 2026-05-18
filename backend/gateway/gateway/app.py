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
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from shared.condition import hit_summary
from shared.data_loader import validate
from shared.logging import (
    configure_logging,
    install_exception_handlers,
    install_middleware,
)
from shared.schemas import (
    ConditionRequest,
    PatientBundle,
    PatientListPage,
)

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
    params: dict | None = None,
) -> Any:
    try:
        resp = await client.get(url, headers=headers, params=params)
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


def _project_list_item(patient: dict, opd_bundle: dict, labs_bundle: dict) -> dict:
    """Build a slim ``PatientListItem`` payload from a base row + per-module bundles.

    Drops every module detail array; keeps only the summary counts and the
    most recent opd visitDate.
    """
    opd_rows = opd_bundle.get("opd", []) or []
    visit_dates = [r.get("visitDate") for r in opd_rows if r.get("visitDate")]
    return {
        **patient,
        "dnabankCount": len(labs_bundle.get("dnabank", []) or []),
        "outbankCount": len(labs_bundle.get("outbank", []) or []),
        "lastVisitDate": max(visit_dates) if visit_dates else None,
    }


async def _fetch_list_items_for_patients(
    client: httpx.AsyncClient,
    patients: list[dict],
    headers: dict,
) -> list[dict]:
    """Fan out to opd/labs/diseases batches and project ``PatientListItem[]``.

    The diseases bundle is fetched but discarded — none of the slim list
    fields depend on disease modules. We still hit the endpoint to keep the
    fan-out shape uniform with the detail flow and to surface 502s early
    if svc-disease is unreachable.
    """
    if not patients:
        return []
    ids = [p["patientId"] for p in patients]
    opd_task = _post_json(
        client, "svc-patient", f"{SVC_PATIENT_URL}/opd/batch",
        {"patientIds": ids}, headers=headers,
    )
    labs_task = _post_json(
        client, "svc-lab", f"{SVC_LAB_URL}/labs/batch",
        {"patientIds": ids}, headers=headers,
    )
    diseases_task = _post_json(
        client, "svc-disease", f"{SVC_DISEASE_URL}/diseases/batch",
        {"patientIds": ids}, headers=headers,
    )
    opd_map, labs_map, _ = await asyncio.gather(opd_task, labs_task, diseases_task)
    return [
        _project_list_item(
            p,
            opd_map.get(p["patientId"], {}),
            labs_map.get(p["patientId"], {}),
        )
        for p in patients
    ]


@app.get("/patients", response_model=PatientListPage)
async def list_patients(
    request: Request,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    assert _client is not None, "httpx client not initialized"
    headers = {"X-Request-ID": request.state.request_id}

    params: dict = {"limit": limit, "offset": offset}
    if q:
        params["q"] = q
    page = await _get_json(
        _client, "svc-patient", f"{SVC_PATIENT_URL}/patients",
        headers=headers, params=params,
    )
    if page is None:
        raise _Upstream502("svc-patient", "unexpected 404 on /patients")

    items = await _fetch_list_items_for_patients(_client, page["items"], headers)
    return {
        "items": items,
        "total": page["total"],
        "limit": page["limit"],
        "offset": page["offset"],
    }


# Which downstream service owns each moduleId. Anything not in
# _PATIENT_MODULES or _LAB_MODULES is routed to svc-disease (the disease
# service catches everything else, including unknown modules — its
# condition-match endpoint returns [] for ids it doesn't index).
_PATIENT_MODULES = frozenset({"basic", "opd"})
_LAB_MODULES = frozenset({"aa", "msms", "biomarker", "outbank", "dnabank"})


def _records_for_module(
    module_id: str,
    patient: dict,
    opd_bundle: dict,
    labs_bundle: dict,
    diseases_bundle: dict,
) -> list[dict]:
    if module_id == "basic":
        return [patient]
    if module_id == "opd":
        return opd_bundle.get("opd", []) or []
    if module_id in _LAB_MODULES:
        return labs_bundle.get(module_id, []) or []
    return diseases_bundle.get(module_id, []) or []


@app.post("/patients/condition-query", response_model=PatientListPage)
async def condition_query(
    req: ConditionRequest,
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    assert _client is not None, "httpx client not initialized"
    headers = {"X-Request-ID": request.state.request_id}

    if not req.conditions:
        return {"items": [], "total": 0, "limit": limit, "offset": offset}

    # Bucket conditions by owning service, remembering original index so we
    # can stitch per-condition results back together for AND/OR combination.
    patient_bucket: list[tuple[int, dict]] = []
    lab_bucket: list[tuple[int, dict]] = []
    disease_bucket: list[tuple[int, dict]] = []
    for i, cond in enumerate(req.conditions):
        entry = (i, cond.model_dump())
        if cond.moduleId in _PATIENT_MODULES:
            patient_bucket.append(entry)
        elif cond.moduleId in _LAB_MODULES:
            lab_bucket.append(entry)
        else:
            disease_bucket.append(entry)

    async def _call(service: str, url: str, bucket: list[tuple[int, dict]]) -> list[list[str]]:
        if not bucket:
            return []
        body = {"conditions": [c for _, c in bucket], "logic": req.logic}
        resp = await _post_json(_client, service, url, body, headers=headers)
        return resp.get("conditionMatches", [])

    patient_res, lab_res, disease_res = await asyncio.gather(
        _call("svc-patient", f"{SVC_PATIENT_URL}/patients/condition-match", patient_bucket),
        _call("svc-lab", f"{SVC_LAB_URL}/labs/condition-match", lab_bucket),
        _call("svc-disease", f"{SVC_DISEASE_URL}/diseases/condition-match", disease_bucket),
    )

    per_cond_sets: list[set[str]] = [set() for _ in req.conditions]
    for (orig_i, _), pids in zip(patient_bucket, patient_res):
        per_cond_sets[orig_i] = set(pids)
    for (orig_i, _), pids in zip(lab_bucket, lab_res):
        per_cond_sets[orig_i] = set(pids)
    for (orig_i, _), pids in zip(disease_bucket, disease_res):
        per_cond_sets[orig_i] = set(pids)

    if req.logic == "AND":
        combined: set[str] = set.intersection(*per_cond_sets)
    else:
        combined = set.union(*per_cond_sets)

    if not combined:
        return {"items": [], "total": 0, "limit": limit, "offset": offset}

    # ``combined`` is a set with no stable iteration order; sort by patientId
    # before slicing so the same (conditions, logic, limit, offset) yields a
    # stable page. ``total`` is the full match count, not the page size.
    total = len(combined)
    page_ids = sorted(combined)[offset : offset + limit]

    # Resolve full base rows for the page ids via a batch id lookup — O(1)
    # per id in svc-patient. Hydrating only the page keeps every downstream
    # batch body bounded to <= limit ids, well within the gateway timeout.
    base_by_pid = await _post_json(
        _client, "svc-patient", f"{SVC_PATIENT_URL}/patients/batch",
        {"patientIds": page_ids}, headers=headers,
    )
    selected = [base_by_pid[pid] for pid in page_ids if pid in base_by_pid]

    # Fan out batches for slim summary AND hit-summary computation.
    ids = [p["patientId"] for p in selected]
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

    items: list[dict] = []
    for p in selected:
        pid = p["patientId"]
        opd_b = opd_map.get(pid, {})
        labs_b = labs_map.get(pid, {})
        diseases_b = diseases_map.get(pid, {})
        item = _project_list_item(p, opd_b, labs_b)
        hits: list[str] = []
        for i, cond in enumerate(req.conditions):
            if pid not in per_cond_sets[i]:
                continue
            records = _records_for_module(cond.moduleId, p, opd_b, labs_b, diseases_b)
            summary = hit_summary(records, cond.moduleId, cond.fieldId)
            if summary:
                hits.append(summary)
        item["conditionHits"] = hits
        items.append(item)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


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
