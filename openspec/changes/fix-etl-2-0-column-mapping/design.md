## Context

`backend/etl/column_mapping_2_0.yaml` is the single source of truth
for how the legacy 2.0 MySQL → 3.0 PostgreSQL ETL maps source
columns onto canonical target columns.
`backend/etl/gen_transform_2_0.py` reads it and emits
`backend/etl/transform_2_0.sql`, which is the SQL that runs against
staging schemas (`stg_main` / `stg_external` / `stg_nbs`) populated
by `backend/etl/extract_2_0_mysql.py` (Python + PyMySQL + psycopg —
the path that replaced pgloader after MySQL 8 handshake issues; see
`backend/etl/LOAD_2_0_PROD.md §Why pgloader is out`).

The current YAML's `external` section was authored as a copy of
`main` on the assumption that `Out_hospital` shares `2.0`'s
naming convention. Likewise the `nbs` section was authored against
an assumed shape of `new_born_screen`. Reality (queried from
`information_schema.columns` on stage's already-loaded staging
tables) disagrees in specific, mechanical ways. The full mismatch
catalogue is in `backend/etl/LOAD_2_0_PROD.md §What's broken`;
stage data (~2.26 M rows across 43 tables, already deduped) is
waiting on a corrected transform.

`backend/etl/transform_2_0_wrapped.sh` already wraps the transform
in widen-to-TEXT → run → narrow-back-with-`LEFT()` so varchar
overflows truncate rather than error. That workaround stays;
this change only needs to make every column reference inside
the YAML point at a column that actually exists.

## Goals / Non-Goals

**Goals:**
- Every `columns:` expression in `column_mapping_2_0.yaml`
  references a column that exists in its corresponding stage
  staging table (`stg_main.<t>`, `stg_external.<t>`,
  `stg_nbs.<t>`), confirmed against `information_schema.columns`.
- `backend/etl/transform_2_0.sql` is regenerated from the
  updated YAML and committed alongside it (the YAML's docstring
  asserts this is the workflow).
- After merge, `backend/etl/LOAD_2_0_PROD.md §Resume` steps 1–7
  run end-to-end against `biogene-3-tst` without producing
  `column "X" does not exist`.

**Non-Goals:**
- Adding new source tables to the migration. Several staging
  tables exist with no canonical target
  (`external.{aadc, ald, mma, mps2}` — canonical `external`
  schema has none of these;
  `nbs.{aadc, ald, lsd, mma, mps2, tgal, tsh}` — `tgal`/`tsh` are
  merged into `cah_tgal`/`dmd_tsh`, populated by the 1.0-mdb path;
  others have no canonical target at all). Adding them would
  require an alembic schema migration first.
- Restructuring the YAML or generator to support per-source-schema
  column-alias maps. The existing
  `target_col: <SQL expression>` pattern handles every required
  rename cleanly; no abstraction is needed for the four `external`
  tables and two `nbs` entries actually affected.
- Touching the systemic issues catalogued in
  `LOAD_2_0_PROD.md §Other transform-shape issues to address while
  you're in there` (sentinel-chartno filtering, `DISTINCT ON` vs
  the existing dedupe pass, per-column `LEFT(...)` instead of the
  widen/narrow wrapper). Those are real but orthogonal; one of
  them (varchar overflow) is already papered over and works.
- App-code changes. Canonical column names are not changing, so
  backend services, ORM, and frontend keep reading what they
  already read; audited and confirmed.

## Decisions

### 1. Minimal-diff in-place column edits, not a YAML refactor

For each affected table, change the offending SQL expression in
`columns:` (and `sample_id:` where applicable) to reference the
real source column. Nothing else moves.

**Why:** The existing pattern
(`target_col: <SQL expression that can reference any staging col>`)
already supports per-schema differences — each schema's section is
already a separate YAML block. The mismatches are mechanical
(`AA-X` → `X`, `Enzyme-X` → `X`, `ABG/GAA` → `ABG_GAA`,
`Sample_name` vs `<X>_Filter_Num`-as-the-real-suffix etc.) and
fit naturally as edits to those expressions. Six entries are
affected. Introducing a column-alias map layer would add
abstraction overhead with no second client.

**Alternatives considered:**
- **Per-source-schema column alias map** (top-level `aliases:`
  block keyed by `<schema>.<table>.<target_col>`). Rejected:
  no second consumer; would obscure the per-table SQL
  expressions that already cover non-trivial cases (`COALESCE`,
  `CAST`, `LEFT(...)`).
