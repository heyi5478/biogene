"""svc-patient — serves merged patient base records and opd visit history.

Runs at ``127.0.0.1:8001``. Reads ``{db_main,db_external,db_nbs}/patient.json``
and ``{db_main,db_external,db_nbs}/opd.json`` once at startup into in-memory
caches, then serves them via HTTP. This service is internal — the gateway
(port 8000) is the only external caller.
"""

from __future__ import annotations

import logging
import sys
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from shared.data_loader import load_all, validate
from shared.schemas import OpdBundle, Patient

log = logging.getLogger("svc-patient")

# In-memory cache populated in lifespan. Dict for O(1) single-patient lookup,
# plus an ordered list to preserve JSON file order for GET /patients.
_patients_by_id: dict[str, dict] = {}
_patients_list: list[dict] = []
_opd_by_id: dict[str, list[dict]] = defaultdict(list)


def _opd_bundle_for(patient_id: str) -> dict[str, list[dict]]:
    return {"opd": list(_opd_by_id.get(patient_id, []))}


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        validate()
    except ValueError as e:
        log.error("%s", e)
        sys.exit(1)
    log.info("mock-data FK validation passed")

    data = load_all()
    _patients_list.clear()
    _patients_by_id.clear()
    _opd_by_id.clear()
    for db_name in ("db_main", "db_external", "db_nbs"):
        tables = data.get(db_name, {})
        for row in tables.get("patient", []):
            _patients_list.append(row)
            _patients_by_id[row["patientId"]] = row
        for row in tables.get("opd", []):
            pid = row.get("patientId")
            if pid is None:
                continue
            _opd_by_id[pid].append(row)
    log.info(
        "loaded %d patients and %d opd rows into svc-patient cache",
        len(_patients_list),
        sum(len(v) for v in _opd_by_id.values()),
    )
    yield


app = FastAPI(title="svc-patient", lifespan=lifespan)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": "svc-patient"}


@app.get("/patients", response_model=list[Patient])
def list_patients() -> list[dict]:
    return _patients_list


@app.get("/patients/{patient_id}", response_model=Patient)
def get_patient(patient_id: str) -> dict:
    row = _patients_by_id.get(patient_id)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "patient_not_found", "patientId": patient_id},
        )
    return row


@app.get("/opd/{patient_id}", response_model=OpdBundle)
def get_opd(patient_id: str) -> dict:
    return _opd_bundle_for(patient_id)


class _BatchRequest(BaseModel):
    patientIds: list[str]


@app.post("/opd/batch", response_model=dict[str, OpdBundle])
def batch_opd(req: _BatchRequest) -> dict[str, dict[str, list[dict]]]:
    """Return ``{patientId: OpdBundle}`` for every requested id.

    Missing ids get an empty bundle — matches svc-lab / svc-disease shape.
    """

    return {pid: _opd_bundle_for(pid) for pid in req.patientIds}


# FastAPI's default HTTPException handler wraps `detail` under {"detail": ...}.
# We want the error body to be the object itself (matching the spec's shape).
from fastapi.exceptions import RequestValidationError  # noqa: E402
from starlette.exceptions import HTTPException as StarletteHTTPException  # noqa: E402


@app.exception_handler(StarletteHTTPException)
async def _http_exc(_, exc: StarletteHTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
