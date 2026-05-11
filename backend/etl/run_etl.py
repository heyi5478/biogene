#!/usr/bin/env python3
"""ETL orchestrator — dispatch by source and run the right pipeline.

This is the single entry point operations runs. It is the only place
where source-specific knobs (MySQL/MSSQL credentials, blob output dir,
which transform step belongs to which source) live.

    python backend/etl/run_etl.py --source 2.0
    python backend/etl/run_etl.py --source 1.0-mdb --mdb-path /path/to/gene.mdb
    python backend/etl/run_etl.py --source 1.0-dbgen     # MVP-3 — see §9

For ``--source 2.0``:
    Iterates the three (mysql_db, target_schema) pairs, expanding
    ``pgloader_2_0.load`` for each and running pgloader into a
    ``stg_<target>`` staging schema. After all three staging schemas
    are populated, runs ``transform_2_0.sql`` (generated from
    ``column_mapping_2_0.yaml`` by ``gen_transform_2_0.py``) which
    INSERTs into the canonical ``main``/``external``/``nbs`` tables
    with column renames and ``patient_id`` UUID synthesis, then drops
    the staging schemas (set ``KEEP_STAGING=1`` to keep them for
    debugging). Connection info comes from ``MYSQL_2_0_URL`` in the
    environment.

For ``--source 1.0-mdb``:
    Runs ``extract_mdb.sh`` → ``extract_blobs_mdb.py`` → ``transform.py``
    → ``load_pg.py`` in sequence (see §8).
"""

from __future__ import annotations

import argparse
import os
import shutil
import string
import subprocess
import sys
from pathlib import Path

ETL_DIR = Path(__file__).resolve().parent
TEMPLATE = ETL_DIR / "pgloader_2_0.load"
POST_SQL = ETL_DIR / "post_pgloader.sql"

# (mysql DB name, target canonical PG schema). MySQL DB names may contain
# a dot or non-ASCII characters so they are always backtick-quoted when
# spliced into the pgloader URL. Defaults match the `pythonProject` 2.0
# install; override via env vars on stage/prod if names differ.
#
# pgloader actually lands in `stg_<target>` (see `pgloader_2_0.load`);
# transform_2_0.sql then moves data into the canonical schema.
SOURCES_2_0: list[tuple[str, str]] = [
    (os.environ.get("MYSQL_2_0_DB_MAIN",     "2.0"),             "main"),
    (os.environ.get("MYSQL_2_0_DB_EXTERNAL", "Out_hospital"),    "external"),
    (os.environ.get("MYSQL_2_0_DB_NBS",      "new_born_screen"), "nbs"),
]

TRANSFORM_SQL = ETL_DIR / "transform_2_0.sql"


def _need(*tools: str) -> None:
    missing = [t for t in tools if shutil.which(t) is None]
    if missing:
        sys.exit(f"required tool(s) not on PATH: {missing}")


def _expand_template(source_schema: str, target_schema: str) -> Path:
    """Render pgloader_2_0.load with placeholders substituted, return temp path.

    Uses ``string.Template`` so unknown ``$VARS`` raise rather than silently
    produce malformed pgloader DSL.
    """
    mysql_url = os.environ.get("MYSQL_2_0_URL")
    pg_url = os.environ.get("PG_URL_SYNC", "postgresql://gimc:gimc@localhost/gimc")
    if not mysql_url:
        sys.exit(
            "MYSQL_2_0_URL not set; expected mysql://user:pw@host:3306/?<flags> "
            "(database supplied per source — pgloader picks DB from the URL)"
        )

    # pgloader expects the database name in the URL path; the source schema
    # changes per call so we splice it in.
    if "?" in mysql_url:
        base, _, _flags = mysql_url.partition("?")
    else:
        base = mysql_url
    # Trim trailing slash and append `/<db>`.
    base = base.rstrip("/")
    full_mysql = f"{base}/`{source_schema}`"

    t = string.Template(TEMPLATE.read_text())
    out = t.substitute(
        MYSQL_URL=full_mysql,
        PG_URL=pg_url,
        SOURCE_SCHEMA=source_schema,
        TARGET_SCHEMA=f"stg_{target_schema}",
    )
    tmp = ETL_DIR / f".pgloader_2_0_{target_schema}.expanded.load"
    tmp.write_text(out)
    return tmp


