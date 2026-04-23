# frontend-patient-data Specification

## Purpose
TBD - created by archiving change wire-index-page-to-api. Update Purpose after archive.
## Requirements

### Requirement: Index page SHALL source patient data from the backend gateway via useQuery

The component `frontend/src/pages/Index.tsx` MUST obtain its patient list from the `usePatients()` hook (defined in `frontend/src/hooks/queries/usePatients.ts`). It MUST NOT import any runtime array from `frontend/src/data/mockData.ts` or from `backend/mock-data/**`.

#### Scenario: Happy path render
- **WHEN** the backend gateway is reachable and returns a non-empty `Patient[]`
- **THEN** the Index page MUST render the same list UI as before, using the hook's resolved `data`
- **AND** the existing text search (by name and chartno) MUST still filter the displayed list

#### Scenario: No static import of mockPatients remains
- **WHEN** the codebase is grep'd for `from ['"]@/data/mockData['"]` importing a runtime value
- **THEN** no production source file under `frontend/src/{pages,components}/` MUST match
- **AND** `frontend/src/data/mockData.ts` MUST NOT export a value named `mockPatients`

### Requirement: Index page SHALL render distinct loading, error, and empty states

While `usePatients()` is pending, Index MUST render a skeleton placeholder (using `frontend/src/components/ui/skeleton.tsx`) consistent with the eventual list height. On error, Index MUST render an alert (using `frontend/src/components/ui/alert.tsx`) showing the error message and a button that calls `refetch()`. When data is an empty array, Index MUST render the existing "no patients found" empty state.

#### Scenario: Loading state
- **WHEN** the page is first mounted and the API request has not yet resolved
- **THEN** the DOM MUST show skeleton placeholders
- **AND** MUST NOT show the "no patients found" empty state

#### Scenario: Error state with retry
- **WHEN** the API request rejects (backend down or 5xx)
- **THEN** the page MUST render an alert containing the error message
- **AND** MUST render a "重試" (Retry) button
- **WHEN** the user clicks Retry
- **THEN** the hook's `refetch()` MUST be called and the state MUST transition back to loading

#### Scenario: Empty list
- **WHEN** the API responds with `[]`
- **THEN** the page MUST render the existing empty state, not the skeleton and not the error alert

### Requirement: ConditionResults SHALL receive patients as a prop from Index

`frontend/src/components/ConditionResults.tsx` MUST continue to accept a `Patient[]` via props (the existing interface). It MUST NOT call `usePatients()` itself, to avoid duplicating query subscriptions and to keep the component pure/testable.

#### Scenario: Index passes hook data to ConditionResults
- **WHEN** Index renders ConditionResults
- **THEN** the `patients` prop MUST be the hook's resolved data (or `[]` while loading)
- **AND** `evaluateConditions` inside ConditionResults MUST be invoked with that prop unchanged in signature

### Requirement: Condition-based filtering SHALL produce results identical to pre-change

For every pre-existing condition template (e.g. "Biomarker 異常" with `dbsLysoGb3 > 5`), the post-change hit set MUST equal the pre-change hit set when the backend is serving the same mock-data fixture.

#### Scenario: Biomarker condition parity
- **WHEN** a user runs the "Biomarker 異常" template with `dbsLysoGb3 > 5` after the change
- **AND** the backend has not modified the mock data
- **THEN** the matched patient set MUST be identical to the pre-change result

#### Scenario: Text search parity
- **WHEN** a user searches "A1234567"
- **THEN** the patient "陳志明" MUST appear in the results (same as pre-change)

### Requirement: Patient type SHALL remain the shared contract between backend and frontend

The `Patient` TypeScript type (in `frontend/src/types/patient.ts`) MUST remain structurally equivalent to the gateway's `PatientBundle` Pydantic model (same camelCase field names, same nested module array names). Any future schema drift detected at runtime MUST be treated as a backend bug, not a frontend coercion target.

#### Scenario: Field casing stays camelCase
- **WHEN** the gateway returns a field named `dbsLysoGb3`
- **THEN** the frontend MUST consume it as `patient.biomarker[0].dbsLysoGb3` without renaming
- **AND** no adapter layer MUST translate between snake_case and camelCase in the frontend
