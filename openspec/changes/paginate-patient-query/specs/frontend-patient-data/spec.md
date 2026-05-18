## ADDED Requirements

### Requirement: Index page SHALL render a pagination control for multi-page result sets

In `patient` query mode, when a search resolves to more patients than fit on one page (`total` exceeds the page size), `frontend/src/pages/Index.tsx` MUST render a pagination control beneath the `PatientList`. The control MUST offer previous/next navigation and numbered page links, collapsing long runs of pages with an ellipsis. Selecting a page MUST update the requested page so `usePatients` fetches it. The result-count summary MUST always reflect `total` (the full hit count), not the number of rows on the current page. Submitting a new search MUST reset the view to the first page.

#### Scenario: Pager appears for multi-page results
- **WHEN** a search resolves to a `total` greater than the page size
- **THEN** Index MUST render a pagination control with previous/next controls and numbered page links beneath the patient list

#### Scenario: Pager is absent for a single page
- **WHEN** a search resolves to a `total` less than or equal to the page size
- **THEN** Index MUST NOT render the pagination control

#### Scenario: Selecting a page fetches it
- **WHEN** the user activates a numbered page link or the next control
- **THEN** `usePatients` MUST be invoked for the selected page
- **AND** the rendered list MUST update to that page's `items`

#### Scenario: Result summary shows the full hit count
- **WHEN** a search resolves to `total` 320 with a page size of 50
- **THEN** the result-count summary MUST report 320 patients, not 50

#### Scenario: New search resets to the first page
- **WHEN** the user is viewing page 4 of one search and submits a different search
- **THEN** Index MUST request page 1 of the new search

## MODIFIED Requirements

### Requirement: Index page SHALL source patient data from the backend gateway via useQuery

The component `frontend/src/pages/Index.tsx` MUST obtain its patient list from the `usePatients(submittedQuery, page)` hook (defined in `frontend/src/hooks/queries/usePatients.ts`) and condition results from `useConditionPatients(req, conditionSubmitted)`. The patient list it renders MUST be the `items` array of the hook's resolved `PatientListPage`. It MUST NOT import any runtime array from `frontend/src/data/mockData.ts` or from `backend/mock-data/**`. It MUST NOT perform client-side `.filter()` over the returned list to apply text search — the `q` parameter passed to `usePatients` is the search.

#### Scenario: Text search is server-side
- **WHEN** the user types `陳` in the search input and clicks the search button
- **THEN** Index MUST set `submittedQuery="陳"` so `usePatients("陳", page)` issues `GET /patients?q=陳` with `limit`/`offset`
- **AND** the rendered list MUST be the `items` of the hook's resolved page without any subsequent `.filter()` over name/chartno/externalChartno/nbsId

#### Scenario: Empty submittedQuery issues no request
- **WHEN** `submittedQuery` is the empty string (initial state, before any search)
- **THEN** Index MUST render the "開始查詢" empty state
- **AND** `usePatients` MUST NOT issue any network request (its `enabled` flag is false while the query is empty)

#### Scenario: Condition results come from the server
- **WHEN** the user submits a non-empty condition list
- **THEN** the matched patients MUST be the resolved data of `useConditionPatients(req, true)`
- **AND** Index MUST NOT call any local `evaluateConditions(...)` function

### Requirement: Index page SHALL render distinct loading, error, and empty states

While `usePatients()` is pending, Index MUST render a skeleton placeholder (using `frontend/src/components/ui/skeleton.tsx`) consistent with the eventual list height. On error, Index MUST render an alert (using `frontend/src/components/ui/alert.tsx`) showing the error message and a button that calls `refetch()`. When the resolved page contains zero matching patients (`total` is 0), Index MUST render the existing "no patients found" empty state.

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

#### Scenario: Empty result set
- **WHEN** the search resolves to a page whose `total` is 0
- **THEN** the page MUST render the existing empty state, not the skeleton and not the error alert

### Requirement: Selection flow SHALL identify a patient by id, not by passing the full object

`frontend/src/components/PatientList.tsx` and `frontend/src/components/ConditionResults.tsx` MUST expose `onSelect` (or `onSelectPatient`) callbacks whose argument is `patientId: string`, not the whole `PatientListItem` or `Patient` object. `frontend/src/pages/Index.tsx` MUST hold the selection in state as a `string | null` and MUST use `usePatient(selectedPatientId)` to obtain the full bundle for `PatientSummary` and `ResultModules`.

#### Scenario: PatientList click selects an id
- **WHEN** the user clicks a row in `PatientList`
- **THEN** `onSelect(p.patientId)` MUST be invoked
- **AND** `Index` MUST set `selectedPatientId` to that id, triggering `usePatient(id)`

#### Scenario: Single-result auto-detail
- **WHEN** a patient search resolves to a page whose `total` is exactly 1
- **THEN** Index MUST set `selectedPatientId` to that single item's `patientId` and render the detail view as soon as `usePatient` resolves
- **AND** Index MUST NOT pass the list item directly to `PatientSummary`

#### Scenario: Detail loading shows a placeholder
- **WHEN** `selectedPatientId` is set and `usePatient` is pending
- **THEN** Index MUST render a loading indicator in place of `PatientSummary` and `ResultModules`