- **Auto-derive aliases from `information_schema.columns` at
  generation time.** Rejected: would make `gen_transform_2_0.py`
  depend on a live PG connection (today it's pure file-in /
  file-out), and the canonical naming is more opinionated than
  a heuristic could safely guess.

### 2. Keep dead-source entries (e.g. `external.{opd, gag, outbank}`)

`Out_hospital` doesn't currently have these tables. The
generator wraps every per-table block in a `DO $$ … END$$` that
checks `to_regclass(<stg_table>)` and `RAISE NOTICE`s instead of
failing if the source is missing. Stage transform stays green
across deployments that vary in source coverage.

**Why:** Removing the entries would lose the hook for future
`Out_hospital` schema additions and would be inconsistent with
the rest of the YAML (e.g. `nbs.biomarker` uses `filter: FALSE`
for a similar reason). The cost is one `NOTICE` line per missing
table during the transform — operationally negligible.

### 3. Fix `main.outbank` even though the immediate blocker is in `external`/`nbs`

The real `2.0.outbank` source column is `Outbank_Sample_name`,
not `Outbank_Sampleno`. Stage currently has both columns only
because a `GENERATED ALWAYS AS ("Outbank_Sample_name")` alias
was added during the failed attempt; a fresh extract would
recreate the table from MySQL and only have `Outbank_Sample_name`,
so the YAML must reference the real name.

**Why:** Without this fix, the next clean extract reintroduces
the `column "Outbank_Sampleno" does not exist` failure.
Bundling it with the `external` / `nbs` fixes keeps the
"YAML matches reality" PR self-contained.

### 4. `nbs.ms` keeps a single `leu` target

`new_born_screen.ms` has `LEU` only — no `ILE` column, no
`Leu/Ile` combined column. The current YAML maps `leu →
"Leu/Ile"` which is wrong for this source. We map `leu → "LEU"`
and lose the `Ile` portion only because the source doesn't
carry it. `main.ms/ms` and `external.ms/ms` keep
`leu → "Leu/Ile"` / `leu → "AA-Leu/Ile"` because their sources
do have that combined column.

**Why:** Target schema is `nbs.msms.leu` (singular). Mapping a
column that doesn't exist would be the bug; preserving the
combined name in the SQL would just throw. Data fidelity is
preserved for the sources that have the combined column.

## Risks / Trade-offs

**[Risk]** Renamed identifiers contain characters that need PG
quoting differently from the bare names (`ABG_GAA` vs
`ABG/GAA`; `母姓名` etc.). → **Mitigation:** the generator
already double-quotes every identifier in `q_ident()` and tests
this against the broad set of existing Chinese / dash / slash /
space column names — `ABG_GAA` is strictly *simpler* to quote
than `ABG/GAA`. After regeneration, `git diff
transform_2_0.sql` is reviewed by eye and a grep cross-check
(see tasks.md verification step) confirms no
`AA-` / `Enzyme-` / `MS/MS-` / `GAG-` references survive
outside `stg_main.*` blocks.

**[Risk]** Stage data has rows where the corrected column is
NULL or out of expected range, surfacing a new error class
(NOT NULL violation, varchar overflow, FK miss) that the old
"column does not exist" failure masked. → **Mitigation:**
`transform_2_0_wrapped.sh` widens canonical columns to TEXT for
the transform, narrows back with `LEFT(...)`; existing
`COALESCE(..., default)` in the YAML covers NOT NULL targets
for `sample_name`, `result`, `specimen_type`, `birthday`, etc.
The transaction-wrapped transform rolls back on error and
leaves canonical untouched — observable failure mode is
"transform exits non-zero, services keep serving 1.0 data".

**[Risk]** Stage canonical data is overwritten in error.
→ **Mitigation:** the existing pre-attempt backup at
`~/db-backups/gimc-pre-2.0-20260514-0826.sql.gz` (5 MB,
validated, restores the 1.0 baseline at 39,621 main patients)
is the documented rollback in `LOAD_2_0_PROD.md §Rollback`;
keep until migration is confirmed good.

**[Trade-off]** Several staging tables remain unused
(`external.aadc/ald/mma/mps2`, `nbs.aadc/ald/lsd/mma/mps2/tgal/tsh`).
Real source data is dropped on the floor at transform time. The
scope-correct fix is an additive alembic migration to extend the
canonical schema, then a follow-up YAML PR — explicitly deferred
here to keep this change a pure rename.
