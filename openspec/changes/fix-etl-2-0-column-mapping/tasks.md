## 1. Edit YAML — `external` schema

- [x] 1.1 `schemas.external.sample_tables[aa]`: drop `AA-` prefix from `specimen_type`, `result`, and the eight amino-acid columns (`gln`, `citr`, `ala`, `arg`, `leu`, `val`, `phe`, `tyr`); keep `sample_name` referencing `AA_Sample_name` (unchanged).
- [x] 1.2 `schemas.external.sample_tables[enzyme]`: drop `Enzyme-` prefix from `specimen_type`, `technician`, `result`, and `enzyme_mps2` (becomes `"MPS2"`); keep `mps1` and `sample_name` unchanged.
- [x] 1.3 `schemas.external.sample_tables[lsd]`: rename `abg_gaa` source from `"ABG/GAA"` to `"ABG_GAA"`; other columns unchanged.
- [x] 1.4 `schemas.external.sample_tables[ms/ms]`: drop `MS/MS-` prefix from `specimen_type` and `result`; *add* `AA-` prefix to the nine amino-acid sources (`ala`/`arg`/`cit`/`gly`/`leu`/`met`/`phe`/`tyr`/`val`); leave `c0`/`c2`/`c3`/`c5` unchanged (Out_hospital uses the same zero-padded names as 2.0).

## 2. Edit YAML — `nbs` schema

- [x] 2.1 `schemas.nbs.patient_sources[門診個案]`: change `name` from `"OPD_母姓名"` to `"母姓名"`; other columns already match.
- [x] 2.2 `schemas.nbs.sample_tables[ms]`: rename amino-acid sources to upper-case (`"ALA"`, `"ARG"`, `"CIT"`, `"GLY"`, `"MET"`, `"PHE"`, `"TYR"`, `"VAL"`); change `leu` source from `"Leu/Ile"` to `"LEU"` (this source carries only `LEU`); change `c2`/`c3`/`c5` source from `"C02"`/`"C03"`/`"C05"` to `"C2"`/`"C3"`/`"C5"`; leave `c0` unchanged.

## 3. Edit YAML — `main` schema

- [x] 3.1 `schemas.main.sample_tables[outbank]`: change `sample_id` from `Outbank_Sampleno` to `Outbank_Sample_name`; change `columns.sampleno` source from `"Outbank_Sampleno"` to `"Outbank_Sample_name"`; leave `shipdate`/`assay`/`result` unchanged.

## 4. Regenerate transform SQL

- [x] 4.1 Run `python3 backend/etl/gen_transform_2_0.py` from repo root; expect a `wrote …/transform_2_0.sql (N lines)` message and zero stderr. (956 lines written.)

## 5. Verify diffs

- [x] 5.1 `git diff --stat backend/etl/` lists exactly two files: `column_mapping_2_0.yaml` and `transform_2_0.sql`. (82 ins / 82 del each, 1:1 line edits as expected.)
- [x] 5.2 `git diff backend/etl/column_mapping_2_0.yaml` shows only the edits from §1–§3 (no whitespace-only or order changes).
- [x] 5.3 `git diff backend/etl/transform_2_0.sql` shows column-name substitutions inside `external.*`, `nbs.*`, and `main.outbank` blocks only — 9 hunks, all in `main.outbank` (lines 398, 402), `external.aa` (513-522), `external.enzyme` (569-573), `external.lsd` (623), `external.msms` (644-654), `nbs.門診個案` (763), `nbs.msms` (794-806). No collateral changes.
- [x] 5.4 Grep cross-check (refined via awk per-block scan since `grep -v stg_main` doesn't respect block boundaries): the only prefixed references outside `stg_main.*` blocks are (a) `external.gag` block — intentional placeholder, source `stg_external.gag` doesn't exist and `to_regclass` guard skips at runtime; and (b) `external.msms` block — correct AA- prefixes for the inverted case (Out_hospital's `ms/ms` table actually uses the prefix, per the spec scenario "external/ms-ms is the inverted case").
- [x] 5.5 Grep cross-check — `grep -E '"(Leu/Ile|C0[235])"' backend/etl/transform_2_0.sql | grep stg_nbs` returns no rows (the nbs ms block no longer references the combined or zero-padded names).

## 6. Commit and PR

- [ ] 6.1 `git switch -c fix/etl-2-0-column-mapping-out-hospital-nbs`.
- [ ] 6.2 `git add backend/etl/column_mapping_2_0.yaml backend/etl/transform_2_0.sql openspec/changes/fix-etl-2-0-column-mapping/`.
- [ ] 6.3 Commit with body: rename catalogue (external `aa`/`enzyme`/`lsd`/`ms/ms`, nbs `門診個案`/`ms`, main `outbank`); regenerated SQL; openspec change attached.
- [ ] 6.4 `git push -u origin fix/etl-2-0-column-mapping-out-hospital-nbs`.
- [ ] 6.5 `gh pr create` — title `fix(etl): align column_mapping_2_0.yaml with actual MySQL source schemas`; body links `backend/etl/LOAD_2_0_PROD.md §What's broken` for the full catalogue, lists the test plan checkboxes from §5.

## 7. Post-merge stage end-to-end (per `backend/etl/LOAD_2_0_PROD.md §Resume`)

- [ ] 7.1 SCP regenerated `transform_2_0.sql` and updated `column_mapping_2_0.yaml` to `user@10.19.209.19:/home/user/my-project/backend/etl/`.
- [ ] 7.2 Re-run extract (Docker python:3.12-slim, ~4 sec; replaces `stg_main`/`stg_external`/`stg_nbs`).
- [ ] 7.3 Re-run `dedupe_2_0_staging.sql` (handles dup-chartno rows that would break `ON CONFLICT DO UPDATE`).
- [ ] 7.4 Run `transform_2_0_wrapped.sh`; expect zero `ERROR:` lines and a final `COMMIT`.
- [ ] 7.5 Verify canonical counts — `main.patient` / `external.patient` / `nbs.patient` should rise well above the 1.0 baseline (39,621 / 3 / 5).
- [ ] 7.6 Restart `svc-patient svc-lab svc-disease gateway`, wait 15 s, then restart `proxy` (nginx DNS cache will 502 if `proxy` doesn't follow).
- [ ] 7.7 Curl `/healthz`, `/api/healthz`, and one random non-sentinel `chartno` via `/api/patients/<uuid>`; expect 200s and shaped JSON.
- [ ] 7.8 Notify requester (per the runbook flow). If 7.4 or 7.5 fails, roll back per `LOAD_2_0_PROD.md §Rollback` (5 MB pre-attempt PG backup at `~/db-backups/gimc-pre-2.0-20260514-0826.sql.gz`).
