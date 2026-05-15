## Why

The 2.0 MySQL → 3.0 PostgreSQL stage migration is currently blocked at
the transform step. `backend/etl/column_mapping_2_0.yaml` was authored
assuming the three source MySQL databases (`2.0`, `Out_hospital`,
`new_born_screen`) share one column-naming convention, but they don't:

- `2.0` uses `<table>-<field>` prefixed columns
  (`AA-Result`, `Enzyme-檢體類別`, `MS/MS-Result`, …).
- `Out_hospital` drops most of those prefixes (`Result`, `檢體類別`)
  — but on its `ms/ms` table it *adds* an `AA-` prefix to amino-acid
  columns that `2.0/ms/ms` leaves bare.
- `new_born_screen` uses upper-case amino acid abbreviations
  (`ALA`, `ARG`, …) and single-digit acylcarnitine labels
  (`C2`/`C3`/`C5`, not the `C02`/`C03`/`C05` zero-padded form used by
  the other two), and `門診個案` uses `母姓名` not `OPD_母姓名`.

`transform_2_0.sql` (generated from the YAML) therefore errors with
`column "X" does not exist` the moment it touches any non-overlapping
column in `stg_external` / `stg_nbs`. ~2.26 M rows of 2.0 staging data
on `biogene-3-tst` are deduped and waiting; only the YAML / transform
needs to be correct. Column lists used here were extracted from
`information_schema.columns` against the actual loaded staging tables
on stage and cross-checked with `backend/etl/LOAD_2_0_PROD.md
§What's broken`.

## What Changes

- Update `schemas.external.sample_tables` for `aa`, `enzyme`, `lsd`,
  `ms/ms` so each `columns:` SQL expression references the actual
  `Out_hospital` source column name (drop `AA-`/`Enzyme-`/`MS/MS-`
  prefixes from text + amino-acid fields; rename `ABG/GAA` →
  `ABG_GAA`; for `ms/ms` *add* `AA-` prefix to bare amino-acid names).
- Update `schemas.nbs.patient_sources[門診個案]` so `name` references
  `母姓名` instead of `OPD_母姓名`.
- Update `schemas.nbs.sample_tables[ms]` to use upper-case amino acid
  abbreviations (`ALA`, `ARG`, …), `LEU` in place of `Leu/Ile` (no
  `ILE` column exists in this source), and `C2`/`C3`/`C5` in place of
  `C02`/`C03`/`C05`.
- Update `schemas.main.sample_tables[outbank]` to reference
  `Outbank_Sample_name` instead of `Outbank_Sampleno` (the real source
  column name; `Outbank_Sampleno` only exists on stage today via a
  `GENERATED ALWAYS AS` workaround column that won't survive a fresh
  extract).
- Regenerate `backend/etl/transform_2_0.sql` via
  `python3 backend/etl/gen_transform_2_0.py`.

Tables whose source MySQL tables don't exist (e.g.
`external.{opd, gag, outbank}`) keep their YAML entries unchanged —
the generator's `to_regclass()` guard emits `RAISE NOTICE 'missing
source %, skipping'` at transform time, which is the existing
pattern for tables that vary across deployments.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `legacy-data-etl`: adds a requirement that the 2.0 → 3.0 column
  mapping handle per-source-schema column-naming variation, since
  the three source MySQL DBs do not share one convention. The
  existing requirement about `2.0` MySQL ETL is silent on this and
  the bug catalogued in `LOAD_2_0_PROD.md §What's broken` traces
  directly to the missing contract.

## Impact

- **Files**: `backend/etl/column_mapping_2_0.yaml` (hand edit) and
  `backend/etl/transform_2_0.sql` (regenerated; do not hand-edit).
- **Not affected**: `backend/etl/gen_transform_2_0.py` (generator
  unchanged), canonical PG schema in `main.*` / `external.*` /
  `nbs.*` (target column names unchanged), all backend services and
  ORM models, frontend, alembic migrations.
- **Stage unblocked**: after merge, `backend/etl/LOAD_2_0_PROD.md
  §Resume` can run steps 1–7 end-to-end against
  `user@10.19.209.19`.
- **Risk**: stage `transform_2_0_wrapped.sh` runs in a single
  transaction; any remaining mismatch produces a clean rollback —
  the 5 MB pre-attempt PG backup at
  `~/db-backups/gimc-pre-2.0-20260514-0826.sql.gz` is the explicit
  rollback path documented in `LOAD_2_0_PROD.md §Rollback`.
- **Out of scope (deferred to follow-ups)**: adding migrations for
  `external.{aadc, ald, mma, mps2}` and
  `nbs.{aadc, ald, lsd, mma, mps2, tgal, tsh}` — staging data exists
  but canonical target tables don't (would need an alembic schema
  migration first); sentinel-chartno filtering (`NA`/`Nil`/`MR Plan`);
  varchar-overflow handling currently papered over by
  `transform_2_0_wrapped.sh`.
