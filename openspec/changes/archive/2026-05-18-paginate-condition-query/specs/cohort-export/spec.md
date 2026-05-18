## MODIFIED Requirements

### Requirement: ConditionResults SHALL expose a cohort-export entry point on the 名單 tab

`frontend/src/components/ConditionResults.tsx` MUST render a "匯出比較報告" button inside the 名單 tab, on the same row as the condition summary chips and the matched-patient count. The button MUST be enabled when the condition query has at least one match (`total > 0`) and disabled otherwise. Clicking it MUST open a `CohortExportDialog`.

Because condition-query results are paginated, the dialog is populated with the **current results page** of matched patients, not the full matched cohort (an interim limitation — a cohort-wide export path is deferred to a future change). A visible `僅供參考` notice MUST indicate that the export covers only the current results page. The button MUST NOT appear on the 族群統計 tab.

#### Scenario: Button renders on 名單 tab and is enabled when there are matches
- **WHEN** the user runs a condition query that matches at least one patient
- **AND** the 名單 tab is active
- **THEN** a "匯出比較報告" button MUST be visible on the chip row
- **AND** the button MUST be enabled
- **AND** the existing condition chips and matched count MUST still render

#### Scenario: Button is disabled when no patients match
- **WHEN** the user runs a condition query whose `total` is 0
- **THEN** the "匯出比較報告" button MUST still render
- **AND** MUST be disabled
- **AND** clicking it MUST NOT open the dialog

#### Scenario: Button is absent on 族群統計 tab
- **WHEN** the user switches to the 族群統計 tab
- **THEN** the "匯出比較報告" button MUST NOT be rendered inside that tab's content

#### Scenario: Clicking the button opens CohortExportDialog with the current page
- **WHEN** the user clicks the enabled "匯出比較報告" button
- **THEN** a `CohortExportDialog` MUST open
- **AND** the dialog's `patients` prop MUST be the array of `Patient` references on the current results page (in the same order)

#### Scenario: Export entry shows a current-page notice
- **WHEN** the user runs a condition query that matches one or more patients
- **THEN** a visible notice MUST indicate the export covers only the current results page
