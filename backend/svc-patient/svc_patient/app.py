"""svc-patient — serves merged patient base records from all three databases.

Runs at ``127.0.0.1:8001``. Reads ``{db_main,db_external,db_nbs}/patient.json``
once at startup into an in-memory cache, then serves them via HTTP. This
service is internal — the gateway (port 8000) is the only external caller.
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from shared.data_loader import load_all, validate
from shared.schemas import Patient

log = logging.getLogger("svc-patient")

# In-memory cache populated in lifespan. Dict for O(1) single-patient lookup,
# plus an ordered list to preserve JSON file order for GET /patients.
_patients_by_id: dict[str, dict] = {}
_patients_list: list[dict] = []


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
    for db_name in ("db_main", "db_external", "db_nbs"):
        for row in data.get(db_name, {}).get("patient", []):
            _patients_list.append(row)
            _patients_by_id[row["patientId"]] = row
    log.info("loaded %d patients into svc-patient cache", len(_patients_list))
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


# FastAPI's default HTTPException handler wraps `detail` under {"detail": ...}.
# We want the error body to be the object itself (matching the spec's shape).
from fastapi.exceptions import RequestValidationError  # noqa: E402
from starlette.exceptions import HTTPException as StarletteHTTPException  # noqa: E402


@app.exception_handler(StarletteHTTPException)
async def _http_exc(_, exc: StarletteHTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
