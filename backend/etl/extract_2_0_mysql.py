#!/usr/bin/env python3
"""Extract 2.0 MySQL data into PG staging schemas.

Replacement for the pgloader-based extract step in `pgloader_2_0.load`.
pgloader 3.6.x's bundled QMYND driver doesn't speak MySQL 8.x's handshake
protocol; PyMySQL does. This script mirrors what pgloader was supposed to do:

    `2.0`             → schema `stg_main`
    `out_hospital`    → schema `stg_external`
    `new_born_screen` → schema `stg_nbs`

Identifiers (table names, column names, including Chinese / spaces / `/`)
are preserved verbatim so the existing `transform_2_0.sql` keeps working
unchanged.

Usage:
    MYSQL_PASSWORD='...' python3 backend/etl/extract_2_0_mysql.py

Env vars (defaults match the stage temp-container setup):
    MYSQL_HOST      127.0.0.1
    MYSQL_PORT      3307
    MYSQL_USER      migration_user
    MYSQL_PASSWORD  (no default — required)
    PG_DSN          postgresql://gimc:gimc@127.0.0.1:5432/gimc

Next step after this finishes:
    psql "$PG_DSN" -f backend/etl/transform_2_0.sql
"""
from __future__ import annotations

import datetime as _dt
import os
import sys
import time

import pymysql
import pymysql.cursors
from pymysql.constants import FIELD_TYPE
from pymysql.converters import conversions, convert_date, convert_datetime
import psycopg


SOURCES: list[tuple[str, str]] = [
    ("2.0",             "stg_main"),
    ("out_hospital",    "stg_external"),
    ("new_born_screen", "stg_nbs"),
]


# --------------------------------------------------------------------------- #
# PyMySQL converters that survive MySQL's `0000-00-00` sentinel values.
# Default converters raise ValueError on year=0; we want None so psycopg can
# COPY them in as NULL.
# --------------------------------------------------------------------------- #

def _is_zero_date(s) -> bool:
    if isinstance(s, str):
        return s.startswith("0000")
    if isinstance(s, (bytes, bytearray)):
        return s.startswith(b"0000")
    return False


def _safe_date(s):
    # PyMySQL's convert_date silently returns the original string on parse
    # failure (rather than raising). Many MySQL exports contain partially-
    # invalid sentinels like `1900-01-00` (valid year, day=0). Verify the
    # result is actually a date object; otherwise treat as NULL.
    if s is None or _is_zero_date(s):
        return None
    try:
        result = convert_date(s)
    except (ValueError, TypeError):
        return None
    return result if isinstance(result, _dt.date) else None


def _safe_datetime(s):
    # Same isinstance guard as _safe_date — convert_datetime delegates to
    # convert_date which can return the original string.
    if s is None or _is_zero_date(s):
        return None
    try:
        result = convert_datetime(s)
    except (ValueError, TypeError, OverflowError):
        return None
    return result if isinstance(result, (_dt.date, _dt.datetime)) else None


_CONV = conversions.copy()
_CONV[FIELD_TYPE.DATE] = _safe_date
_CONV[FIELD_TYPE.NEWDATE] = _safe_date
_CONV[FIELD_TYPE.DATETIME] = _safe_datetime
_CONV[FIELD_TYPE.TIMESTAMP] = _safe_datetime


# --------------------------------------------------------------------------- #
# MySQL → PG type mapping. Mirrors `pgloader_2_0.load` CAST rules.
# --------------------------------------------------------------------------- #

def mysql_to_pg_type(data_type: str, column_type: str, char_max_len: int | None) -> str:
    dt = (data_type or "").lower()
    ct = (column_type or "").lower()

    if dt == "tinyint":
        return "boolean" if "(1)" in ct else "smallint"
    if dt in ("smallint", "mediumint", "int", "integer"):
        return "integer"
    if dt == "bigint":
        return "bigint"
    if dt in ("decimal", "numeric", "float", "double"):
        return "numeric"
    if dt == "date":
        return "date"
    if dt in ("datetime", "timestamp"):
        return "timestamptz"
    if dt == "time":
        return "time"
    if dt == "year":
        return "integer"
    if dt in ("char", "varchar"):
        if char_max_len and char_max_len <= 65535:
            return f"varchar({char_max_len})"
        return "text"
    if dt in ("text", "mediumtext", "longtext", "tinytext"):
        return "text"
    if dt in ("blob", "mediumblob", "longblob", "tinyblob", "binary", "varbinary"):
        return "bytea"
    if dt in ("enum", "set"):
        return "text"
    if dt == "json":
        return "jsonb"
    if dt == "bit":
        return "bit varying"
    return "text"


# --------------------------------------------------------------------------- #
# Identifier quoting
# --------------------------------------------------------------------------- #

def qpg(ident: str) -> str:
    return '"' + ident.replace('"', '""') + '"'


def qmy(ident: str) -> str:
    return "`" + ident.replace("`", "``") + "`"


# --------------------------------------------------------------------------- #
# Connection helpers
# --------------------------------------------------------------------------- #

