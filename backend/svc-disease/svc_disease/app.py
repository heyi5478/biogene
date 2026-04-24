"""svc-disease — disease-module records (main-DB disease panels + NBS screens).

Runs at ``127.0.0.1:8003``. Loads:

* ``db_main/{aadc,ald,mma,mps2,lsd,enzyme,gag}``
* ``db_nbs/{bd,cah,cah_tgal,dmd,dmd_tsh,g6pd,sma_scid}``

NBS sub-tables are joined in memory (``cah_tgal`` by ``cahId`` into its parent
``cah`` row's ``tgal`` list; ``dmd_tsh`` by ``dmdId`` into ``tsh``).
"""

from __future__ import annotations

import sys
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from pydantic import BaseModel

from shared.data_loader import load_all, validate
from shared.logging import (
    configure_logging,
    install_exception_handlers,
    install_middleware,
)
from shared.schemas import DiseaseBundle

log = configure_logging("svc-disease")

# Module -> which database owns it. Output key is the dict key; db/table the value.
_MAIN_MODULES = {
    "aadc": "aadc",
    "ald": "ald",
    "mma": "mma",
    "mps2": "mps2",
    "lsd": "lsd",
    "enzyme": "enzyme",
    "gag": "gag",
}
_NBS_SIMPLE_MODULES = {
    "bd": "bd",
    "g6pd": "g6pd",
    "smaScid": "sma_scid",
}

_ALL_OUTPUT_KEYS = (
    *_MAIN_MODULES.keys(),
    *_NBS_SIMPLE_MODULES.keys(),
    "cah",
    "dmd",
)

# output_key -> patientId -> list[row]
_index: dict[str, dict[str, list[dict]]] = {k: defaultdict(list) for k in _ALL_OUTPUT_KEYS}


def _empty_bundle() -> dict[str, list[dict]]:
    return {k: [] for k in _ALL_OUTPUT_KEYS}


def _bundle_for(patient_id: str) -> dict[str, list[dict]]:
    return {k: list(_index[k].get(patient_id, [])) for k in _ALL_OUTPUT_KEYS}


def _join_cah_tgal(cah_rows: list[dict], tgal_rows: list[dict]) -> list[dict]:
    """Attach ``cah_tgal`` rows onto their parent ``cah`` row via ``cahId``."""
    tgal_by_cah: dict[str, list[dict]] = defaultdict(list)
    for row in tgal_rows:
        cah_id = row.get("cahId")
        if cah_id is None:
            continue
        rest = {k: v for k, v in row.items() if k != "cahId"}
        tgal_by_cah[cah_id].append(rest)
    joined: list[dict] = []
    for cah in cah_rows:
        merged = {**cah, "tgal": list(tgal_by_cah.get(cah.get("cahId", ""), []))}
        joined.append(merged)
    return joined


def _join_dmd_tsh(dmd_rows: list[dict], tsh_rows: list[dict]) -> list[dict]:
    """Attach ``dmd_tsh`` rows onto their parent ``dmd`` row via ``dmdId``."""
    tsh_by_dmd: dict[str, list[dict]] = defaultdict(list)
    for row in tsh_rows:
        dmd_id = row.get("dmdId")
        if dmd_id is None:
            continue
        rest = {k: v for k, v in row.items() if k != "dmdId"}
        tsh_by_dmd[dmd_id].append(rest)
    joined: list[dict] = []
    for dmd in dmd_rows:
        merged = {**dmd, "tsh": list(tsh_by_dmd.get(dmd.get("dmdId", ""), []))}
        joined.append(merged)
    return joined


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        validate()
    except ValueError as e:
        log.error("%s", e)
        sys.exit(1)
    log.info("mock-data FK validation passed")

    data = load_all()
    for k in _ALL_OUTPUT_KEYS:
        _index[k].clear()

    main_tables = data.get("db_main", {})
    for out_key, table in _MAIN_MODULES.items():
        for row in main_tables.get(table, []):
            pid = row.get("patientId")
            if pid is None:
                continue
            _index[out_key][pid].append(row)

    nbs_tables = data.get("db_nbs", {})
    for out_key, table in _NBS_SIMPLE_MODULES.items():
        for row in nbs_tables.get(table, []):
            pid = row.get("patientId")
            if pid is None:
                continue
            _index[out_key][pid].append(row)

    cah_joined = _join_cah_tgal(
        nbs_tables.get("cah", []), nbs_tables.get("cah_tgal", [])
    )
    for row in cah_joined:
        pid = row.get("patientId")
        if pid is None:
            continue
        _index["cah"][pid].append(row)

    dmd_joined = _join_dmd_tsh(
        nbs_tables.get("dmd", []), nbs_tables.get("dmd_tsh", [])
    )
    for row in dmd_joined:
        pid = row.get("patientId")
        if pid is None:
            continue
        _index["dmd"][pid].append(row)

    total = sum(sum(len(v) for v in idx.values()) for idx in _index.values())
    log.info("svc-disease indexed %d rows across %d modules", total, len(_ALL_OUTPUT_KEYS))
    yield


app = FastAPI(title="svc-disease", lifespan=lifespan)
install_middleware(app, log)
install_exception_handlers(app, log)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": "svc-disease"}


@app.get("/diseases/{patient_id}", response_model=DiseaseBundle)
def get_diseases(patient_id: str) -> dict:
    return _bundle_for(patient_id)


class _BatchRequest(BaseModel):
    patientIds: list[str]


@app.post("/diseases/batch", response_model=dict[str, DiseaseBundle])
def batch_diseases(req: _BatchRequest) -> dict[str, dict[str, list[dict]]]:
    return {pid: _bundle_for(pid) for pid in req.patientIds}
