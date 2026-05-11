# `backend/etl/` — one-shot legacy data ETL

Pipelines that ingest the 1.0 (Access `gene.mdb` + SQL Server `DBGEN`) and 2.0
(MySQL three-database) systems into the 3.0 PostgreSQL `gimc` database. ETL is
**one-shot** — once production cuts over to `GIMC_DATA_BACKEND=postgres`, 1.0 /
2.0 are set read-only and these scripts are retired.

See `openspec/specs/legacy-data-etl/spec.md` for the contract this directory
must satisfy.

## System dependencies

ETL host needs (in addition to the Python deps in `backend/shared/pyproject.toml`):

```bash
sudo apt update
sudo apt install -y \
    postgresql-client-16 \   # psql + pg_dump
    pgloader \               # 2.0 MySQL → PG, optional MSSQL → PG
    mdbtools                 # 1.0 gene.mdb (Access) extract: mdb-tables / mdb-export
```

Optional, only for the DBGEN (MSSQL) source:

```bash
sudo apt install -y unixodbc unixodbc-dev tdsodbc
pip install -e 'backend/shared[etl-mssql]'   # pulls in pyodbc
```

## Source-system assumptions

| Source | Tech | Reach | Notes |
|---|---|---|---|
| 2.0 `2.0`             | MySQL on legacy host | network | utf8mb4; → `main` schema |
| 2.0 `2.0外院資料庫`     | MySQL on legacy host | network | utf8mb4; → `external` schema |
| 2.0 `new_born_screening` | MySQL on legacy host | network | utf8mb4; NBS sub-tables `cah_tgal`, `dmd_tsh`; → `nbs` schema |
| 1.0 `gene.mdb`         | Access `.mdb` file | local file; copy to `backend/etl/sources/1.0-mdb/gene.mdb` | English legacy column names; BLOB columns in MSDATA/GCDATA/MPSUDATA/ENZYME |
| 1.0 `DBGEN`            | SQL Server on ta-server | network (see §9 plan) | MVP-3 — content & reachability TBD |

## BLOB convention

Large binary columns (`MSDATA.DATA`, `GCDATA.pic`, `MPSUDATA.pic`, `ENZYME.pic`)
are written to the filesystem under `$GIMC_BLOB_ROOT` (default `/srv/gimc/blobs`):

```
/srv/gimc/blobs/
  msms/<sampleno>.bin     # MSDATA.DATA — raw spectrum
  gcms/<sampleno>.jpg     # GCDATA.pic
  mpsu/<sampleno>.jpg     # MPSUDATA.pic
  enzyme/<sampleno>.jpg   # ENZYME.pic
```

The DB stores only the relative path in the corresponding `raw_data_path`
column. Rerunning the extract overwrites the same path (idempotent).

## Tables NOT migrated

By design the following are excluded from the cutover:

- `users`, `operator`, `doctor` — 3.0 has its own auth.
- `CELLDATA` — staging-only on the 1.0 side.
- `opd_tmp`, `disease_count` — derived; recomputed on demand in 3.0.
- MOH report forms (`G0001`, `G0016`, `G0017`) — stay in 1.0; not in scope.

## Operations playbook

### Pre-flight (every source)

1. Apply pending migrations: `make alembic-up` from `backend/`.
2. Confirm zero drift: `make alembic-check` should print
   `No new upgrade operations detected.`
3. Set the connection env vars in your shell:
   - `DATABASE_URL=postgresql+asyncpg://gimc:gimc@localhost:5432/gimc`
   - For 2.0 ETL: `MYSQL_2_0_URL=mysql://user:pw@host:3306` (no DB name —
     `run_etl.py` appends each `2.0` / `2.0外院資料庫` /
     `new_born_screening` per call).
4. Make sure no service is reading the DB while the ETL runs. The 2.0
   pgloader rule includes `include drop` and will recreate tables.

### Source: 2.0 (MySQL)

```bash
python backend/etl/run_etl.py --source 2.0
```

What happens (extract → transform → load → cleanup):

1. **Extract (pgloader, ×3).** `pgloader_2_0.load` is expanded by
   `run_etl.py` per source MySQL DB and pgloads each into a temporary
   *staging* PG schema (`stg_main` / `stg_external` / `stg_nbs`).
   pgloader keeps original identifiers intact — Chinese table names,
   dash-suffixed columns, slashes, the lot — so the transform step has
   something obvious to map from.

2. **Transform (psql + transform_2_0.sql).** Once all three staging
   schemas exist, `transform_2_0.sql` (generated from
   `column_mapping_2_0.yaml` by `gen_transform_2_0.py`) runs in a
   single transaction. It:
   - `TRUNCATE … CASCADE`s the canonical `main` / `external` / `nbs`
     tables created by the alembic baseline.
   - For each `patient` source (`基本資料`, `opd`, `nbs`, `系統外自費`,
     `門診個案`), `INSERT … ON CONFLICT (patient_id) DO UPDATE` with
     `COALESCE()` so the first source wins on collisions and subsequent
     sources only fill NULL fields. `patient_id` is
     `uuid_generate_v5(uuid_ns_oid(), '<schema>:' || <chartno>)`.
   - For each sample table, `INSERT … SELECT` from the staging table,
     joining back to `patient` either by recomputing the same UUID
     (main / external) or by `patient.nbs_id = src.Sample_name` (nbs),
     filling `ntubiogene_sampleno` and `v2_source_schema` for audit.
   - Every `INSERT` is guarded by `to_regclass(...) IS NULL THEN
     RAISE NOTICE` so a missing source table is logged but doesn't
     abort the run — important when a tenant never used (say)
     `Out_hospital`.

