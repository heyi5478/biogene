# mock-data-layer Specification

## Purpose
TBD - created by archiving change restructure-mockdata-for-db-alignment. Update Purpose after archive.
## Requirements

### Requirement: Mock data SHALL be organized as one JSON file per database table

Mock data MUST be stored under `backend/mock-data/` with three top-level directories — `db_main/`, `db_external/`, `db_nbs/` — each corresponding to one logical MySQL database (`2.0`, `2.0 外院資料庫`, `new_born_screening`). Within each directory, every database table MUST be represented by exactly one JSON file named `<table>.json`, whose contents are a JSON array of records.

#### Scenario: New table is added to a database
- **WHEN** a contributor needs to add a new table to `db_main`
- **THEN** they MUST create exactly one new file `backend/mock-data/db_main/<table>.json` containing a JSON array
- **AND** they MUST NOT add the table's records to any other JSON file

#### Scenario: Microservice loads only its owned tables
- **WHEN** `svc-lab` starts up and needs only `aa`, `msms`, `biomarker`, `lsd`, `enzyme`, `gag`, `dnabank`, `outbank` tables
- **THEN** it MUST be able to load only those JSON files without parsing tables it does not own

### Requirement: Each patient record SHALL have a deterministic UUID v5 patientId

Every record in any `patient.json` MUST have a `patientId` field whose value is a UUID v5 generated from a stable seed `f"{source}:{naturalKey}"`, where `source ∈ {"main", "external", "nbs"}` and `naturalKey` is `chartno` (main), `externalChartno` (external), or `nbsId` (nbs). Re-running the generator on the same seed MUST produce the same UUID.

#### Scenario: Generator runs twice on identical seed data
- **WHEN** `python backend/scripts/generate_mock.py` is executed twice in succession
- **THEN** every `patientId` in the output JSON files MUST be byte-identical between the two runs
- **AND** all foreign-key references from sample tables MUST remain valid

#### Scenario: Patient natural key is unique within its source
- **WHEN** the generator processes a `db_main` patient with `chartno = "A1234567"`
- **THEN** the resulting `patientId` MUST equal `uuid5(NAMESPACE_OID, "main:A1234567")`

### Requirement: Sample tables SHALL reference patients by patientId, not chartno

Every record in every non-`patient.json` table MUST include a `patientId` field that points to a `patientId` in the corresponding `patient.json` of the same database. Sample records MUST NOT use `chartno` as a foreign key, because external and NBS patients may not have a chartno.

#### Scenario: Sample row is created for an external patient with no chartno
- **WHEN** an `aa.json` row is added under `db_external/`
- **THEN** the row MUST have a `patientId` field referencing a `patientId` in `db_external/patient.json`
- **AND** the row MUST NOT depend on `chartno` for identification

#### Scenario: FK validator catches dangling reference
- **WHEN** a sample row's `patientId` does not exist in the corresponding `patient.json`
- **AND** `python backend/scripts/load_mock.py` is executed
- **THEN** the script MUST exit with non-zero status and report the offending row

### Requirement: NBS sub-tables SHALL reference parent test rows by parent id

Records in `db_nbs/cah_tgal.json` MUST include a `cahId` field referencing a `cahId` in `db_nbs/cah.json`. Records in `db_nbs/dmd_tsh.json` MUST include a `dmdId` field referencing a `dmdId` in `db_nbs/dmd.json`.

#### Scenario: tgal sub-row references its parent cah row
- **WHEN** the loader reads `db_nbs/cah_tgal.json`
- **THEN** every `cahId` in the file MUST resolve to a record in `db_nbs/cah.json`

#### Scenario: FK validator catches dangling sub-table reference
- **WHEN** a `dmd_tsh.json` row references a `dmdId` not present in `dmd.json`
- **AND** `load_mock.py` is run
- **THEN** the validator MUST report the dangling reference and exit non-zero

### Requirement: Frontend SHALL load JSON mock data via Vite JSON imports and join by patientId

The file `frontend/src/data/mockData.ts` MUST import the JSON files from `backend/mock-data/` using Vite's native JSON import syntax, then join sample tables onto patient records by `patientId` to produce the existing `mockPatients: Patient[]` export. The join MUST happen at module load time (not async), and the exported shape MUST remain compatible with all existing consumers.

#### Scenario: Existing consumer reads patient sample arrays
- **WHEN** `frontend/src/components/ConditionResults.tsx` imports `mockPatients` and reads `patient.aa[0].Phe`
- **THEN** the value MUST equal the value from `db_main/aa.json` row whose `patientId` matches the patient

#### Scenario: Frontend build succeeds
- **WHEN** `npm run build` is executed in `frontend/`
- **THEN** Vite MUST resolve all JSON imports and produce a clean build with no errors

### Requirement: Mock data SHALL preserve the existing 5 main DB patients without behavioral regression

The five existing patients in `db_main/patient.json` (chartno A1234567, B2345678, C3456789, D4567890, E5678901) MUST retain their current `name`, `birthday`, `sex`, `diagnosis*`, and all original sample data. Running existing condition templates against the new mock MUST produce the same hit counts as before this change.

#### Scenario: Existing condition template produces same results
- **WHEN** the user runs the "Biomarker 異常" template (`dbsLysoGb3 > 5`)
- **THEN** the matched patient set MUST be identical to the pre-change result

#### Scenario: Patient text search by chartno still works
- **WHEN** the user searches for "A1234567"
- **THEN** the patient "陳志明" MUST appear in the results

### Requirement: load_mock.py SHALL expose a stable Python API for FastAPI services to consume

In addition to its existing CLI behavior, `backend/scripts/load_mock.py` MUST provide two importable functions with stable signatures:

- `load_all() -> dict[str, dict[str, list[dict]]]` — returns the full mock dataset keyed by `database_name -> table_name -> list_of_rows`
- `validate(data: dict | None = None) -> None` — when `data` is None, internally calls `load_all()`; raises `ValueError` (with offending file/row/field) if any FK constraint fails; returns `None` on success

These two functions MUST be importable as `from backend.shared.data_loader import load_all, validate` (the `shared` module re-exports them to decouple services from script layout).

#### Scenario: Service imports and validates at startup
- **WHEN** a FastAPI service executes `from backend.shared.data_loader import validate` during `lifespan` startup and calls `validate()`
- **THEN** the call MUST complete without exception on valid mock data
- **AND** MUST NOT require spawning a subprocess or parsing CLI output

#### Scenario: Service loads data once and caches in memory
- **WHEN** a service calls `load_all()` inside its `lifespan` context
- **THEN** the return value MUST be a plain Python `dict` that the service can keep as an in-process cache
- **AND** subsequent HTTP requests MUST NOT re-read JSON files from disk

#### Scenario: Validation failure raises typed error
- **WHEN** a sample row references a non-existent `patientId` and `validate()` is called
- **THEN** it MUST raise `ValueError` whose message identifies the database, table, row index, and offending key
- **AND** the existing CLI entrypoint (`python backend/scripts/load_mock.py`) MUST still exit non-zero as before
