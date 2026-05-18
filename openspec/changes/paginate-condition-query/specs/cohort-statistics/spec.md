## MODIFIED Requirements

### Requirement: ConditionResults SHALL expose a cohort-statistics tab

`frontend/src/components/ConditionResults.tsx` MUST wrap its chip-row + result-table content in a shadcn `Tabs`. The first tab, labelled `名單`, MUST host the condition chips, the matched-count summary, the results table, the "patient row click → detail view" flow, and the results pager. A second tab, labelled `族群統計`, MUST render `CohortStatsPanel`.

Because condition-query results are paginated, `CohortStatsPanel` receives only the **current results page** of matched patients as input, not the full matched cohort (an interim limitation — a cohort-wide statistics path is deferred to a future change). The `族群統計` tab MUST therefore display a visible `僅供參考` notice stating that the statistics cover only the current results page.

#### Scenario: Default tab shows the condition list
- **WHEN** a user runs a condition query
- **THEN** the `名單` tab MUST be selected by default
- **AND** it MUST render the condition chips, the matched-count summary, and the results table

#### Scenario: Switching to 族群統計
- **WHEN** the user clicks the `族群統計` tab
- **THEN** `CohortStatsPanel` MUST render
- **AND** its input patient list MUST be the current results page — the same list rendered by the `名單` tab's table

#### Scenario: Cohort statistics tab shows a current-page notice
- **WHEN** the user views the `族群統計` tab
- **THEN** a visible notice MUST state that the statistics cover only the current results page and are for reference only

### Requirement: 名單 tab SHALL host the cohort export entry point

The 名單 tab inside `frontend/src/components/ConditionResults.tsx` MUST host an export entry point implemented as a "匯出比較報告" button rendered on the same row as the condition summary chips and the matched-patient count. The button MUST be enabled when the condition query has at least one match (`total > 0`) and disabled otherwise.

Because condition-query results are paginated, the exported report covers only the **current results page** of matched patients, not the full matched cohort (an interim limitation — a cohort-wide export path is deferred to a future change). A visible `僅供參考` notice MUST indicate that the export covers only the current results page.

The 族群統計 tab MUST NOT render this export button. The detailed dialog and writer behaviour are governed by the `cohort-export` capability; this requirement only governs that the entry point is mounted on the 名單 tab and gated on match count.

#### Scenario: Export entry button is mounted in 名單 tab content
- **WHEN** a user runs a condition query that matches one or more patients and the 名單 tab is active
- **THEN** the 名單 tab content MUST contain a "匯出比較報告" button
- **AND** the button MUST be enabled

#### Scenario: Export entry button is disabled when no patient matches
- **WHEN** a user runs a condition query whose `total` is 0
- **THEN** the "匯出比較報告" button MUST render but be disabled

#### Scenario: Export entry button is not mounted in 族群統計 tab
- **WHEN** the user switches to the 族群統計 tab
- **THEN** the 族群統計 tab content MUST NOT contain a "匯出比較報告" button

#### Scenario: Export entry shows a current-page notice
- **WHEN** a user runs a condition query that matches one or more patients
- **THEN** a visible notice MUST indicate the export covers only the current results page

#### Scenario: Row action still navigates to detail
- **WHEN** a user clicks a row's "查看" button in the 名單 tab
- **THEN** the single-patient detail view MUST open, as before this change
