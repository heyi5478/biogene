# patient-statistics Specification

## Purpose
TBD - created by archiving change add-export-and-stats. Update Purpose after archive.
## Requirements

### Requirement: statsUtils SHALL provide pure functions for descriptive statistics

The module `frontend/src/utils/statsUtils.ts` MUST export pure functions with the following semantics:

- `mean(xs: number[]): number | null` — returns arithmetic mean; returns `null` when `xs.length === 0`
- `stddev(xs: number[]): number | null` — returns sample standard deviation (divisor `n-1`); returns `null` when `xs.length < 2`
- `summarize(xs: number[]): { n, mean, sd, min, max }` where each of `mean`, `sd`, `min`, `max` is `number | null`
- `ageInYears(birthday: string, asOf?: Date): number | null` — whole years between `birthday` and `asOf` (default: `new Date()`); returns `null` when `birthday` fails `Date` parse
- `bucketAge(age: number | null): AgeBucket | null` where `AgeBucket = '0-17' | '18-39' | '40-59' | '60+'`; returns `null` for `null` input
- `filterByDateRange<T>(records: T[], getDate: (r: T) => string | null, min?: string, max?: string): T[]` — inclusive on both ends; records with `null` date are kept only when neither `min` nor `max` is provided
- `filterByValueRange<T>(records: T[], getValue: (r: T) => number | null | undefined, min?: number, max?: number): T[]` — inclusive; records with non-finite value are dropped
- `extractNumericField<T>(records: T[], fieldId: string): number[]` — reads `rec[fieldId]` from each record, drops `undefined`, `null`, and `NaN`
- `formatCell(s: SummaryStats, digits?: number): string` — returns `'—'` for `n=0`, `'v (n=1)'` for `n=1`, `'m ± s (n=k)'` for `n≥2`; `digits` defaults to 2

These functions MUST NOT import from `react`, any UI library, or any component file.

#### Scenario: Mean of three values
- **WHEN** `summarize([12, 14, 16])` is called
- **THEN** the returned object MUST deep-equal `{ n: 3, mean: 14, sd: 2, min: 12, max: 16 }`

#### Scenario: Empty input
- **WHEN** `summarize([])` is called
- **THEN** the result MUST be `{ n: 0, mean: null, sd: null, min: null, max: null }`

#### Scenario: Single-value input yields no SD
- **WHEN** `summarize([42])` is called
- **THEN** the result MUST be `{ n: 1, mean: 42, sd: null, min: 42, max: 42 }`

#### Scenario: Invalid birthday
- **WHEN** `ageInYears('not-a-date')` is called
- **THEN** the return value MUST be `null`

#### Scenario: Age bucket boundaries are inclusive on upper edge
- **WHEN** `bucketAge(17)` is called
- **THEN** the result MUST be `'0-17'`
- **WHEN** `bucketAge(18)` is called
- **THEN** the result MUST be `'18-39'`
- **WHEN** `bucketAge(59)` is called
- **THEN** the result MUST be `'40-59'`
- **WHEN** `bucketAge(60)` is called
- **THEN** the result MUST be `'60+'`

#### Scenario: formatCell renders n-dependent representations
- **WHEN** `formatCell({ n: 0, mean: null, sd: null, min: null, max: null })` is called
- **THEN** the result MUST be `'—'`
- **WHEN** `formatCell({ n: 1, mean: 42, sd: null, min: 42, max: 42 })` is called
- **THEN** the result MUST include `'(n=1)'` and the mean value
- **AND** MUST NOT include the `'±'` character
- **WHEN** `formatCell({ n: 3, mean: 14, sd: 2, min: 12, max: 16 })` is called
- **THEN** the result MUST include `'±'` and `'(n=3)'`

### Requirement: moduleDate SHALL be the single source of truth for per-module date fields

The module `frontend/src/utils/moduleDate.ts` MUST export:
- `MODULE_DATE_FIELD: Record<ModuleId, string | null>` — keyed by every `ModuleId`; value is the record-level date field name, or `null` for modules whose schema has no date
- `getRecordDate(moduleId: ModuleId, rec: unknown): string | null` — returns the date string if present and non-empty, otherwise `null`

