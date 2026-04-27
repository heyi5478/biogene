# cohort-export Specification

## Purpose
TBD - created by archiving change add-cohort-report-export. Update Purpose after archive.
## Requirements
### Requirement: ConditionResults SHALL expose a cohort-export entry point on the 名單 tab

`frontend/src/components/ConditionResults.tsx` MUST render a "匯出比較報告" button inside the 名單 tab, on the same row as the condition summary chips and the matched-patient count. The button MUST be enabled when `matchedPatients.length > 0` and disabled otherwise. Clicking it MUST open a `CohortExportDialog` populated with the current matched-patient list. The button MUST NOT appear on the 族群統計 tab. The existing 名單 tab DOM (chips, count, table, "查看" row action) MUST remain unchanged apart from the new button.

#### Scenario: Button renders on 名單 tab and is enabled when cohort has patients

- **WHEN** the user runs a condition query that matches at least one patient
- **AND** the 名單 tab is active
- **THEN** a "匯出比較報告" button MUST be visible on the chip row
- **AND** the button MUST be enabled
- **AND** the existing condition chips and matched count MUST still render

#### Scenario: Button is disabled when no patients match

- **WHEN** the user runs a condition query that matches zero patients
- **THEN** the "匯出比較報告" button MUST still render
- **AND** MUST be disabled
- **AND** clicking it MUST NOT open the dialog

#### Scenario: Button is absent on 族群統計 tab

- **WHEN** the user switches to the 族群統計 tab
- **THEN** the "匯出比較報告" button MUST NOT be rendered inside that tab's content

#### Scenario: Clicking the button opens CohortExportDialog with the matched patients

- **WHEN** the user clicks the enabled "匯出比較報告" button
- **THEN** a `CohortExportDialog` MUST open
- **AND** the dialog's `patients` prop MUST be the array of `Patient` references taken from the current `matchedPatients` (in the same order)

### Requirement: CohortExportDialog SHALL offer module selection and filename editing for XLSX-only export

`CohortExportDialog` MUST present:
1. A title that includes the cohort size (e.g. `匯出比較報告 — N 位病人`).
2. A checkbox list of all exportable modules (every `MODULE_DEFINITIONS` entry whose `id !== 'basic'`); each row MUST show the module code and a count of how many records that module has across the entire cohort.
3. A `全選／全不選` toggle.
4. An editable filename prefix input pre-filled with `cohort_{yyyyMMdd}`.
5. A `匯出` confirm button and a `取消` button.

The dialog MUST NOT render a format selector (XLSX is the only supported format in this capability). Modules whose total cohort record count is zero MUST still be listed but unchecked by default; modules with at least one cohort record MUST be checked by default. The user MUST be able to toggle any module regardless of default.

#### Scenario: Default module selection reflects cohort-wide data presence

- **WHEN** the dialog opens for a cohort where at least one patient has `enzyme.length > 0` and no patient has `aa.length > 0`
- **THEN** the `enzyme` checkbox MUST be checked by default
- **AND** the `aa` checkbox MUST be unchecked by default
- **AND** both MUST remain user-toggleable

#### Scenario: Default filename prefix uses cohort prefix and today's date

- **WHEN** the dialog opens on 2026-04-23
- **THEN** the filename prefix input MUST be initialized to `cohort_20260423`

#### Scenario: Empty module selection disables confirm

- **WHEN** the user unchecks every module
- **THEN** the `匯出` confirm button MUST be disabled

#### Scenario: Empty filename prefix disables confirm

- **WHEN** the user clears the filename prefix input
- **THEN** the `匯出` confirm button MUST be disabled

#### Scenario: Title shows cohort size

- **WHEN** the dialog opens for a cohort of 7 patients
- **THEN** the dialog title MUST include the substring `7 位病人`

### Requirement: Cohort XLSX export SHALL emit one workbook with one sheet per selected module

Confirming the `CohortExportDialog` MUST dynamically import the `xlsx` library and emit a single `<prefix>.xlsx` file. Each selected module MUST become exactly one worksheet. Sheet names MUST be derived from the module identifier, truncated to 31 characters (Excel limit), and MUST be unique within the workbook. The `xlsx` library MUST remain lazy-loaded (no addition to the initial bundle).

For each sheet:
- The first three columns MUST be `patientId`, `name`, `chartno` (in that order). The `chartno` value MUST follow the fallback chain `chartno || externalChartno || nbsId || patientId`.
- The remaining columns MUST be derived from `MODULE_FIELDS[moduleId]`, using each field's `label` as the column header, in the order defined in `MODULE_FIELDS`.

For each patient in the export's `patients` array:
- If `patient[moduleId]` is a non-empty array, the sheet MUST emit one row per record. The leading three columns MUST be repeated on every row for that patient. Each module column MUST contain `record[field.id]` (or empty string when undefined / null).
- If `patient[moduleId]` is empty or missing, the sheet MUST emit exactly one row with the leading three columns filled and every module column blank.

For the `basic` module specifically, fields MUST be read directly from the patient object (not from an array), and exactly one row per patient MUST be emitted.

