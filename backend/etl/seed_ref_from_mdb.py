#!/usr/bin/env python3
"""One-shot seed for the ``ref`` schema lookup tables from gene.mdb.

Pulls the five legacy reference tables (``AAM``, ``MSM``, ``DNAITEM``,
``ENZYMEITEM``, ``COMMAND``) and inserts them into the matching
``ref.*`` tables. Idempotent via UNIQUE constraint on ``code``:
``INSERT … ON CONFLICT (code) DO UPDATE``.

This is separate from ``run_etl.py --source 1.0-mdb`` because:

- It's only run once across the project lifetime (or whenever the legacy
  catalogues are revised).
- Loading these tables doesn't depend on patient data being present, so
  it can be done before or after the main ETL — orchestrating it
  separately keeps run_etl.py simpler.

Usage:
    python backend/etl/seed_ref_from_mdb.py /path/to/gene.mdb

The mapping table below is the source-of-truth for which legacy column
becomes which ``ref`` column. Update if the actual ``gene.mdb`` deviates.
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import subprocess
import sys
from pathlib import Path

import psycopg
from psycopg import sql

# (legacy_table_in_mdb, target_ref_table, code_col_in_legacy, label_col_in_legacy, desc_col)
REF_MAPPING: list[tuple[str, str, str, str, str | None]] = [
    ("AAM",        "aa_method_ref",   "methodno",  "methodname",  None),
    ("MSM",        "msms_method_ref", "methodno",  "methodname",  None),
    ("ENZYMEITEM", "enzyme_item_ref", "itemno",    "itemname",    "remark"),
    ("DNAITEM",    "dna_item_ref",    "itemno",    "itemname",    "remark"),
    ("COMMAND",    "command_phrase",  "phraseno",  "phrasetext",  None),
]


def _sync_url() -> str:
    url = os.environ.get(
        "DATABASE_URL", "postgresql+asyncpg://gimc:gimc@localhost:5432/gimc"
    )
    return url.replace("+asyncpg", "+psycopg").replace("+psycopg", "")


def _read_mdb_table(mdb: Path, table: str) -> list[dict[str, str]]:
    """Use mdb-export to dump one table as CSV in-memory."""
    res = subprocess.run(
        ["mdb-export", "-D", "%Y-%m-%d %H:%M:%S", str(mdb), table],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )
    return list(csv.DictReader(io.StringIO(res.stdout)))


def _upsert(conn: psycopg.Connection, target_table: str, rows: list[dict]) -> int:
    if not rows:
        return 0
    stmt = sql.SQL(
        "INSERT INTO ref.{} (code, label, description, v2_source_schema) "
        "VALUES (%(code)s, %(label)s, %(description)s, '1.0-mdb') "
        "ON CONFLICT (code) DO UPDATE SET "
        "    label = EXCLUDED.label, "
        "    description = COALESCE(EXCLUDED.description, ref.{}.description)"
    ).format(sql.Identifier(target_table), sql.Identifier(target_table))
    with conn.cursor() as cur:
        cur.executemany(stmt, rows)
    return len(rows)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mdb", type=Path, help="path to gene.mdb")
    args = p.parse_args()

    if not args.mdb.exists():
        sys.exit(f"mdb not found: {args.mdb}")

    with psycopg.connect(_sync_url()) as conn:
        for legacy_t, target_t, code_c, label_c, desc_c in REF_MAPPING:
            try:
                src = _read_mdb_table(args.mdb, legacy_t)
            except subprocess.CalledProcessError as e:
                print(
                    f"  WARN  {legacy_t}: mdb-export failed "
                    f"({e.stderr or 'no stderr'}); skipping",
                    file=sys.stderr,
                )
                continue
            normalised = [
                {
                    "code": r.get(code_c, "").strip(),
                    "label": (r.get(label_c) or "").strip(),
                    "description": (r.get(desc_c) or "").strip() if desc_c else None,
                }
                for r in src if r.get(code_c)
            ]
            n = _upsert(conn, target_t, normalised)
            print(f"  ref.{target_t:18}  {n:4} rows  ← {legacy_t}")
        conn.commit()

    print("\nseed_ref_from_mdb.py done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
