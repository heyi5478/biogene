## MODIFIED Requirements

### Requirement: Index page SHALL source patient data from the backend gateway via useQuery

The component `frontend/src/pages/Index.tsx` MUST obtain its patient list from the `usePatients(submittedQuery)` hook (defined in `frontend/src/hooks/queries/usePatients.ts`) and condition results from `useConditionPatients(req, conditionSubmitted)`. It MUST NOT import any runtime array from `frontend/src/data/mockData.ts` or from `backend/mock-data/**`. It MUST NOT perform client-side `.filter()` over the returned list to apply text search — the `q` parameter passed to `usePatients` is the search.

#### Scenario: Text search is server-side
- **WHEN** the user types `陳` in the search input and clicks the search button
- **THEN** Index MUST set `submittedQuery="陳"` so `usePatients("陳")` issues `GET /patients?q=陳`
- **AND** the rendered list MUST be the hook's resolved data without any subsequent `.filter()` over name/chartno/externalChartno/nbsId

#### Scenario: Empty submittedQuery returns nothing
- **WHEN** `submittedQuery` is the empty string (initial state, before any search)
- **THEN** Index MUST render the "開始查詢" empty state and MUST NOT issue a list query that materially uses `q`
- **AND** the existing UX of "no results until user searches" MUST be preserved (an early-return on empty `submittedQuery` is acceptable)

#### Scenario: Condition results come from the server
- **WHEN** the user submits a non-empty condition list
- **THEN** the matched patients MUST be the resolved data of `useConditionPatients(req, true)`
- **AND** Index MUST NOT call any local `evaluateConditions(...)` function

### Requirement: Condition-based filtering SHALL produce results identical to pre-change

For every pre-existing condition template (e.g. "Biomarker 異常" with `dbsLysoGb3 > 5`) and for every text search input, the post-change matched patient set MUST equal the pre-change matched patient set when the backend serves the same fixture. The backend evaluator (`backend/shared/condition.py`) MUST mirror the operator semantics of the previous `evaluateConditions` function in `frontend/src/components/ConditionResults.tsx` for all eleven operators (`contains, eq, neq, gt, gte, lt, lte, between, before, after, has_data, no_data`).

#### Scenario: Biomarker condition parity
- **WHEN** a user runs the "Biomarker 異常" template with `dbsLysoGb3 > 5` after the change
- **AND** the backend has not modified the seeded data
- **THEN** the matched patient set MUST be identical to the pre-change result

#### Scenario: Text search parity
- **WHEN** a user searches "A1234567"
- **THEN** the patient "陳志明" MUST appear in the results (same as pre-change)

#### Scenario: Operator parity for has_data
- **WHEN** any condition uses the `has_data` operator on a field
- **THEN** the patient MUST match if and only if at least one of that patient's records in the target module has a non-null, non-empty value for the field

### Requirement: Patient type SHALL remain the shared contract between backend and frontend

The `Patient` TypeScript type (in `frontend/src/types/patient.ts`) MUST remain structurally equivalent to the gateway's detail-endpoint response (same camelCase field names, same nested module array names). The `PatientListItem` TypeScript interface MUST remain structurally equivalent to the gateway's list-endpoint element (base fields + `dnabankCount`, `outbankCount`, `lastVisitDate`, optional `conditionHits`). Any future schema drift detected at runtime MUST be treated as a backend bug, not a frontend coercion target.

#### Scenario: Field casing stays camelCase
- **WHEN** the gateway returns a field named `dbsLysoGb3` on a detail response
- **THEN** the frontend MUST consume it as `patient.biomarker[0].dbsLysoGb3` without renaming
- **AND** no adapter layer MUST translate between snake_case and camelCase in the frontend

#### Scenario: PatientListItem has the summary fields
- **WHEN** the gateway returns a list element
- **THEN** TypeScript MUST recognise `dnabankCount`, `outbankCount`, and `lastVisitDate` on the element

## ADDED Requirements

### Requirement: Selection flow SHALL identify a patient by id, not by passing the full object

`frontend/src/components/PatientList.tsx` and `frontend/src/components/ConditionResults.tsx` MUST expose `onSelect` (or `onSelectPatient`) callbacks whose argument is `patientId: string`, not the whole `PatientListItem` or `Patient` object. `frontend/src/pages/Index.tsx` MUST hold the selection in state as a `string | null` and MUST use `usePatient(selectedPatientId)` to obtain the full bundle for `PatientSummary` and `ResultModules`.

#### Scenario: PatientList click selects an id
- **WHEN** the user clicks a row in `PatientList`
- **THEN** `onSelect(p.patientId)` MUST be invoked
- **AND** `Index` MUST set `selectedPatientId` to that id, triggering `usePatient(id)`

#### Scenario: Single-result auto-detail
- **WHEN** the search returns exactly one `PatientListItem`
- **THEN** Index MUST set `selectedPatientId` to that single item's `patientId` and render the detail view as soon as `usePatient` resolves
- **AND** Index MUST NOT pass the list item directly to `PatientSummary`

#### Scenario: Detail loading shows a placeholder
- **WHEN** `selectedPatientId` is set and `usePatient` is pending
- **THEN** Index MUST render a loading indicator in place of `PatientSummary` and `ResultModules`

## REMOVED Requirements

### Requirement: ConditionResults SHALL receive patients as a prop from Index

**Reason**: Condition matching is now performed by the backend (`POST /patients/condition-query`). `ConditionResults` no longer needs the full patient list because it never evaluates conditions itself; it renders a server-supplied `PatientListItem[]` (with per-row `conditionHits`).

**Migration**: Replace the `patients: Patient[]` prop with `matchedPatients: PatientListItem[]` (already in the existing `MatchedPatient` interface — this change just changes the element type from `Patient` to `PatientListItem`). Remove the local call to `evaluateConditions(patients, conditions, logic)` in `Index.tsx` and read `useConditionPatients(req, enabled).data ?? []` instead. The `evaluateConditions`, `getModuleData`, `evalCondition`, and `getHitSummary` functions MUST be deleted from `frontend/src/components/ConditionResults.tsx`; their behaviour is preserved by `backend/shared/condition.py` (covered by "Condition-based filtering SHALL produce results identical to pre-change").