def connect_mysql(db: str, streaming: bool = False) -> pymysql.connections.Connection:
    # `streaming=True` → server-side cursor (SSCursor): rows arrive one at a
    # time so we can pump straight into psycopg COPY without buffering the
    # whole table in Python. Required for wide tables in `2.0` (e.g.
    # `dna bank` has 100+ columns × 38k rows — a fetchall() blew swap on
    # stage and hung the host).
    cursorclass = pymysql.cursors.SSCursor if streaming else pymysql.cursors.Cursor
    return pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYSQL_PORT", "3307")),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=db,
        charset="utf8mb4",
        # SET sql_mode='' disables STRICT_TRANS_TABLES so MySQL returns
        # `0000-00-00` rather than raising; our converters above turn
        # those into None.
        init_command="SET SESSION sql_mode = ''",
        conv=_CONV,
        cursorclass=cursorclass,
    )


# --------------------------------------------------------------------------- #
# Per-DB extraction
# --------------------------------------------------------------------------- #

def extract_db(pg, mysql_db: str, stg_schema: str) -> dict[str, int]:
    print(f"\n=== {mysql_db!r} → {stg_schema} ===", flush=True)
    counts: dict[str, int] = {}

    # Metadata connection: default Cursor (buffered), small queries only.
    meta = connect_mysql(mysql_db, streaming=False)
    try:
        with meta.cursor() as mc:
            mc.execute(
                """
                SELECT TABLE_NAME
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
                """,
                (mysql_db,),
            )
            tables = [r[0] for r in mc.fetchall()]
            print(f"  {len(tables)} table(s) in source", flush=True)

            with pg.cursor() as pgc:
                pgc.execute(f"DROP SCHEMA IF EXISTS {qpg(stg_schema)} CASCADE")
                pgc.execute(f"CREATE SCHEMA {qpg(stg_schema)}")

            for tbl in tables:
                mc.execute(
                    """
                    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, COLUMN_TYPE
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                    """,
                    (mysql_db, tbl),
                )
                cols = list(mc.fetchall())
                if not cols:
                    print(f"  {tbl:30s}  (no columns? skipped)", flush=True)
                    continue

                col_defs = ", ".join(
                    f"{qpg(c[0])} {mysql_to_pg_type(c[1], c[3], c[2])}"
                    for c in cols
                )
                with pg.cursor() as pgc:
                    pgc.execute(
                        f"CREATE TABLE {qpg(stg_schema)}.{qpg(tbl)} ({col_defs})"
                    )

                # Stream rows from a fresh streaming connection to avoid
                # holding the whole table in memory.
                t0 = time.time()
                cols_list = ", ".join(qpg(c[0]) for c in cols)
                sql = (
                    f"COPY {qpg(stg_schema)}.{qpg(tbl)} ({cols_list}) "
                    f"FROM STDIN"
                )
                n = 0
                data = connect_mysql(mysql_db, streaming=True)
                try:
                    with data.cursor() as dc:
                        dc.execute(f"SELECT * FROM {qmy(mysql_db)}.{qmy(tbl)}")
                        with pg.cursor() as pgc:
                            with pgc.copy(sql) as cp:
                                for row in dc:
                                    cp.write_row(row)
                                    n += 1
                                    if n % 10000 == 0:
                                        print(f"  {tbl:30s}  ... {n:>10d} rows", flush=True)
                finally:
                    data.close()

                elapsed = time.time() - t0
                counts[tbl] = n
                print(f"  {tbl:30s}  {n:>10d} rows  ({elapsed:5.1f}s)", flush=True)
    finally:
        meta.close()

    return counts


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> int:
    if "MYSQL_PASSWORD" not in os.environ:
        sys.exit("MYSQL_PASSWORD env var required")
    if "MYSQL_USER" not in os.environ:
        os.environ["MYSQL_USER"] = "migration_user"

    only = os.environ.get("ONLY_DB")  # optional smoke test: ONLY_DB=out_hospital
    sources = [s for s in SOURCES if not only or s[0] == only]

    pg_dsn = os.environ.get(
        "PG_DSN", "postgresql://gimc:gimc@127.0.0.1:5432/gimc"
    )
    pg = psycopg.connect(pg_dsn, autocommit=True)

    overall: dict[str, dict[str, int]] = {}
    failed: list[tuple[str, str]] = []
    try:
        for mysql_db, stg_schema in sources:
            try:
                overall[mysql_db] = extract_db(pg, mysql_db, stg_schema)
            except Exception as e:
                print(f"\n!! {mysql_db!r} failed: {e}")
                failed.append((mysql_db, str(e)))
    finally:
        pg.close()

    print("\n=== summary ===")
    grand = 0
    grand_tbls = 0
    for db, counts in overall.items():
        sub = sum(counts.values())
        grand += sub
        grand_tbls += len(counts)
        print(f"  {db:20s}  {len(counts):3d} tables  {sub:>12,d} rows")
    print(f"  {'TOTAL':20s}  {grand_tbls:3d} tables  {grand:>12,d} rows")

    if failed:
        print("\nFAILED databases:")
        for db, err in failed:
            print(f"  {db}: {err}")
        return 1

    print("\nNext: psql -h 127.0.0.1 -U gimc -d gimc -f backend/etl/transform_2_0.sql")
    return 0


if __name__ == "__main__":
    sys.exit(main())
