## MODIFIED Requirements

### Requirement: Index page SHALL source patient data from the backend gateway via useQuery

The component `frontend/src/pages/Index.tsx` MUST obtain its patient list from the `usePatients(submittedQuery, page)` hook (defined in `frontend/src/hooks/queries/usePatients.ts`) and condition results from the `useConditionPatients(req, conditionPage, conditionSubmitted)` hook. Both the patient list and the condition-results list it renders MUST be the `items` array of the respective hook's resolved `PatientListPage`. It MUST NOT import any runtime array from `frontend/src/data/mockData.ts` or from `backend/mock-data/**`. It MUST NOT perform client-side `.filter()` over the returned list to apply text search — the `q` parameter passed to `usePatients` is the search.

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
- **THEN** the matched patients MUST be the `items` of the resolved `PatientListPage` from `useConditionPatients(req, conditionPage, true)`
- **AND** Index MUST NOT call any local `evaluateConditions(...)` function

### Requirement: Index page SHALL render a pagination control for multi-page result sets

In `patient` query mode, when a search resolves to more patients than fit on one page (`total` exceeds the page size), `frontend/src/pages/Index.tsx` MUST render a pagination control beneath the `PatientList`. In `condition` query mode, when a condition query resolves to more matched patients than fit on one page, `frontend/src/components/ConditionResults.tsx` MUST render the same pagination control beneath its results table. In both modes the control MUST offer previous/next navigation and numbered page links, collapsing long runs of pages with an ellipsis. Selecting a page MUST update the requested page so the corresponding hook (`usePatients` or `useConditionPatients`) fetches it. The result-count summary MUST always reflect `total` (the full hit count), not the number of rows on the current page. Submitting a new search or a new condition query MUST reset the view to the first page; editing the condition set MUST also reset the condition view to the first page.

#### Scenario: Pager appears for multi-page patient results
- **WHEN** a patient search resolves to a `total` greater than the page size
- **THEN** Index MUST render a pagination control with previous/next controls and numbered page links beneath the patient list

#### Scenario: Pager appears for multi-page condition results
- **WHEN** a condition query resolves to a `total` greater than the page size
- **THEN** `ConditionResults` MUST render a pagination control beneath its results table

#### Scenario: Pager is absent for a single page
- **WHEN** a search or condition query resolves to a `total` less than or equal to the page size
- **THEN** the corresponding view MUST NOT render the pagination control

#### Scenario: Selecting a page fetches it
- **WHEN** the user activates a numbered page link or the next control
- **THEN** the corresponding hook (`usePatients` or `useConditionPatients`) MUST be invoked for the selected page
- **AND** the rendered list MUST update to that page's `items`

#### Scenario: Result summary shows the full hit count
- **WHEN** a search or condition query resolves to `total` 320 with a page size of 50
- **THEN** the result-count summary MUST report 320 patients, not 50

#### Scenario: New search or condition query resets to the first page
- **WHEN** the user is viewing page 4 of one result set and submits a different search or condition query
- **THEN** the view MUST request page 1 of the new result set

#### Scenario: Editing a condition resets the condition view to the first page
- **WHEN** the user is viewing page 4 of a condition query and edits the condition set
- **THEN** the condition view MUST request page 1
