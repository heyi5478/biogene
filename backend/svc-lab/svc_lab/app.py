"""svc-lab — common lab records (AA / MS/MS / biomarker / outbank / dnabank).

Runs at ``127.0.0.1:8002``. Loads the five lab tables from all three databases
at startup and indexes them by ``patientId`` for O(1) per-patient lookup.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
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
    GcmsRecord,
    LabBundle,
)

log = configure_logging("svc-lab")

# gcms only exists in main (introduced by 1.0 ETL — no 2.0 equivalent).
_LAB_TABLES = ("aa", "msms", "biomarker", "outbank", "dnabank", "gcms")
_DB_DIRS = ("db_main", "db_external", "db_nbs")

# table -> patientId -> list[row]
_index: dict[str, dict[str, list[dict]]] = {t: defaultdict(list) for t in _LAB_TABLES}


def _empty_bundle() -> dict[str, list[dict]]:
    return {t: [] for t in _LAB_TABLES}


def _bundle_for(patient_id: str) -> dict[str, list[dict]]:
    return {t: list(_index[t].get(patient_id, [])) for t in _LAB_TABLES}


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        validate()
    except ValueError as e:
        log.error("%s", e)
        sys.exit(1)
    log.info("mock-data FK validation passed")

    data = load_all()
    total = 0
    for t in _LAB_TABLES:
        _index[t].clear()
    for db in _DB_DIRS:
        tables = data.get(db, {})
        for t in _LAB_TABLES:
            for row in tables.get(t, []):
                pid = row.get("patientId")
                if pid is None:
                    continue
                _index[t][pid].append(row)
                total += 1
    log.info("svc-lab indexed %d lab rows across %d tables", total, len(_LAB_TABLES))
    yield


app = FastAPI(title="svc-lab", lifespan=lifespan)
install_middleware(app, log)
install_exception_handlers(app, log)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": "svc-lab"}


@app.get("/labs/{patient_id}", response_model=LabBundle)
def get_labs(patient_id: str) -> dict:
    return _bundle_for(patient_id)


@app.get("/labs/{patient_id}/gcms", response_model=list[GcmsRecord])
def get_gcms(patient_id: str) -> list[dict]:
    """Per-patient GC-MS records — empty list if none.

    Added by §13.1 of postgres-data-backend; populated by the 1.0 ETL
    (GCDATA → main.gcms). 2.0 had no GC-MS equivalent.
    """
    return list(_index["gcms"].get(patient_id, []))


class _BatchRequest(BaseModel):
    patientIds: list[str]


@app.post("/labs/batch", response_model=dict[str, LabBundle])
def batch_labs(req: _BatchRequest) -> dict[str, dict[str, list[dict]]]:
    """Return ``{patientId: LabBundle}`` for every requested id.

    Missing ids get an empty bundle — the gateway is responsible for verifying
    patient existence via svc-patient.
    """

    return {pid: _bundle_for(pid) for pid in req.patientIds}


# Modules svc-lab owns. Conditions whose moduleId isn't here return [].
_LAB_MODULES = frozenset({"aa", "msms", "biomarker", "outbank", "dnabank"})


@app.post("/labs/condition-match", response_model=ConditionMatchResponse)
def condition_match(req: ConditionRequest) -> dict:
    """Per-condition matched patientIds for the lab modules.

    For each inbound condition, walks the corresponding ``_index`` table
    and collects every patientId with at least one record satisfying the
    condition. Conditions on modules outside ``_LAB_MODULES`` return [].
    """
    out: list[list[str]] = []
    for cond in req.conditions:
        if cond.moduleId not in _LAB_MODULES:
            out.append([])
            continue
        table = _index[cond.moduleId]
        matched: list[str] = []
        for pid, rows in table.items():
            if match_records(
                rows, cond.fieldId, cond.operator, cond.value, cond.value2
            ):
                matched.append(pid)
        out.append(matched)
    return {"conditionMatches": out}
