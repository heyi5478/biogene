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

- [x] 6.1 `git switch -c fix/etl-2-0-column-mapping-out-hospital-nbs`.
- [x] 6.2 `git add backend/etl/column_mapping_2_0.yaml backend/etl/transform_2_0.sql openspec/changes/fix-etl-2-0-column-mapping/`.
- [x] 6.3 Commit `2f66f56` on `fix/etl-2-0-column-mapping-out-hospital-nbs`.
- [x] 6.4 Pushed to `origin/fix/etl-2-0-column-mapping-out-hospital-nbs`.
- [x] 6.5 PR opened: https://github.com/heyi5478/biogene/pull/61

## 7. Post-merge stage end-to-end (per `backend/etl/LOAD_2_0_PROD.md §Resume`)

- [x] 7.1 SCP'd to stage; md5 verified.
- [x] 7.2 Extract: 43 tables / 2,260,387 rows (matches doc baseline; 1m08s wall-clock incl. Docker pip install).
- [x] 7.3 Dedupe: stg_main."基本資料" 8040, stg_main."opd" 206, stg_external."基本資料" 4894, stg_nbs."nbs" 8447, stg_nbs.{"系統外自費","門診個案"} 0+0; 0.66s.
- [x] 7.4 Wrapped transform: 0 ERROR, 56s wall-clock, final `COMMIT` reached. NOTICEs limited to TRUNCATE CASCADE and the four expected `missing source %, skipping` lines (`stg_external.{opd,gag,outbank}`, `stg_nbs.biomarker`) — design-intended `to_regclass` skips.
- [x] 7.5 Canonical row counts post-transform: **main.patient 39,621 → 70,518** (+30,897), **external.patient 3 → 58,984** (+58,981), **nbs.patient 5 → 53,670** (+53,665). main.{aa 10976, opd 12264, enzyme 16224, msms 18347, outbank 3364}; external.{aa 434, enzyme 0 (source `stg_external.enzyme` itself is empty — Out_hospital-side data emptiness, not a column-mapping bug), lsd 30927, msms 2677}; nbs.{bd 50564, cah 49601, g6pd 45647, msms 55932, sma_scid 50556}.
- [x] 7.6 Restarted svc-patient/svc-lab/svc-disease/gateway then proxy. Cold-start cache reload from 2.0-sized PG took longer than the 15s the runbook documents for 1.0 data — `svc-patient` finished at +7 min (loaded **183,172 patients + 12,264 opd rows** = 70518+58984+53670, exact match), `svc-disease` finished at +11 min (indexed **267,908 rows across 12 modules**). All three services + gateway + proxy report healthy.
- [x] 7.7 `GET /healthz` → 200 `ok`; `GET /api/healthz` → 200 `{"status":"ok","service":"gateway"}`; `GET /api/patients/<uuid>` round-trip verified twice — first against an opd-empty patient (`魏嘉緯`, chartno `1068912-0`), then one with lab data (`胥    磊`, chartno `4509850`) showing `aa`+`msms`+`dnabank` rows with the renamed canonical columns (`Gln`/`Citr`/`Ala`/`Arg`, `Ala`/`Arg`/`Cit`/`Gly`, `orderno`/`order`/`orderMemo`) populated correctly.
- [x] 7.8 Stage verified — no rollback needed.
