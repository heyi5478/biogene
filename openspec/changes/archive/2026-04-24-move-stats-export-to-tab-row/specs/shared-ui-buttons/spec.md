## MODIFIED Requirements

### Requirement: Designated action buttons SHALL use the matching semantic variant

The following user-facing buttons SHALL render with the indicated semantic variant so their color communicates the nature of the action:

- The「清除全部條件」button in `frontend/src/components/FilterPanel.tsx` (sidebar footer) SHALL use `variant="destructive"`.
- The「清除全部條件」button in `frontend/src/components/ConditionBuilder.tsx` (condition-builder footer) SHALL use `variant="destructive"`.
- The「統計」button in `frontend/src/components/PatientActions.tsx` (rendered on the tab row of the patient detail view) SHALL use `variant="success"`.
- The「匯出」button in `frontend/src/components/PatientActions.tsx` (rendered on the tab row, adjacent to 統計) SHALL use `variant="info"`.

The jump-link buttons in `frontend/src/components/PatientSummary.tsx` (門診 / MS/MS / AA / Enzyme / GAG / DNA / 外送) SHALL continue to use `variant="outline"` and MUST NOT be recolored by this change.

#### Scenario: Clear-all button uses destructive

- **WHEN** the FilterPanel renders its footer
- **THEN** the「清除全部條件」button MUST be rendered via `<Button variant="destructive">`

#### Scenario: Condition-builder clear-all button uses destructive

- **WHEN** the ConditionBuilder renders its footer
- **THEN** the「清除全部條件」button MUST be rendered via `<Button variant="destructive">`

#### Scenario: Stats button uses success

- **WHEN** `PatientActions` renders for a selected patient
- **THEN** the「統計」button MUST be rendered via `<Button variant="success">`

#### Scenario: Export button uses info

- **WHEN** `PatientActions` renders for a selected patient
- **THEN** the「匯出」button MUST be rendered via `<Button variant="info">`

#### Scenario: Jump links remain outline

- **WHEN** `PatientSummary` renders jump-link buttons for modules with `count > 0`
- **THEN** every such jump-link button MUST be rendered via `<Button variant="outline">`
