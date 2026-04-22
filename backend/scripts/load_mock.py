#!/usr/bin/env python3
"""Load JSON mock data and validate foreign-key integrity.

Usage:
    python backend/scripts/load_mock.py

Exits non-zero on dangling FK. Prints per-table row counts.

Public API (stable, consumed by FastAPI services via `backend.shared.data_loader`):
    load_all() -> dict[str, dict[str, list[dict]]]
        Return the full mock dataset keyed by database -> table -> rows.

    validate(data: dict | None = None) -> None
        If `data` is None, call `load_all()` first. Raise `ValueError`
        describing the offending database/table/row/field on any FK violation.
        Return `None` on success.

Standard library only (no third-party deps).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "mock-data"

DB_DIRS = ("db_main", "db_external", "db_nbs")

# Sub-table FKs: {db: [(sub_table, parent_id_field, parent_table, parent_pk)]}
SUB_TABLE_FKS: dict[str, list[tuple[str, str, str, str]]] = {
    "db_nbs": [
        ("cah_tgal", "cahId", "cah", "cahId"),
        ("dmd_tsh", "dmdId", "dmd", "dmdId"),
    ],
}


def load_all() -> dict[str, dict[str, list[dict]]]:
    """Read every JSON file under backend/mock-data/ into nested dicts.

    Returns
    -------
    dict
        Shape ``{database_name: {table_name: [row_dict, ...]}}``.
    """
    data: dict[str, dict[str, list[dict]]] = {}
    for db in DB_DIRS:
        db_path = ROOT / db
        if not db_path.is_dir():
            continue
        tables: dict[str, list[dict]] = {}
        for f in sorted(db_path.iterdir()):
            if f.suffix != ".json":
                continue
            with f.open(encoding="utf-8") as fh:
                tables[f.stem] = json.load(fh)
        data[db] = tables
    return data


def _find_fk_errors(data: dict[str, dict[str, list[dict]]]) -> list[str]:
    """Return FK-violation messages (empty list == OK)."""
    errors: list[str] = []

    for db, tables in data.items():
        patient_rows = tables.get("patient", [])
        patient_ids = {r["patientId"] for r in patient_rows}

        # 1) Every non-patient table row must reference an existing patientId,
        #    except sub-tables that reference their parent test row instead.
        sub_table_names = {st for st, _, _, _ in SUB_TABLE_FKS.get(db, [])}
        for table, rows in tables.items():
            if table == "patient" or table in sub_table_names:
                continue
            for i, row in enumerate(rows):
                pid_val = row.get("patientId")
                if pid_val is None:
                    errors.append(f"{db}/{table}.json row {i}: missing patientId")
                elif pid_val not in patient_ids:
                    errors.append(
                        f"{db}/{table}.json row {i}: patientId {pid_val} not in {db}/patient.json"
                    )

        # 2) Sub-tables must reference an existing parent row.
        for sub_table, parent_id_field, parent_table, parent_pk in SUB_TABLE_FKS.get(db, []):
            parent_ids = {r[parent_pk] for r in tables.get(parent_table, []) if parent_pk in r}
            for i, row in enumerate(tables.get(sub_table, [])):
                parent_val = row.get(parent_id_field)
                if parent_val is None:
                    errors.append(
                        f"{db}/{sub_table}.json row {i}: missing {parent_id_field}"
                    )
                elif parent_val not in parent_ids:
                    errors.append(
                        f"{db}/{sub_table}.json row {i}: {parent_id_field}={parent_val} "
                        f"not in {db}/{parent_table}.json"
                    )

    return errors


def validate(data: dict[str, dict[str, list[dict]]] | None = None) -> None:
    """Validate FK integrity across all mock databases.

    Parameters
    ----------
    data
        Pre-loaded dataset returned by :func:`load_all`. If ``None``, this
        function calls :func:`load_all` itself.

    Raises
    ------
    ValueError
        When any FK constraint fails. The message lists every offending
        ``database/table.json`` row and field.
    """
    if data is None:
        data = load_all()
    errors = _find_fk_errors(data)
    if errors:
        raise ValueError(
            "mock-data FK validation failed:\n  - " + "\n  - ".join(errors)
        )


def main() -> int:
    data = load_all()
    errors = _find_fk_errors(data)

    for db in DB_DIRS:
        tables = data.get(db, {})
        total = sum(len(rows) for rows in tables.values())
        print(f"{db}: {len(tables)} tables, {total} rows")
        for t in sorted(tables):
            print(f"  {t:<12} {len(tables[t])} rows")

    if errors:
        print("\nFK validation FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("\nFK validation OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
