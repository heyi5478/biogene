"""Dual-backend facade: ``GIMC_DATA_BACKEND`` selects ``json`` or ``postgres``.

Service code calls :func:`load_all` and :func:`validate` exactly the same
way regardless of backend — that's the contract from `postgres-data-backend`
spec ("service Python source MUST be bit-equal across the two modes").

JSON path (`json`, default)
    Reads ``backend/mock-data/db_main/`` etc. Validation is in-memory FK
    sweep over loaded dicts.

PostgreSQL path (`postgres`)
    Reads from the live ``gimc`` database via the sync SQLAlchemy engine
    in :mod:`shared.db`. Validation is a per-sample-table ``LEFT JOIN …
    IS NULL`` sweep that fails fast on the first orphan row.

Returns the same shape either way::

    {
        "db_main":     {"patient": [...], "aa": [...], ...},
        "db_external": {"patient": [...], ...},
        "db_nbs":      {"patient": [...], "cah": [...], "cah_tgal": [...], ...},
    }

Row dicts use camelCase keys aligned with ``schemas.py`` (so the same dict
can flow into Pydantic without renaming). Internal-only columns
(``id``, ``created_at``, ``updated_at``, ``ntubiogene_sampleno``,
``v2_source_schema``) are filtered out so the key set matches the JSON
path exactly.
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

# JSON-path public API (re-exported for backwards compatibility) — pulled in
# only when JSON backend is selected.
_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# Schema → mock-data dir-name → list of tables in load order.
# (FK-safe: patient first, then sub-tables of cah/dmd come after their parents.)
_PG_SCHEMAS: list[tuple[str, str, list[str]]] = [
    (
        "main",
        "db_main",
        [
            "patient",
            "aa",
            "msms",
            "biomarker",
            "opd",
            "dnabank",
            "outbank",
            "enzyme",
            # disease modules (§12.1)
            "aadc",
            "ald",
            "mma",
            "mps2",
            "lsd",
            "gag",
            # 1.0 ETL additions (§8.4) — gcms has no 2.0 source so it's
            # always empty in JSON dev mode (mock-data/db_main/gcms.json = []).
            "gcms",
        ],
    ),
    (
        "external",
        "db_external",
        [
            "patient",
            "aa",
            "msms",
            "biomarker",
            "opd",
            "outbank",
            "enzyme",
            # disease modules mirrored from main (§12.3)
            "lsd",
            "gag",
        ],
    ),
    (
        "nbs",
        "db_nbs",
        [
            "patient",
            "aa",
            "msms",
            "biomarker",
            "opd",
            "outbank",
            "bd",
            "cah",
            "cah_tgal",
            "dmd",
            "dmd_tsh",
            "g6pd",
            "sma_scid",
        ],
    ),
]

# Sub-tables that don't have their own patient_id (linkage is via parent).
# Mirrors load_mock.SUB_TABLE_FKS but typed for FK queries.
_SUB_TABLES: dict[str, list[tuple[str, str, str]]] = {
    # schema → [(sub_table, parent_table, parent_pk_column)]
    "nbs": [
        ("cah_tgal", "cah", "cah_id"),
        ("dmd_tsh", "dmd", "dmd_id"),
    ],
}


def _backend() -> str:
    return os.getenv("GIMC_DATA_BACKEND", "json").lower()


# ----- JSON backend ---------------------------------------------------------

def _load_from_json() -> dict[str, dict[str, list[dict]]]:
    from load_mock import load_all as _json_load  # type: ignore[import-not-found]
    return _json_load()


def _validate_json() -> None:
    from load_mock import validate as _json_validate  # type: ignore[import-not-found]
    _json_validate()


# ----- PostgreSQL backend ---------------------------------------------------

def _serialise_value(v: Any) -> Any:
    """Coerce a SQLAlchemy row value to JSON-friendly Python.

    ``schemas.py`` expects strings for ``patientId``, ``birthday``, etc., and
    floats for numeric fields. PG returns UUID/date/Decimal which Pydantic
    would reject, so we normalise at the boundary.
    """
    if v is None:
        return None
    if isinstance(v, uuid.UUID):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    return v


_INTERNAL_ATTRS: frozenset[str] = frozenset(
    # Mapper attribute names (Python-side, camelCase or snake_case for
    # internal-only fields) of columns we never expose to service code.
    {"id", "created_at", "updated_at", "ntubiogene_sampleno", "v2_source_schema"}
)


def _row_to_dict(row: Any, attrs: list[str]) -> dict[str, Any]:
    """Serialise an ORM row to a camelCase dict, dropping internal-only fields.

    ``attrs`` is the list of mapper attribute names (already camelCase for
    user-facing columns, snake_case for internal accounting columns).
    """
    out: dict[str, Any] = {}
    for k in attrs:
        if k in _INTERNAL_ATTRS:
            continue
        out[k] = _serialise_value(getattr(row, k))
    return out


def _model_for(schema_name: str, table: str):
    """Resolve a (schema, table) pair to its declarative model class."""
    from importlib import import_module
    pkg = import_module(f"shared.models.{schema_name}")
    # Convention: snake_case table name → CamelCase class name (e.g.
    # ``cah_tgal`` → ``CahTgal``). This matches every class we declared.
    cls_name = "".join(part.capitalize() for part in table.split("_"))
    return getattr(pkg, cls_name)


def _attrs_of(model) -> list[str]:
    """Return ORM mapper attribute names (Python-side keys) for ``model``."""
    from sqlalchemy.inspection import inspect as sa_inspect
    return [prop.key for prop in sa_inspect(model).attrs]


def _load_links(session) -> dict[str, list[str]]:
    """Materialise ``linkedPatientIds`` for every patient via UNION query."""
    from sqlalchemy import text
    rows = session.execute(
        text(
            "SELECT patient_id_a::text AS a, patient_id_b::text AS b "
            "FROM links.patient_link"
        )
    ).all()
    out: dict[str, list[str]] = {}
    for a, b in rows:
        out.setdefault(a, []).append(b)
        out.setdefault(b, []).append(a)
    return out


def _load_from_postgres() -> dict[str, dict[str, list[dict]]]:
    from sqlalchemy import select

    from shared.db import get_sync_session

    session = get_sync_session()
    try:
        out: dict[str, dict[str, list[dict]]] = {}

        for schema_name, db_key, tables in _PG_SCHEMAS:
            out[db_key] = {}
            for tbl in tables:
                model = _model_for(schema_name, tbl)
                rows = session.execute(select(model)).scalars().all()
                attrs = _attrs_of(model)
                out[db_key][tbl] = [_row_to_dict(r, attrs) for r in rows]

        # Decorate patient rows with linkedPatientIds (computed from junction
        # table — not a real column on patient).
        link_map = _load_links(session)
        for db_key in out:
            for prow in out[db_key].get("patient", []):
                prow["linkedPatientIds"] = link_map.get(prow["patientId"], [])

        return out
    finally:
        session.close()


def _validate_postgres() -> None:
    """FK integrity check via LEFT JOIN — first orphan raises ValueError."""
    from sqlalchemy import text

    from shared.db import get_sync_session

    session = get_sync_session()
    try:
        for schema_name, _db_key, tables in _PG_SCHEMAS:
            sub_tables = {
                st: (parent, parent_pk)
                for st, parent, parent_pk in _SUB_TABLES.get(schema_name, [])
            }
            for tbl in tables:
                if tbl == "patient":
                    continue
                if tbl in sub_tables:
                    parent, parent_pk = sub_tables[tbl]
                    sql = (
                        f"SELECT s.{parent_pk} FROM {schema_name}.{tbl} s "
                        f"LEFT JOIN {schema_name}.{parent} p "
                        f"  ON s.{parent_pk} = p.{parent_pk} "
                        f"WHERE p.{parent_pk} IS NULL LIMIT 1"
                    )
                    bad = session.execute(text(sql)).first()
                    if bad is not None:
                        raise ValueError(
                            f"FK violation: {schema_name}.{tbl}.{parent_pk}={bad[0]} "
                            f"not in {schema_name}.{parent}"
                        )
                else:
                    sql = (
                        f"SELECT s.patient_id FROM {schema_name}.{tbl} s "
                        f"LEFT JOIN {schema_name}.patient p "
                        f"  ON s.patient_id = p.patient_id "
                        f"WHERE p.patient_id IS NULL LIMIT 1"
                    )
                    bad = session.execute(text(sql)).first()
                    if bad is not None:
                        raise ValueError(
                            f"FK violation: {schema_name}.{tbl}.patient_id={bad[0]} "
                            f"not in {schema_name}.patient"
                        )
    finally:
        session.close()


# ----- Public API -----------------------------------------------------------

def load_all() -> dict[str, dict[str, list[dict]]]:
    """Return the full dataset keyed by mock-data dir name → table → rows.

    Backend selected by ``GIMC_DATA_BACKEND``: ``json`` (default) or
    ``postgres``. Both backends MUST return the same key set so service
    code is identical across the two modes (see spec mock-parity scenario).
    """
    if _backend() == "postgres":
        return _load_from_postgres()
    return _load_from_json()


def validate(data: dict | None = None) -> None:
    """Validate FK integrity and raise ValueError on the first violation.

    JSON path: walks the in-memory dict (cheap). PostgreSQL path: emits
    one ``LEFT JOIN`` per sample table and bails on the first orphan.

    The ``data`` argument is honoured only for the JSON backend (matches
    legacy ``load_mock.validate()`` signature). For the postgres backend
    the live DB is the source of truth.
    """
    if _backend() == "postgres":
        _validate_postgres()
        return
    # JSON path: preserve existing semantics — caller may pre-load.
    if data is None:
        _validate_json()
    else:
        # Lazy import to avoid forcing JSON deps on PG-only callers.
        from load_mock import _find_fk_errors  # type: ignore[import-not-found]
        errors = _find_fk_errors(data)
        if errors:
            raise ValueError(
                "mock-data FK validation failed:\n  - " + "\n  - ".join(errors)
            )


__all__ = ["load_all", "validate"]
