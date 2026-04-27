## ADDED Requirements

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
