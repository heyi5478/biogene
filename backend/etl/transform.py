#!/usr/bin/env python3
"""1.0-mdb transform — convert legacy CSV exports to 3.0 row dicts.

Reads the per-table CSVs that ``extract_mdb.sh`` produced and the
``blob_paths.json`` from ``extract_blobs_mdb.py``, then emits one
transformed CSV per (target_schema, target_table) under
``<out_dir>/transformed/main_<table>.csv``.

Three concrete responsibilities:

1. Column name remap — 1.0 used English names like ``ptinfo.chartno``
   while 3.0 (aligned with 2.0) uses ``patient.chartno``. Per-table
   transformer functions handle this.

2. ``patient_id`` synthesis — both legacy patient tables (``ptinfo`` and
   the Chinese-named ``patient``) use ``chartno`` as the natural key, so
   ``uuid5(NAMESPACE_OID, "main:" + chartno)`` produces the canonical
   3.0 ``patient_id`` and incidentally deduplicates rows that exist in
   both tables.

3. BLOB path join — for sample rows whose source table had a BLOB column
   (``MSDATA``/``GCDATA``/``MPSUDATA``/``ENZYME``), look up the
   ``blob_paths.json`` entry and set ``raw_data_path`` accordingly.

Two source-specific merges:
- MPSUDATA columns map onto the widened ``main.gag`` columns (od,
  urine_creatinine, mggag, twos, twos_cre).
- GCDATA rows feed the brand-new ``main.gcms`` table.

Usage:
    python backend/etl/transform.py <out_dir>

Where <out_dir> is the same directory passed to extract_mdb.sh; we read
from there and write transformed/ alongside.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import uuid
from collections.abc import Iterable
from pathlib import Path

NAMESPACE_OID = uuid.NAMESPACE_OID


def _patient_uuid(chartno: str) -> str:
    """Canonical 3.0 patient_id from a 1.0 chartno (matches mock-data spec)."""
    return str(uuid.uuid5(NAMESPACE_OID, f"main:{chartno}"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _write_csv(path: Path, rows: Iterable[dict], fieldnames: list[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})
    return len(rows)


# ── per-table transformers ──────────────────────────────────────────────────

def transform_patient(ptinfo: list[dict], patient_zh: list[dict]) -> list[dict]:
    """Merge 1.0 ``ptinfo`` (English) and ``patient`` (Chinese) on chartno.

    Both tables key by ``chartno``; we keep one row per chartno. Where a
    field is present in both, prefer the Chinese ``patient`` row (newer
    schema) — ``referring_doctor`` only exists there.
    """
    by_chartno: dict[str, dict] = {}

    # Older English-named table first.
    for r in ptinfo:
        chartno = r.get("chartno")
        if not chartno:
            continue
        by_chartno[chartno] = {
            "patientId": _patient_uuid(chartno),
            "source": "main",
            "chartno": chartno,
            "name": r.get("name") or "",
            "birthday": r.get("birthday") or None,
            "sex": r.get("sex") or "",
            "diagnosis": r.get("diagnosis") or None,
        }

    # Newer Chinese-named table overlays — provides referring_doctor.
    for r in patient_zh:
        chartno = r.get("chartno")
        if not chartno:
            continue
        existing = by_chartno.setdefault(
            chartno,
            {
                "patientId": _patient_uuid(chartno),
                "source": "main",
                "chartno": chartno,
            },
        )
        for src_col, dst_col in (
            ("name", "name"),
            ("birthday", "birthday"),
            ("sex", "sex"),
            ("diagnosis", "diagnosis"),
            ("referring_doctor", "referring_doctor"),
            # Chinese table sometimes uses these alt names:
            ("doctor", "referring_doctor"),
        ):
            if r.get(src_col):
                existing[dst_col] = r[src_col]

    return list(by_chartno.values())


def transform_msms_with_blobs(rows: list[dict], blob_paths: dict[str, str]) -> list[dict]:
    out = []
    for r in rows:
        chartno = r.get("chartno", "")
        if not chartno:
            continue
        sampleno = r.get("sampleno") or ""
        out.append({
            "patientId": _patient_uuid(chartno),
            "sampleName": sampleno,
            "specimenType": r.get("specimentype") or "DBS",
            "result": r.get("result") or "",
            "raw_data_path": blob_paths.get(sampleno),
            "ntubiogene_sampleno": sampleno,
            "v2_source_schema": "1.0-mdb",
        })
    return out


def transform_gcms(rows: list[dict], blob_paths: dict[str, str]) -> list[dict]:
    """GCDATA → main.gcms (brand-new in 3.0)."""
    out = []
    for r in rows:
        chartno = r.get("chartno", "")
        if not chartno:
            continue
        sampleno = r.get("sampleno") or ""
        out.append({
            "patientId": _patient_uuid(chartno),
            "sampleName": sampleno,
            "specimenType": r.get("specimentype"),
            "result": r.get("result"),
            "rawDataPath": blob_paths.get(sampleno),
            "collectDate": r.get("collectdate") or r.get("date"),
            "notes": r.get("notes"),
            "ntubiogene_sampleno": sampleno,
            "v2_source_schema": "1.0-mdb",
        })
    return out


def transform_mpsu_into_gag(mpsu_rows: list[dict]) -> list[dict]:
    """MPSUDATA → widened main.gag rows.

    The MPSUDATA columns ``od``/``urinecreatinine``/``mggag``/``twos``/
    ``twoscre`` populate the new gag fields added by §8.4.
    """
    out = []
    for r in mpsu_rows:
        chartno = r.get("chartno", "")
        if not chartno:
            continue
        out.append({
            "patientId": _patient_uuid(chartno),
            "sampleName": r.get("sampleno", ""),
            "specimenType": r.get("specimentype") or "Urine",
            "technician": r.get("technician") or "",
            "result": r.get("result") or "",
            "od": r.get("od"),
            "urineCreatinine": r.get("urinecreatinine"),
            "mggag": r.get("mggag"),
            "twos": r.get("twos"),
            "twosCre": r.get("twoscre"),
            "ntubiogene_sampleno": r.get("sampleno") or "",
            "v2_source_schema": "1.0-mdb",
        })
    return out


# ── orchestrator ─────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("out_dir", type=Path, help="directory containing extract_mdb.sh output")
    args = p.parse_args()

    src = args.out_dir
    if not src.is_dir():
        sys.exit(f"not a directory: {src}")

    blob_index = json.loads((src / "blob_paths.json").read_text()) \
        if (src / "blob_paths.json").exists() else {}

    transformed = src / "transformed"

    # Patient — merge ptinfo + 中文 patient.
    ptinfo = _read_csv(src / "ptinfo.csv")
    patient_zh = _read_csv(src / "patient.csv")
    patient_rows = transform_patient(ptinfo, patient_zh)
    n = _write_csv(
        transformed / "main_patient.csv",
        patient_rows,
        fieldnames=[
            "patientId", "source", "name", "birthday", "sex", "chartno",
            "external_chartno", "nbs_id", "category",
            "diagnosis", "diagnosis2", "diagnosis3",
            "referring_doctor",
        ],
    )
    print(f"main.patient    {n} rows")

    # MSDATA → main.msms (with raw_data_path)
    msms = transform_msms_with_blobs(
        _read_csv(src / "MSDATA.csv"), blob_index.get("msms", {})
    )
    n = _write_csv(
        transformed / "main_msms.csv",
        msms,
        fieldnames=["patientId", "sampleName", "specimenType", "result",
                    "raw_data_path", "ntubiogene_sampleno", "v2_source_schema"],
    )
    print(f"main.msms       {n} rows  (with raw_data_path)")

    # GCDATA → main.gcms (new table)
    gcms = transform_gcms(
        _read_csv(src / "GCDATA.csv"), blob_index.get("gcms", {})
    )
    n = _write_csv(
        transformed / "main_gcms.csv",
        gcms,
        fieldnames=["patientId", "sampleName", "specimenType", "result",
                    "rawDataPath", "collectDate", "notes",
                    "ntubiogene_sampleno", "v2_source_schema"],
    )
    print(f"main.gcms       {n} rows")

    # MPSUDATA → widened main.gag
    gag = transform_mpsu_into_gag(_read_csv(src / "MPSUDATA.csv"))
    n = _write_csv(
        transformed / "main_gag.csv",
        gag,
        fieldnames=["patientId", "sampleName", "specimenType", "technician", "result",
                    "DMGGAG", "CREATININE",
                    "od", "urineCreatinine", "mggag", "twos", "twosCre",
                    "ntubiogene_sampleno", "v2_source_schema"],
    )
    print(f"main.gag        {n} rows  (widened with MPSUDATA fields)")

    # TODO: AAM/MSM/DNAITEM/ENZYMEITEM/COMMAND ref tables — see §10.3.
    print(f"\ntransformed CSVs in {transformed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
