"""svc-lab — common lab records (AA / MS/MS / biomarker / outbank / dnabank).

Runs at ``127.0.0.1:8002``. Loads the five lab tables from all three databases
at startup and indexes them by ``patientId`` for O(1) per-patient lookup.
"""

from __future__ import annotations

import logging
import sys
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from pydantic import BaseModel

from shared.data_loader import load_all, validate
from shared.schemas import LabBundle

log = logging.getLogger("svc-lab")

_LAB_TABLES = ("aa", "msms", "biomarker", "outbank", "dnabank")
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": "svc-lab"}


@app.get("/labs/{patient_id}", response_model=LabBundle)
def get_labs(patient_id: str) -> dict:
    return _bundle_for(patient_id)


class _BatchRequest(BaseModel):
    patientIds: list[str]


@app.post("/labs/batch", response_model=dict[str, LabBundle])
def batch_labs(req: _BatchRequest) -> dict[str, dict[str, list[dict]]]:
    """Return ``{patientId: LabBundle}`` for every requested id.

    Missing ids get an empty bundle — the gateway is responsible for verifying
    patient existence via svc-patient.
    """

    return {pid: _bundle_for(pid) for pid in req.patientIds}