#### Scenario: Workbook contains one sheet per selected module with unique 31-char names

- **WHEN** the user selects modules `enzyme`, `aa`, `msms` and confirms
- **THEN** the downloaded `<prefix>.xlsx` MUST contain exactly three worksheets
- **AND** every sheet name MUST be ≤ 31 characters
- **AND** all sheet names MUST be unique

#### Scenario: Sheet leading columns are patientId / name / chartno with fallback

- **WHEN** any sheet of the cohort workbook is opened
- **THEN** the first three column headers MUST be `patientId`, `name`, `chartno` (in that order)
- **AND** for a patient whose `chartno` is null but `nbsId` is `"NBS-9001"`, that patient's `chartno` cell value MUST be `"NBS-9001"`
- **AND** for a patient whose `chartno`, `externalChartno`, and `nbsId` are all null, the cell value MUST be that patient's `patientId`

#### Scenario: Multi-record patient produces multiple rows

- **WHEN** the cohort contains a patient with three `aa` records and the user exports with `aa` selected
- **THEN** the `aa` sheet MUST contain three rows whose first three columns all repeat that patient's identifier values
- **AND** the module columns of those three rows MUST contain that patient's three records' values respectively

#### Scenario: Selected patient with no records appears as a single blank-data row

- **WHEN** the cohort contains a patient with `aa.length === 0` and the user exports with `aa` selected
- **THEN** the `aa` sheet MUST contain exactly one row for that patient with the first three columns filled and every module column blank

#### Scenario: basic module emits one row per patient from patient-level fields

- **WHEN** the user exports with `basic` selected and a cohort of 5 patients
- **THEN** the `basic` sheet MUST contain exactly 5 data rows
- **AND** the column for `MODULE_FIELDS.basic` field `diagnosis` MUST contain each patient's `patient.diagnosis` value (not from any array)

#### Scenario: xlsx library is lazy-loaded

- **WHEN** a session never opens the cohort export dialog and never confirms a cohort export
- **THEN** the `xlsx` library MUST NOT be present in the initial page bundle for that session

### Requirement: Cohort export filename SHALL follow the `cohort_YYYYMMDD` convention by default

The downloaded file MUST be named `<prefix>.xlsx` where `<prefix>` is the value of the dialog's filename prefix input at confirm time. The default value of that input MUST be `cohort_<yyyyMMdd>` using today's date in the user's local timezone, formatted with zero-padded month and day.

#### Scenario: Default download filename on 2026-04-23

- **WHEN** the user opens the dialog on 2026-04-23 and confirms without editing the prefix
- **THEN** the downloaded file name MUST be `cohort_20260423.xlsx`

#### Scenario: User-edited prefix is honored

- **WHEN** the user changes the prefix to `pku-cohort_2026Q1` and confirms
- **THEN** the downloaded file name MUST be `pku-cohort_2026Q1.xlsx`

### Requirement: Shared XLSX helpers SHALL be extracted and reused

`uniqueSheetName` MUST live in a single shared module (`frontend/src/utils/exporters/_sheetName.ts`) and MUST be imported by both the single-patient `xlsxExporter` and the cohort XLSX exporter. `todayStamp` MUST live in a single shared module (`frontend/src/utils/dateStamp.ts`) and MUST be imported by both `ExportDialog` and `CohortExportDialog`. Neither helper MUST be duplicated across files.

#### Scenario: uniqueSheetName has exactly one definition

- **WHEN** the codebase is grepped for `function uniqueSheetName` (or equivalent named export)
- **THEN** exactly one definition MUST be found, located in `frontend/src/utils/exporters/_sheetName.ts`

#### Scenario: todayStamp has exactly one definition

- **WHEN** the codebase is grepped for `function todayStamp` (or equivalent named export)
- **THEN** exactly one definition MUST be found, located in `frontend/src/utils/dateStamp.ts`

### Requirement: exportPatients dispatcher SHALL provide the cohort export entry API

`frontend/src/utils/exporters/index.ts` MUST export an `exportPatients(patients, options)` function with `options: { format: 'xlsx'; modules: ModuleId[]; filenamePrefix: string }`. The function MUST switch on `options.format` and call the cohort XLSX exporter for `'xlsx'`. The switch MUST include an exhaustiveness guard so that adding a new format variant is a compile error until handled. The single-patient `exportPatient` function and its API MUST remain unchanged.

#### Scenario: exportPatients with format xlsx invokes the cohort xlsx exporter

- **WHEN** `exportPatients(patients, { format: 'xlsx', modules, filenamePrefix: 'cohort_20260423' })` is called
- **THEN** a single `cohort_20260423.xlsx` file MUST be produced via the cohort XLSX exporter

#### Scenario: Single-patient export entry point is preserved

- **WHEN** `exportPatient(patient, { format: 'csv', modules, filenamePrefix })` is called after this change ships
- **THEN** the behaviour MUST be identical to the pre-change behaviour (same zip layout, same headers, same fallback chain)