The registry MUST match the actual fields in `frontend/src/types/patient.ts` at the time of writing:
- `opd: 'visitDate'`, `aadc: 'date'`, `ald: 'date'`, `mma: 'date'`, `outbank: 'shipdate'`, `bd: 'collectDate'`, `cah: 'collectDate'`, `dmd: 'collectDate'`, `g6pd: 'collectDate'`, `smaScid: 'collectDate'`, `basic: 'birthday'`
- `aa: null`, `msms: null`, `biomarker: null`, `enzyme: null`, `lsd: null`, `mps2: null`, `gag: null`, `dnabank: null`

No other file in `frontend/src/` MAY hard-code a date field name per module.

#### Scenario: Modules without date fields return null
- **WHEN** `getRecordDate('enzyme', { sampleName: 'S1', MPS1: 10 })` is called
- **THEN** the result MUST be `null`

#### Scenario: Modules with date fields return the ISO string
- **WHEN** `getRecordDate('opd', { visitDate: '2025-07-01', diagCode: 'X' })` is called
- **THEN** the result MUST be `'2025-07-01'`

### Requirement: PatientSummary SHALL expose a single-patient statistics entry point

`frontend/src/components/PatientSummary.tsx` MUST render a "統計" button next to the "匯出" button. Clicking it MUST open a `StatsDialog` for the currently displayed patient. The local `calcAge` helper in `PatientSummary.tsx` MUST be removed and replaced with an import of `ageInYears` from `statsUtils`.

#### Scenario: Stats button renders and triggers the dialog
- **WHEN** a patient is displayed
- **THEN** a "統計" button MUST appear in the `PatientSummary` action area
- **WHEN** the user clicks it
- **THEN** a `StatsDialog` MUST mount with the same `patient` prop

#### Scenario: calcAge duplication is removed
- **WHEN** the codebase is searched for `calcAge` function declarations
- **THEN** exactly zero declarations MUST exist in `PatientSummary.tsx`
- **AND** `ageInYears` from `statsUtils.ts` MUST be used in its place

### Requirement: StatsDialog SHALL compute range-bounded descriptive statistics

`StatsDialog` MUST present:
1. A module `Select`; options limited to modules where `patient[moduleId].length > 0` AND `numericFieldsFor(moduleId).length > 0`
2. A field `Select`; options are the numeric fields of the chosen module (from `numericFieldsFor(moduleId)`)
3. Two date inputs (min, max); MUST be disabled when `MODULE_DATE_FIELD[moduleId] === null`, with visible helper text `此模組資料無採檢日期欄位`
4. Two number inputs (min, max) for value range
5. An output area showing `n`, `mean`, `sd`, `min`, `max` from `summarize(values)`
6. A `StatsSparkline` rendered only when the module has a date field AND filtered count ≥ 2

The pipeline MUST be: `records → filterByDateRange (if applicable) → filterByValueRange → extractNumericField → summarize`.

#### Scenario: Numeric-only field options
- **WHEN** the user opens `StatsDialog` and selects module `enzyme`
- **THEN** the field selector MUST include `MPS1` and `Enzyme-MPS2`
- **AND** MUST NOT include `Sample Name`, `檢體類別`, or `Result`

#### Scenario: Date inputs disabled for dateless modules
- **WHEN** the user selects module `enzyme`
- **THEN** both date inputs MUST be disabled
- **AND** the helper text `此模組資料無採檢日期欄位` MUST be visible

#### Scenario: Empty filtered set shows explicit message
- **WHEN** after applying filters `n === 0`
- **THEN** the output area MUST display `無資料符合條件`
- **AND** MUST NOT display the sparkline

#### Scenario: Sparkline only appears when meaningful
- **WHEN** the filtered records for module `aadc` field `conc` have `n = 4` and all have non-null `date`
- **THEN** the sparkline MUST render with 4 data points, sorted by date ascending
- **WHEN** `n < 2`
- **THEN** the sparkline MUST NOT render

### Requirement: StatsSparkline SHALL use Recharts with a fixed compact layout

`StatsSparkline` MUST use `recharts` (already installed) to render a `LineChart` of size approximately 320×120 pixels with `XAxis dataKey="date"` and `YAxis` auto-domain. Input data MUST be sorted by date ascending and MUST exclude records lacking a parseable date.

#### Scenario: Unsorted input is displayed sorted
- **WHEN** input contains records dated `2025-07-01`, `2025-01-15`, `2025-04-10` in that order
- **THEN** the rendered line's data points MUST go left-to-right as `2025-01-15 → 2025-04-10 → 2025-07-01`
