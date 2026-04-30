#!/usr/bin/env python3
"""1.0-mdb load — push transformed CSVs into PostgreSQL.

Two write strategies depending on the table:

- ``patient`` — ``INSERT … ON CONFLICT (patient_id) DO UPDATE SET col =
  COALESCE(target.col, EXCLUDED.col)``. Same UUID may already exist
  (seeded by §6 or written by 2.0 ETL), and the merge rule is "keep
  whichever non-null we already have, fill any null from the 1.0 row".
  This is what gives us the "ptinfo + 中文 patient + 2.0 patient all
  collapse onto one row" behaviour described in design D2.

- Sample tables — ``COPY FROM STDIN`` is dramatically faster and we know
  every row is fresh (sample identity is the IDENTITY ``id``, no merge
  semantics expected). We DELETE-and-COPY to be idempotent on rerun.

Connection: psycopg 3 against ``DATABASE_URL`` (sync URL after
stripping +asyncpg). Same env var as the rest of the backend.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

import psycopg
from psycopg import sql


def _sync_url() -> str:
    url = os.environ.get(
        "DATABASE_URL", "postgresql+asyncpg://gimc:gimc@localhost:5432/gimc"
    )
    return url.replace("+asyncpg", "+psycopg").replace("+psycopg", "")


# (csv_filename, schema, table, columns_in_csv_order, copy_columns_in_db_order)
SAMPLE_LOADS: list[tuple[str, str, str, list[str], list[str]]] = [
    (
        "main_msms.csv", "main", "msms",
        ["patientId", "sampleName", "specimenType", "result",
         "raw_data_path", "ntubiogene_sampleno", "v2_source_schema"],
        ["patient_id", "sample_name", "specimen_type", "result",
         "raw_data_path", "ntubiogene_sampleno", "v2_source_schema"],
    ),
    (
        "main_gcms.csv", "main", "gcms",
        ["patientId", "sampleName", "specimenType", "result",
         "rawDataPath", "collectDate", "notes",
         "ntubiogene_sampleno", "v2_source_schema"],
        ["patient_id", "sample_name", "specimen_type", "result",
         "raw_data_path", "collect_date", "notes",
         "ntubiogene_sampleno", "v2_source_schema"],
    ),
    (
        "main_gag.csv", "main", "gag",
        ["patientId", "sampleName", "specimenType", "technician", "result",
         "DMGGAG", "CREATININE",
         "od", "urineCreatinine", "mggag", "twos", "twosCre",
         "ntubiogene_sampleno", "v2_source_schema"],
        ["patient_id", "sample_name", "specimen_type", "technician", "result",
         "dmggag", "creatinine",
         "od", "urine_creatinine", "mggag", "twos", "twos_cre",
         "ntubiogene_sampleno", "v2_source_schema"],
    ),
]


def _upsert_patient(conn: psycopg.Connection, csv_path: Path) -> int:
    if not csv_path.exists():
        return 0

    with csv_path.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    if not rows:
        return 0

    # COALESCE merge: keep existing non-null, fill null from EXCLUDED.
    cols = [
        "patient_id", "source", "name", "birthday", "sex",
        "chartno", "external_chartno", "nbs_id", "category",
        "diagnosis", "diagnosis2", "diagnosis3", "referring_doctor",
    ]
    # JSON-side keys (camelCase) — map onto DB cols above.
    src_keys = [
        "patientId", "source", "name", "birthday", "sex",
        "chartno", "external_chartno", "nbs_id", "category",
        "diagnosis", "diagnosis2", "diagnosis3", "referring_doctor",
    ]

    placeholders = ", ".join(["%s"] * len(cols))
    set_clause = ", ".join(
        f"{c} = COALESCE(main.patient.{c}, EXCLUDED.{c})"
        for c in cols if c != "patient_id"
    )
    stmt = (
        f"INSERT INTO main.patient ({', '.join(cols)}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT (patient_id) DO UPDATE SET {set_clause}"
    )

    n = 0
    with conn.cursor() as cur:
        for row in rows:
            params = [row.get(k) or None for k in src_keys]
            cur.execute(stmt, params)
            n += 1
    return n


def _copy_sample(conn: psycopg.Connection, csv_path: Path,
                 schema: str, table: str,
                 csv_cols: list[str], db_cols: list[str]) -> int:
    """DELETE then COPY — caller assumes rerun semantics."""
    if not csv_path.exists():
        return 0
    with csv_path.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return 0

    with conn.cursor() as cur:
        cur.execute(sql.SQL("DELETE FROM {}.{}").format(
            sql.Identifier(schema), sql.Identifier(table)
        ))

    copy_sql = sql.SQL("COPY {}.{} ({}) FROM STDIN").format(
        sql.Identifier(schema),
        sql.Identifier(table),
        sql.SQL(", ").join(sql.Identifier(c) for c in db_cols),
    )
    with conn.cursor() as cur, cur.copy(copy_sql) as cp:
        for row in rows:
            cp.write_row([row.get(k) or None for k in csv_cols])
    return len(rows)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("out_dir", type=Path, help="directory containing transformed/")
    args = p.parse_args()

    transformed = args.out_dir / "transformed"
    if not transformed.is_dir():
        sys.exit(f"missing transformed/ — run transform.py first: {transformed}")

    with psycopg.connect(_sync_url()) as conn:
        n = _upsert_patient(conn, transformed / "main_patient.csv")
        print(f"main.patient    {n} rows upserted (COALESCE merge)")

        for csv_name, schema, table, csv_cols, db_cols in SAMPLE_LOADS:
            n = _copy_sample(conn, transformed / csv_name, schema, table, csv_cols, db_cols)
            print(f"{schema}.{table:11} {n} rows COPY")

        conn.commit()

    print("\nload_pg.py done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
