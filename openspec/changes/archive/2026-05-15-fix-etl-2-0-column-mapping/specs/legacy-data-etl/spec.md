## ADDED Requirements

### Requirement: 2.0 → 3.0 column mapping SHALL handle per-source-schema column-naming variation

`backend/etl/column_mapping_2_0.yaml` MUST express column references per source MySQL schema, because the three legacy databases (`2.0`, `Out_hospital`, `new_born_screen`) do not share one column-naming convention; every SQL expression in each `<schema>.<table>` entry's `columns:` map (and `sample_id:` when set) MUST reference a column that exists in the corresponding staging table (`stg_main` / `stg_external` / `stg_nbs`).

The naming variation that MUST be honoured includes:

- `2.0` uses `<table>-<field>` for text and many numeric columns
  (e.g. `aa.AA-Result`, `enzyme.Enzyme-檢體類別`,
  `gag.GAG-技術人員`, `ms/ms.MS/MS-Result`).
- `Out_hospital` drops those prefixes on most tables
  (`aa.Result`, `enzyme.檢體類別`), but on `ms/ms` it *adds* an
  `AA-` prefix to amino-acid columns that `2.0/ms/ms` leaves bare.
- `new_born_screen` uses upper-case amino acid abbreviations
  (`ms.ALA`, `ms.ARG`, …) with `LEU` only (no `Leu/Ile` combined
  column), and single-digit acylcarnitine labels
  (`ms.C2`/`C3`/`C5`, not zero-padded `C02`/`C03`/`C05`); its
  `門診個案` patient table uses `母姓名`, not `OPD_母姓名`.

Authority for the column lists is `information_schema.columns` of the staging schema after extract; any divergence between YAML and staging is a defect. Where a source MySQL table is absent in a given source DB, its YAML entry MAY remain — the generator's `to_regclass(<stg_table>)` guard in `gen_transform_2_0.py` MUST emit `RAISE NOTICE 'missing source %, skipping'` and the transform MUST continue. Where a source staging column exists but the canonical 3.0 target table does not, the staging data SHALL remain unmapped until a schema migration extends the target.

#### Scenario: external schema column drops the AA- prefix

- **GIVEN** `stg_external.aa` has columns `檢體類別`, `Result`, and
  `Leu` (no `AA-` prefix, per `Out_hospital`'s actual schema)
- **WHEN** `transform_2_0.sql` is generated from
  `column_mapping_2_0.yaml`
- **THEN** the `INSERT INTO external.aa` block MUST reference
  `"檢體類別"`, `"Result"`, and `"Leu"`
- **AND** MUST NOT reference `"AA-檢體類別"`, `"AA-Result"`, or
  `"AA-Leu"` in that block

#### Scenario: external/ms-ms is the inverted case and gains the AA- prefix

- **GIVEN** `stg_external."ms/ms"` has columns `AA-Ala` / `AA-Arg` /
  `AA-Leu/Ile` (Out_hospital's ms/ms table does have the prefix)
- **WHEN** `transform_2_0.sql` is generated
- **THEN** the `INSERT INTO external.msms` block MUST reference
  `"AA-Ala"`, `"AA-Arg"`, and `"AA-Leu/Ile"`
- **AND** the `INSERT INTO main.msms` block MUST still reference
  the unprefixed names `"Ala"`, `"Arg"`, `"Leu/Ile"` because
  `stg_main."ms/ms"` uses the unprefixed form

#### Scenario: nbs/ms uses uppercase amino acids and unpadded acylcarnitines

- **GIVEN** `stg_nbs.ms` has columns `ALA`, `ARG`, `LEU` (no `ILE`,
  no combined `Leu/Ile`), and `C2`, `C3`, `C5`
- **WHEN** `transform_2_0.sql` is generated
- **THEN** the `INSERT INTO nbs.msms` block MUST reference `"ALA"`,
  `"ARG"`, `"LEU"`, `"C2"`, `"C3"`, `"C5"`
- **AND** MUST NOT reference `"Ala"`, `"Leu/Ile"`, `"C02"`, `"C03"`,
  or `"C05"` in that block

#### Scenario: missing source table is skipped, not failed

- **GIVEN** `Out_hospital` does not contain a `gag` table on a
  particular deployment, so `stg_external.gag` is absent
- **AND** `column_mapping_2_0.yaml` still has an
  `external.sample_tables[gag]` entry
- **WHEN** `transform_2_0.sql` runs
- **THEN** the surrounding `DO $$ … END$$` block MUST detect
  `to_regclass('stg_external.gag') IS NULL` and `RAISE NOTICE
  'missing source %, skipping'`
- **AND** the wrapping transaction MUST NOT roll back; subsequent
  table blocks MUST continue