def run_2_0() -> int:
    """2.0 ETL: extract via pgloader into stg_* schemas, then transform.

    Sequence per source:
        1. pgloader: MySQL DB → stg_<target> (raw mirror, identifiers preserved)

    Then once, after all three staging schemas exist:
        2. psql -f transform_2_0.sql  — INSERT INTO <canonical> SELECT ...
                                        FROM stg_<canonical> with renames
                                        and uuid_generate_v5 patient_id.
        3. DROP SCHEMA stg_main, stg_external, stg_nbs CASCADE
           (skipped if KEEP_STAGING=1 — useful for debugging).
    """
    _need("pgloader", "psql")
    pg_url = os.environ.get("PG_URL_SYNC", "postgresql://gimc:gimc@localhost/gimc")
    keep_staging = os.environ.get("KEEP_STAGING") == "1"

    # 1. pgloader each MySQL DB into its staging schema.
    for source_schema, target_schema in SOURCES_2_0:
        print(f"\n=== {source_schema!r} → stg_{target_schema} ===")
        load_file = _expand_template(source_schema, target_schema)
        print(f"  pgloader: {load_file.name}")
        rc = subprocess.call(["pgloader", str(load_file)])
        if rc != 0:
            return rc

    # 2. transform staging → canonical (single transaction).
    if not TRANSFORM_SQL.exists():
        sys.exit(
            f"missing {TRANSFORM_SQL.name}; run `python backend/etl/gen_transform_2_0.py` first"
        )
    print(f"\n=== transform: {TRANSFORM_SQL.name} ===")
    rc = subprocess.call(["psql", pg_url, "-f", str(TRANSFORM_SQL)])
    if rc != 0:
        return rc

    # 3. drop staging unless asked to keep.
    if keep_staging:
        print("\nKEEP_STAGING=1 → leaving stg_main / stg_external / stg_nbs in place.")
    else:
        print("\n=== cleanup: DROP SCHEMA stg_* CASCADE ===")
        drop_sql = "DROP SCHEMA IF EXISTS stg_main CASCADE; " \
                   "DROP SCHEMA IF EXISTS stg_external CASCADE; " \
                   "DROP SCHEMA IF EXISTS stg_nbs CASCADE;"
        rc = subprocess.call(["psql", pg_url, "-c", drop_sql])
        if rc != 0:
            return rc

    print("\n2.0 ETL complete. Recommend: python backend/etl/verify.py --skip 6")
    return 0


def run_1_0_mdb(mdb_path: Path) -> int:
    """1.0 Access database ETL — see §8.

    Pipeline: extract_mdb.sh → extract_blobs_mdb.py → transform.py → load_pg.py.
    """
    _need("mdb-tables", "mdb-export", "psql")
    if not mdb_path.exists():
        sys.exit(f"mdb file not found: {mdb_path}")

    out_dir = ETL_DIR / "out" / "1.0-mdb"
    out_dir.mkdir(parents=True, exist_ok=True)

    extract = ETL_DIR / "extract_mdb.sh"
    blobs = ETL_DIR / "extract_blobs_mdb.py"
    transform = ETL_DIR / "transform.py"
    load = ETL_DIR / "load_pg.py"

    steps = [
        ["bash", str(extract), str(mdb_path), str(out_dir)],
        [sys.executable, str(blobs), str(mdb_path), str(out_dir)],
        [sys.executable, str(transform), str(out_dir)],
        [sys.executable, str(load), str(out_dir)],
    ]
    for cmd in steps:
        print(">>", " ".join(cmd))
        rc = subprocess.call(cmd)
        if rc != 0:
            return rc

    print("\n1.0-mdb ETL complete. Recommend: python backend/etl/verify.py --skip 6")
    return 0


def run_1_0_dbgen() -> int:
    sys.exit("DBGEN ETL is MVP-3; see §9 plan in tasks.md before running.")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--source", required=True,
        choices=["2.0", "1.0-mdb", "1.0-dbgen"],
    )
    p.add_argument("--mdb-path", type=Path, help="path to gene.mdb (for --source 1.0-mdb)")
    args = p.parse_args()

    if args.source == "2.0":
        return run_2_0()
    if args.source == "1.0-mdb":
        if args.mdb_path is None:
            sys.exit("--mdb-path is required for --source 1.0-mdb")
        return run_1_0_mdb(args.mdb_path)
    if args.source == "1.0-dbgen":
        return run_1_0_dbgen()
    return 1


if __name__ == "__main__":
    sys.exit(main())
