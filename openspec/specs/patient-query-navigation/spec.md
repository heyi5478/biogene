# patient-query-navigation Specification

## Purpose
TBD - created by archiving change add-patient-list-back-button. Update Purpose after archive.
## Requirements
### Requirement: Patient-mode detail view SHALL offer a back control when reached from a multi-result list

On the Index page in `patient` query mode, when the user has viewed a detail by selecting a patient from a `PatientList` containing more than one result, the detail view MUST render a visible "返回病人名單" back control above the patient summary. Activating the control MUST return the user to the `PatientList` with the prior search query, submitted query, selected modules, and active tab preserved. The control MUST NOT render when the query returned exactly one patient (auto-selection case) or zero patients, since no list exists to return to.

The control MUST use the same visual treatment as the existing condition-mode back button (ghost Button variant, small size, `ArrowLeft` leading icon), differing only in label copy, so the two modes feel uniform.

#### Scenario: Multi-result detail shows back control
- **WHEN** the user runs a patient search that returns more than one patient
- **AND** the user picks one entry from the rendered `PatientList`
- **THEN** the detail view MUST render a back control labelled "返回病人名單" above the patient summary

#### Scenario: Back control returns to the preserved list
- **WHEN** the user is on a patient-mode detail view reached from a multi-result list
- **AND** the user activates the back control
- **THEN** the `PatientList` MUST be rendered again
- **AND** `searchQuery`, `submittedQuery`, `selectedModules`, and `activeTab` MUST be unchanged from before the detail was opened

#### Scenario: Single-result auto-selection does not show the back control
- **WHEN** a patient search returns exactly one patient and the detail view is auto-rendered for that patient
- **THEN** the back control MUST NOT be rendered

#### Scenario: Condition-mode back control remains unchanged
- **WHEN** the user is on a condition-mode detail view
- **THEN** the existing "返回條件查詢結果" back control MUST continue to render and function as before this change
