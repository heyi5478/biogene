# patient-export Specification

## Purpose
TBD - created by archiving change add-export-and-stats. Update Purpose after archive.
## Requirements

### Requirement: PatientActions SHALL expose an export entry point

`frontend/src/components/PatientActions.tsx` MUST render a "匯出" button that opens an `ExportDialog` scoped to the currently displayed `patient`. The component MUST accept the patient as a prop and MUST own the dialog's open/close state locally. The "匯出" button MUST sit adjacent to the "統計" button inside `PatientActions`.

`PatientActions` MUST be rendered on the same row as the `TabsList` in `frontend/src/pages/Index.tsx`, positioned to the right of the tab triggers, so that the export entry point is always visible while the user browses any tab (`全部 / 基本資料 / 門診 / 檢驗 / 檢體 / 新生兒篩檢`).

The "匯出" button MUST be enabled whenever a patient is displayed; it MUST NOT be disabled, hidden, or gated by which tab is active.

#### Scenario: Export button renders inside PatientActions on every tab

- **WHEN** a patient is selected (either via single-match search or `PatientList` click) and any tab is active
- **THEN** `PatientActions` MUST render a "匯出" button on the tab row
- **AND** `PatientSummary` MUST NOT render a "匯出" button
- **AND** the button MUST be enabled

#### Scenario: Clicking the export button opens the ExportDialog

- **WHEN** the user clicks the "匯出" button in `PatientActions`
- **THEN** an `ExportDialog` MUST open with the same `patient` reference passed into `PatientActions`
- **AND** the dialog MUST NOT alter any state outside itself until the user confirms

### Requirement: ExportDialog SHALL offer three formats and per-module selection

`ExportDialog` MUST present:
1. A format selector (radio group) with options **CSV (zip)**, **JSON**, **XLSX**
2. A checkbox list of modules; modules whose array on the patient is empty MUST still be shown but unchecked by default, while modules with at least one record MUST be checked by default
3. A "全選／全不選" toggle
4. An editable filename prefix input, pre-filled with `{chartno || externalChartno || nbsId || patientId}_{yyyyMMdd}`
5. A "匯出" confirm button and a "取消" button

#### Scenario: Default module selection reflects data presence
- **WHEN** the dialog opens for a patient who has `enzyme.length > 0` but `aa.length === 0`
- **THEN** the `enzyme` checkbox MUST be checked
- **AND** the `aa` checkbox MUST be unchecked
- **AND** both MUST still be selectable by the user

#### Scenario: Filename prefix prefers chartno
- **WHEN** the dialog opens for a patient whose `chartno` is `"A1234567"` on 2026-04-23
- **THEN** the filename prefix input MUST be initialized to `"A1234567_20260423"`

#### Scenario: Fallback filename chain when chartno is missing
- **WHEN** `chartno` is absent but `nbsId` is `"NBS-9001"`
- **THEN** the prefix MUST fall back to `"NBS-9001_<yyyyMMdd>"`
- **AND** if all identifiers are missing, the prefix MUST fall back to `patientId`

### Requirement: JSON export SHALL produce a valid PatientBundle subset

Selecting **JSON** and confirming MUST trigger a browser download of a single `.json` file whose content is `JSON.stringify(subset, null, 2)`. `subset` MUST equal the original `patient` object with every module array the user DID NOT select replaced by `[]`. Patient-level fields (`patientId`, `name`, `sex`, `birthday`, etc.) MUST be preserved verbatim.

#### Scenario: JSON download is valid JSON
- **WHEN** the user selects JSON with only `enzyme` module checked and confirms
- **THEN** a file `<prefix>.json` MUST be downloaded
- **AND** the downloaded file MUST parse with `JSON.parse` without error
- **AND** the parsed object's `patient.enzyme` array MUST match `patient.enzyme` element-for-element
- **AND** every other module array in the parsed object MUST be `[]`

### Requirement: CSV export SHALL deliver one CSV per selected module inside a zip

Selecting **CSV (zip)** and confirming MUST dynamically import `jszip` and assemble a zip archive containing one `.csv` file per selected module plus a `manifest.json` describing the patient. Each CSV MUST use column headers derived from `MODULE_FIELDS[moduleId]` — preferring the `label` field for localized Chinese headers — in the order defined in `MODULE_FIELDS`. CSV serialization MUST use `papaparse.unparse` to correctly quote commas, line breaks, and double quotes.

#### Scenario: Zip layout
- **WHEN** the user exports CSV with `enzyme` and `opd` modules selected
- **THEN** the downloaded `<prefix>.zip` MUST contain exactly `enzyme.csv`, `opd.csv`, and `manifest.json`

#### Scenario: CSV header uses localized labels
- **WHEN** `enzyme.csv` is extracted
- **THEN** the header row MUST include `Sample Name`, `檢體類別`, `Result`, `MPS1`, `Enzyme-MPS2` in the order defined by `MODULE_FIELDS.enzyme`

#### Scenario: Field values with commas are safely quoted
- **WHEN** a record contains a comma in a text field (e.g. `diagnosis` or `subDiag1`)
- **THEN** the CSV cell MUST be wrapped in double quotes per RFC 4180
- **AND** the file MUST re-parse correctly with any compliant CSV parser

### Requirement: XLSX export SHALL deliver a single workbook with one sheet per module

Selecting **XLSX** and confirming MUST dynamically import the `xlsx` library and emit a single `<prefix>.xlsx` file. Each selected module MUST be one worksheet. Sheet names MUST be derived from the module identifier, truncated to 31 characters (Excel limit), and MUST be unique within the workbook. Column headers MUST follow the same `MODULE_FIELDS`-based derivation used for CSV.

#### Scenario: Sheet-per-module
- **WHEN** the user selects XLSX with `enzyme`, `lsd`, and `opd` checked
- **THEN** the downloaded `.xlsx` MUST open in Excel with exactly three sheets whose names correspond to those three modules

#### Scenario: XLSX bundle is lazy-loaded
- **WHEN** the user never clicks XLSX export throughout a session
- **THEN** the `xlsx` library MUST NOT appear in the initial page bundle
- **AND** the initial bundle size delta from pre-change MUST NOT exceed the size of `papaparse` (~20KB gzipped)

### Requirement: Export SHALL handle empty and error cases gracefully

If every module checkbox is unchecked, the confirm button MUST be disabled. If the dynamic import of `xlsx` or `jszip` fails, a shadcn `toast` (via the existing toaster in `App.tsx`) MUST display a Chinese error message and the dialog MUST remain open.

#### Scenario: Empty selection disables confirm
- **WHEN** the user unchecks every module
- **THEN** the "匯出" confirm button MUST be disabled

#### Scenario: Dynamic import failure surfaces a toast
- **WHEN** the user selects XLSX and the `xlsx` chunk fails to load
- **THEN** a toast MUST appear with an error message in Traditional Chinese
- **AND** the dialog MUST remain open so the user can retry or switch format