3. **Cleanup.** `DROP SCHEMA stg_* CASCADE`. Set `KEEP_STAGING=1` in
   the environment to keep the staging schemas around for post-mortem.

The mapping is data, not code. To adjust the 2.0 → 3.0 column wiring,
edit `column_mapping_2_0.yaml`, re-run `python backend/etl/gen_transform_2_0.py`,
and commit both files together. The schema is documented inline in the
YAML header.

`post_pgloader.sql` is **not** part of the 2.0 path anymore — it's a
no-op left in the tree for the 1.0 paths to opt into. The 2.0 transform
SQL handles `patient_id` casting, `ntubiogene_sampleno` synthesis, and
trigger setup implicitly (triggers come from the alembic baseline, since
we INSERT into existing canonical tables).

### Source: 1.0 (gene.mdb / Access)

```bash
python backend/etl/run_etl.py --source 1.0-mdb --mdb-path /path/to/gene.mdb
```

Pipeline:
- `extract_mdb.sh` → CSVs under `backend/etl/out/1.0-mdb/`.
- `extract_blobs_mdb.py` → BLOBs to `$GIMC_BLOB_ROOT/{msms,gcms,mpsu,enzyme}/`
  + `blob_paths.json` index.
- `transform.py` → English column names → 3.0 schema, deterministic UUID
  per chartno (merges `ptinfo` and the Chinese-named `patient` table),
  joins blob paths into the relevant sample rows.
- `load_pg.py` → `INSERT ... ON CONFLICT (patient_id) DO UPDATE` for
  patient (preserves 2.0 values, fills nulls from 1.0); `COPY FROM
  STDIN` for sample tables.

The reference catalogues (`AAM` / `MSM` / `DNAITEM` / `ENZYMEITEM` /
`COMMAND`) load via a separate one-shot:

```bash
python backend/etl/seed_ref_from_mdb.py /path/to/gene.mdb
```

### Source: 1.0 (DBGEN / SQL Server) — MVP-3

Deferred until the team confirms which DBGEN tables hold data not
covered by 2.0 or `gene.mdb`. See `extract_dbgen.py` (TBD).

## Verification

After every source run:

```bash
make verify-pg                     # all 7 checks; needs services running
python backend/etl/verify.py --skip 6   # CI / no services
```

The seven checks are documented inline in `verify.py`:

1. row-count parity vs `expected_counts.py`
2. FK integrity (sample → patient, sub → parent)
3. anchor chartno → UUID round-trip
4. `dbsLysoGb3 > 5` mock-parity regression (JSON ↔ PG)
5. links symmetry / `ix_link_b` reverse query
6. gateway `/patients/{uuid}` PatientBundle shape
7. perf baseline `SELECT … FROM main.aa WHERE leu > 200` < 200 ms

## Rerun semantics (idempotency)

The pipeline is designed to be safe to rerun:

- 2.0 pgloader uses `include drop` — every run rebuilds the target
  schema from scratch. Safe iff no other process holds rows you care about.
- 1.0 patient upsert preserves existing non-null values, so re-importing
  the same `gene.mdb` converges to the same row set. The `chartno`-based
  UUID guarantees no duplicate patient rows even across multiple ETL
  passes (1.0 + 2.0 collapse onto the same `patient_id`).
- 1.0 sample tables are DELETE-then-COPY per run (the IDENTITY `id`
  prevents otherwise-clean idempotency).
- BLOB writes are content-addressed by `sampleno` and overwrite in place.

## Refreshing `expected_counts.py`

When the source data legitimately changes, regenerate the baseline:

```bash
psql "$DATABASE_URL" -c "
SELECT n.nspname AS db, c.relname AS tbl, c.reltuples::bigint
FROM pg_class c JOIN pg_namespace n ON c.relnamespace = n.oid
WHERE n.nspname IN ('main','external','nbs') AND c.relkind = 'r'
ORDER BY 1, 2;
"
```

Hand-edit `backend/etl/expected_counts.py` so the dict keys match the
mock-data dir naming (`db_main`, `db_external`, `db_nbs`).

## Troubleshooting

- **pgloader: `cannot find type for table ...`** — almost always a
  CAST rule mismatch. Check the source column type with `mysql -e
  "DESCRIBE <db>.<tbl>"`; add a more specific CAST in `pgloader_2_0.load`.
- **`ALTER COLUMN patient_id TYPE UUID` fails on stray non-UUID values**
  — find them via `SELECT patient_id FROM <schema>.patient WHERE
  patient_id !~ '^[0-9a-f-]{36}$' LIMIT 10`. Fix at source then rerun
  pgloader.
- **`mdb-export` returns garbled non-ASCII** — install mdbtools >= 0.7
  (apt has 0.5 on Ubuntu 22.04 main; the pgdg-style PPA carries newer).
  Or convert the .mdb on a Windows host first.
- **`verify.py #6` fails with connection refused** — start the four
  services first (`bash backend/scripts/dev.sh`); CI should use
  `--skip 6`.
