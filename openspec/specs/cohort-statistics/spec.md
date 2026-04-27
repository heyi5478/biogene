# cohort-statistics Specification

## Purpose
TBD - created by archiving change add-export-and-stats. Update Purpose after archive.
## Requirements
### Requirement: ConditionResults SHALL expose a cohort-statistics tab

`frontend/src/components/ConditionResults.tsx` MUST wrap its current chip-row + result-table content in a shadcn `Tabs`. The first tab, labelled `名單`, MUST preserve 100% of the pre-change behavior (same chips, same table, same "patient row click → detail view" flow). A second tab, labelled `族群統計`, MUST render `CohortStatsPanel` with the matched patient list as input.

#### Scenario: Default tab preserves existing behavior
- **WHEN** a user runs a condition query
- **THEN** the `名單` tab MUST be selected by default
- **AND** the rendered DOM inside it MUST be equivalent to the pre-change `ConditionResults` output (chips, count, table, row click)

#### Scenario: Switching to 族群統計
- **WHEN** the user clicks the `族群統計` tab
- **THEN** `CohortStatsPanel` MUST render
- **AND** the underlying matched-patient list MUST be the same reference used by the `名單` tab

### Requirement: CohortStatsPanel SHALL produce a sex × age-bucket cross-tabulation

`CohortStatsPanel` MUST present:
1. A `ModuleFieldPicker` (module + numeric field) with the same filtering rules as `StatsDialog`
2. Optional date-range inputs (disabled for dateless modules, with the same helper text as patient-statistics)
3. Optional value-range inputs
4. A cohort size indicator (`共 N 位病人`)
5. A 5×3 results table with rows `0-17 | 18-39 | 40-59 | 60+ | 全部年齡` and columns `男 | 女 | 全部性別`
6. A footnote `年齡以該筆紀錄的日期減去病人生日為準；若該模組無紀錄日期則以今日為準`

Each cell MUST display `formatCell(summarize(values))`, where `values` is the multiset of numeric field values from cohort records falling into that `(age-bucket, sex)` combination after filters.

#### Scenario: Marginal column is truly inclusive
- **WHEN** a cohort has males in `0-17` and `18-39` only
- **THEN** the `全部性別` column for `0-17` MUST equal the `男` column for `0-17` (since no females match)
- **AND** the `全部年齡` row's `全部性別` cell MUST aggregate every numeric data point across the cohort

#### Scenario: Each record contributes once per applicable cell
- **WHEN** a single record has value `v`, sex `男`, and falls in age bucket `18-39`
- **THEN** `v` MUST appear exactly once in the multiset for `(18-39, 男)`
- **AND** exactly once in `(18-39, 全部性別)`
- **AND** exactly once in `(全部年齡, 男)`
- **AND** exactly once in `(全部年齡, 全部性別)`

#### Scenario: Empty cells render em-dash
- **WHEN** no cohort records land in `(60+, 女)` after filters
- **THEN** that cell MUST render as `—`

#### Scenario: Enzyme-deficiency canonical path
- **WHEN** the condition query is `enzyme.result = Deficient` and 族群統計 is opened
- **AND** the user picks module `enzyme`, field `MPS1`, no additional filters
- **THEN** the bottom-right `(全部年齡, 全部性別)` cell MUST show `mean ± sd (n=k)` where `k` equals the count of finite `MPS1` values across all matched patients' enzyme records

### Requirement: Cohort age bucketing SHALL use record date when available

For each cohort record, `CohortStatsPanel` MUST compute `asOf = getRecordDate(moduleId, record) ?? new Date()` and derive `age = ageInYears(patient.birthday, asOf)`. A patient whose `birthday` fails to parse MUST be silently omitted from the grid (no throw, no error banner).

#### Scenario: Record date drives age when present
- **WHEN** a patient born `2000-01-01` has an `opd` record dated `2025-01-01`
- **AND** the cohort view is showing OPD-based statistics
- **THEN** the record MUST be bucketed as if the patient is 25 years old (bucket `18-39`)

#### Scenario: Fallback to today for dateless modules
- **WHEN** the cohort view uses module `enzyme` (no date field) and the current date is 2026-04-23
- **AND** a patient was born `2000-01-01`
- **THEN** the record MUST be bucketed using age 26 (bucket `18-39`)

#### Scenario: Unparseable birthday is silently skipped
- **WHEN** a cohort patient has `birthday === ''`
- **THEN** that patient's records MUST NOT contribute to any cell
- **AND** the panel MUST NOT throw or show an error banner

### Requirement: Cohort statistics SHALL NOT render any chart in this change

This change MUST NOT introduce a chart (bar, scatter, box, or otherwise) inside `CohortStatsPanel`. Only the 5×3 tabular view and accompanying controls are in scope.

#### Scenario: No chart elements in the panel
- **WHEN** `族群統計` tab is active
- **THEN** the rendered DOM MUST NOT contain any `recharts` chart component
- **AND** MUST NOT import from `recharts` inside `CohortStatsPanel.tsx`

### Requirement: 名單 tab SHALL host the cohort export entry point

The 名單 tab inside `frontend/src/components/ConditionResults.tsx` MUST host an export entry point that turns the currently matched cohort into a downloadable comparison report. The entry point MUST be implemented as a "匯出比較報告" button rendered on the same row as the condition summary chips and the matched-patient count. The button MUST be enabled when `matchedPatients.length > 0` and disabled otherwise. The button MUST NOT alter the existing 名單 tab behaviour (chips, count, table contents, row "查看" action remain unchanged).

The 族群統計 tab MUST NOT render this export button.

The detailed dialog and writer behaviour are governed by the `cohort-export` capability; this requirement only governs that the entry point is mounted on the 名單 tab and is gated on cohort size.

#### Scenario: Export entry button is mounted in 名單 tab content

- **WHEN** a user runs a condition query that matches one or more patients and the 名單 tab is active
- **THEN** the 名單 tab content MUST contain a "匯出比較報告" button
- **AND** the button MUST be enabled

#### Scenario: Export entry button is disabled when cohort is empty

- **WHEN** a user runs a condition query that matches zero patients
- **THEN** the "匯出比較報告" button MUST render but be disabled

#### Scenario: Export entry button is not mounted in 族群統計 tab

- **WHEN** the user switches to the 族群統計 tab
- **THEN** the 族群統計 tab content MUST NOT contain a "匯出比較報告" button

#### Scenario: Existing 名單 behaviour is preserved

- **WHEN** the change ships and a user runs a condition query
- **THEN** the chip row, matched-count text, results table columns, and per-row "查看" button MUST behave exactly as before this change
- **AND** clicking "查看" MUST still navigate to the single-patient detail view

