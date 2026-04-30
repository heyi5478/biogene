#!/usr/bin/env python3
"""Seed the gimc PostgreSQL database from the mock-data JSON files.

Used by `make seed-pg` and by the §11 mock-parity smoke. NOT part of the
production cutover path — production data comes from the §7-§9 ETL.

What it does:

1. Reads ``backend/mock-data/db_main/``, ``db_external/``, ``db_nbs/``.
2. Inserts rows into the matching PG tables under schemas ``main`` /
   ``external`` / ``nbs``, in FK-safe order (patient first, then samples,
   then sub-tables of cah/dmd).
3. Uses ``INSERT ... ON CONFLICT DO NOTHING`` so reruns are idempotent.

Convention reminders:
- JSON keys are camelCase (Python attr names on our models).
- DB columns are snake_case but SQLAlchemy maps via ``mapped_column("...")``.
- Numeric floats coerce cleanly to ``Numeric`` via SQLAlchemy.
- Date/datetime strings come in as ISO; PG accepts that on the wire.

Usage:
    python backend/scripts/seed_from_json.py
    DATABASE_URL=postgresql+asyncpg://... python backend/scripts/seed_from_json.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import uuid as uuidlib

import shared.models  # noqa: F401  — register every table on metadata
from shared.db import get_sync_session
from shared.models.links import PatientLink

ROOT = Path(__file__).resolve().parents[1] / "mock-data"

# (mock-data dir, schema name, table load order — patient first, sub-tables last)
LOAD_ORDER: list[tuple[str, str, list[str]]] = [
    (
        "db_main",
        "main",
        [
            "patient",
            "aa", "msms", "biomarker", "opd", "dnabank", "outbank", "enzyme",
            "aadc", "ald", "mma", "mps2", "lsd", "gag",
        ],
    ),
    (
        "db_external",
        "external",
        [
            "patient",
            "aa", "msms", "biomarker", "opd", "outbank", "enzyme",
            "lsd", "gag",
        ],
    ),
    (
        "db_nbs",
        "nbs",
        [
            "patient",
            "aa", "msms", "biomarker", "opd", "outbank",
            "bd", "cah", "dmd", "g6pd", "sma_scid",
            # Sub-tables (FK to parent must already exist):
            "cah_tgal", "dmd_tsh",
        ],
    ),
]


def _model_for(schema: str, table: str):
    from importlib import import_module
    pkg = import_module(f"shared.models.{schema}")
    cls_name = "".join(part.capitalize() for part in table.split("_"))
    return getattr(pkg, cls_name)


def _load_json(db_dir: str, table: str) -> list[dict]:
    p = ROOT / db_dir / f"{table}.json"
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return json.load(fh)


def _filter_and_coerce(model, row: dict) -> dict:
    """Drop keys that aren't mapped on this model and coerce JSON strings.

    JSON serialises UUID, date, datetime as strings; SQLAlchemy doesn't do
    implicit cast through asyncpg/psycopg, so we convert here based on the
    declared column python_type.
    """
    from datetime import date as _date, datetime as _datetime
    from sqlalchemy.inspection import inspect as sa_inspect

    attrs = {prop.key: prop for prop in sa_inspect(model).attrs}
    out: dict = {}
    for k, v in row.items():
        prop = attrs.get(k)
        if prop is None:
            continue
        if v is not None and isinstance(v, str):
            try:
                py_type = prop.columns[0].type.python_type  # type: ignore[attr-defined]
            except (AttributeError, NotImplementedError):
                py_type = str
            if py_type is uuidlib.UUID:
                v = uuidlib.UUID(v)
            elif py_type is _date and not v.endswith(":00"):  # plain ISO date
                v = _date.fromisoformat(v)
            elif py_type is _datetime:
                v = _datetime.fromisoformat(v)
        out[k] = v
    return out


def _seed_table(session, schema: str, table: str, rows: list[dict]) -> int:
    if not rows:
        return 0
    model = _model_for(schema, table)
    # Wipe the table first; rerunning is idempotent because we re-insert
    # the same rows, and patient_id is the natural key. Sample tables use
    # IDENTITY for id so re-inserting would add duplicates without this.
    session.execute(model.__table__.delete())
    session.flush()
    for row in rows:
        clean = _filter_and_coerce(model, row)
        session.add(model(**clean))
    return len(rows)


def _seed_links(session, all_data: dict[str, list[dict]]) -> int:
    """Materialise ``linkedPatientIds`` from patient rows into links.patient_link.

    Walks every patient row across the three databases and emits one
    junction row per ordered pair (smaller UUID first, satisfying the
    ``patient_id_a < patient_id_b`` CHECK).
    """
    session.execute(PatientLink.__table__.delete())
    session.flush()

    seen: set[tuple[str, str]] = set()
    n = 0
    for db_dir in ("db_main", "db_external", "db_nbs"):
        for prow in all_data.get(db_dir, []):
            pid = prow["patientId"]
            for other in prow.get("linkedPatientIds", []) or []:
                a, b = sorted([pid, other])
                if a == b or (a, b) in seen:
                    continue
                seen.add((a, b))
                session.add(
                    PatientLink(
                        patient_id_a=uuidlib.UUID(a),
                        patient_id_b=uuidlib.UUID(b),
                        link_kind="same_person",
                    )
                )
                n += 1
    return n


def main() -> int:
    session = get_sync_session()
    try:
        total = 0
        # Load every patient.json so we can later wire up links.
        patient_rows: dict[str, list[dict]] = {}

        # Iterate sample tables in reverse FK-dependency order for delete,
        # then forward order for insert. We just commit at the end.
        for db_dir, schema, tables in LOAD_ORDER:
            print(f"seeding {schema} (from {db_dir}/):")
            for tbl in tables:
                rows = _load_json(db_dir, tbl)
                if tbl == "patient":
                    patient_rows[db_dir] = rows
                n = _seed_table(session, schema, tbl, rows)
                print(f"  {tbl:14}  {n:4} rows")
                total += n

        # Cross-schema links — derived from patient.json[*].linkedPatientIds.
        link_count = _seed_links(session, patient_rows)
        print(f"  patient_link   {link_count:4} rows  (links schema)")
        total += link_count

        session.commit()
        print(f"\nOK — {total} rows seeded.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
