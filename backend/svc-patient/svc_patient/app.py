"""svc-patient — serves merged patient base records and opd visit history.

Runs at ``127.0.0.1:8001``. Reads ``{db_main,db_external,db_nbs}/patient.json``
and ``{db_main,db_external,db_nbs}/opd.json`` once at startup into in-memory
caches, then serves them via HTTP. This service is internal — the gateway
(port 8000) is the only external caller.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from shared.condition import match_records
from shared.data_loader import load_all, validate
from shared.logging import (
    configure_logging,
    install_exception_handlers,
    install_middleware,
)
from shared.schemas import (
    ConditionMatchResponse,
    ConditionRequest,
    OpdBundle,
    Patient,
    PatientPage,
)

log = configure_logging("svc-patient")

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
install_middleware(app, log)
install_exception_handlers(app, log)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": "svc-patient"}


@app.get("/patients", response_model=PatientPage)
def list_patients(
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    """Return a page of patient base rows, optionally filtered by ``q``.

    Mirrors ``frontend/src/pages/Index.tsx:81-91``: ``name`` matches by
    case-sensitive substring; ``chartno``/``externalChartno``/``nbsId``
    match by case-insensitive substring. The ``q`` filter is applied
    before the page slice, so ``total`` is the full filtered count.
    """
    if q is None or q == "":
        filtered: list[dict] = _patients_list
    else:
        q_lower = q.lower()
        filtered = []
        for p in _patients_list:
            name = p.get("name") or ""
            if q in name:
                filtered.append(p)
                continue
            for key in ("chartno", "externalChartno", "nbsId"):
                v = p.get(key)
                if v and q_lower in v.lower():
                    filtered.append(p)
                    break
    total = len(filtered)
    return {
        "items": filtered[offset : offset + limit],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.post("/patients/condition-match", response_model=ConditionMatchResponse)
def condition_match(req: ConditionRequest) -> dict:
    """Return per-condition matched patientIds for the modules svc-patient owns.

    ``basic`` evaluates against the patient base row itself; ``opd``
    evaluates against the patient's opd visit history. Conditions on
    other modules return an empty list (the gateway routes them to
    svc-lab / svc-disease).
    """
    out: list[list[str]] = []
    for cond in req.conditions:
        matched: list[str] = []
        if cond.moduleId == "basic":
            for p in _patients_list:
                if match_records(
                    [p], cond.fieldId, cond.operator, cond.value, cond.value2
                ):
                    matched.append(p["patientId"])
        elif cond.moduleId == "opd":
            for p in _patients_list:
                pid = p["patientId"]
                if match_records(
                    _opd_by_id.get(pid, []),
                    cond.fieldId,
                    cond.operator,
                    cond.value,
                    cond.value2,
                ):
                    matched.append(pid)
        out.append(matched)
    return {"conditionMatches": out}


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


@app.post("/patients/batch", response_model=dict[str, Patient])
def batch_patients(req: _BatchRequest) -> dict[str, dict]:
    """Return ``{patientId: Patient}`` for every requested id that exists.

    Unknown ids are omitted — a ``Patient`` has required fields, so no
    placeholder row is possible. Lets the gateway resolve a known set of
    patients' base rows without fetching the whole table.
    """

    return {
        pid: _patients_by_id[pid]
        for pid in req.patientIds
        if pid in _patients_by_id
    }


# FastAPI's default HTTPException handler wraps `detail` under {"detail": ...}.
# We want the error body to be the object itself (matching the spec's shape).
from fastapi.exceptions import RequestValidationError  # noqa: E402
from starlette.exceptions import HTTPException as StarletteHTTPException  # noqa: E402


@app.exception_handler(StarletteHTTPException)
async def _http_exc(_, exc: StarletteHTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
