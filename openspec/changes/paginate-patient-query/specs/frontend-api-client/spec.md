## ADDED Requirements

### Requirement: Frontend SHALL define a paginated patient-list envelope type

The module `frontend/src/types/patient.ts` MUST define a generic page envelope type `Page<T>` with the fields `items: T[]`, `total: number`, `limit: number`, `offset: number`, and a `PatientListPage` alias equal to `Page<PatientListItem>` that mirrors the gateway's paginated `GET /patients` response. The existing `frontend/src/types/medical.ts` MUST re-export both `Page` and `PatientListPage` so existing `@/types/medical` imports keep working.

#### Scenario: PatientListPage mirrors the gateway envelope
- **WHEN** a developer types the resolved value of a paginated `GET /patients` call
- **THEN** `PatientListPage` MUST expose `items: PatientListItem[]`, `total: number`, `limit: number`, and `offset: number`

#### Scenario: Page type is re-exported from medical.ts
- **WHEN** a module imports `Page` or `PatientListPage` from `@/types/medical`
- **THEN** the import MUST resolve to the definitions declared in `@/types/patient`

## MODIFIED Requirements

### Requirement: Frontend SHALL provide service functions that wrap API endpoints

The directory `frontend/src/services/` MUST host pure, React-agnostic service functions. The module `patients.ts` MUST export at minimum:
- `PATIENT_PAGE_SIZE` — the patient-list page size constant (`50`)
- `fetchPatients(q: string, page: number): Promise<PatientListPage>` — calls `apiGet<PatientListPage>('/patients?...')` with `limit` set to `PATIENT_PAGE_SIZE` and `offset` set to `(page - 1) * PATIENT_PAGE_SIZE`; when `q` is non-empty the request MUST also include a URL-encoded `q` parameter; when `q` is empty the request MUST omit the `q` parameter entirely
- `fetchPatient(patientId: string): Promise<Patient>` — calls `apiGet<Patient>('/patients/{patientId}')`
- `searchByConditions(req: ConditionRequest): Promise<PatientListItem[]>` — calls `apiPost<PatientListItem[]>('/patients/condition-query', req)`

`ConditionRequest` MUST be `{conditions: ConditionRow[], logic: 'AND' | 'OR'}`. Service functions MUST NOT import from `react` or `@tanstack/react-query`.

#### Scenario: fetchPatients requests a page
- **WHEN** a test calls `fetchPatients('', 1)` against a mocked `/patients` endpoint
- **THEN** the request URL MUST include `limit=50` and `offset=0`
- **AND** MUST NOT include a `q` parameter
- **AND** the return value MUST be the parsed `PatientListPage` envelope

#### Scenario: fetchPatients with q and a later page
- **WHEN** a test calls `fetchPatients('陳', 3)`
- **THEN** the request URL MUST contain `q=` followed by the URL-encoded value of `陳`
- **AND** MUST include `offset=100` (page 3 at page size 50)

#### Scenario: searchByConditions issues POST
- **WHEN** a test calls `searchByConditions({conditions: [...], logic: 'AND'})`
- **THEN** the request MUST be POST `/patients/condition-query` with the body equal to the input

### Requirement: Frontend SHALL provide React Query hooks for patient resources

The directory `frontend/src/hooks/queries/` MUST provide:
- `usePatients(q: string, page: number)` — wraps `useQuery` with `queryKey: queryKeys.patients.list(q, page)`, `queryFn: () => fetchPatients(q, page)`, `enabled: q !== ''` (no request is issued until a non-empty query is submitted), and `placeholderData` set to React Query's `keepPreviousData` so the current page stays visible while the next page loads
- `usePatient(patientId: string | undefined)` — wraps `useQuery` with `queryKey: queryKeys.patients.detail(patientId)`, `queryFn: () => fetchPatient(patientId!)`, and `enabled: Boolean(patientId)`
- `useConditionPatients(req: ConditionRequest, enabled: boolean)` — wraps `useQuery` with `queryKey: queryKeys.patients.condition(req)`, `queryFn: () => searchByConditions(req)`, and the supplied `enabled` flag (callers MUST pass `false` until the user submits a non-empty condition list)

`usePatients` and `useConditionPatients` MUST set `staleTime: 5 * 60 * 1000` and `gcTime: 30 * 60 * 1000` so navigation across the SPA does not re-issue requests within the stale window.

#### Scenario: usePatients keys per q and page
- **WHEN** a component renders `usePatients('陳', 1)` then `usePatients('陳', 2)` in sequence
- **THEN** React Query MUST track two distinct queries with different keys
- **AND** each query's request URL MUST reflect its `offset`

#### Scenario: usePatients disabled before a query is submitted
- **WHEN** a component renders `usePatients('', 1)` with an empty query
- **THEN** no network request MUST be issued
- **AND** the query status MUST be `pending` with `fetchStatus: 'idle'`

#### Scenario: useConditionPatients gated by enabled
- **WHEN** a component renders `useConditionPatients({conditions: [], logic: 'AND'}, false)`
- **THEN** no network request MUST be issued
- **AND** the query status MUST be `pending` with `fetchStatus: 'idle'`

#### Scenario: usePatient disabled when id is undefined
- **WHEN** a component renders `usePatient(undefined)`
- **THEN** no network request MUST be issued
- **AND** the query status MUST be `pending` with `fetchStatus: 'idle'`

### Requirement: Frontend SHALL define query key conventions in a central module

The module `frontend/src/hooks/queries/keys.ts` MUST export a `queryKeys` helper organising keys as:
- `queryKeys.patients.list(q?: string, page?: number)` → `['patients', 'list', q ?? '', page ?? 1]`
- `queryKeys.patients.condition(req: ConditionRequest)` → `['patients', 'condition', req]`
- `queryKeys.patients.detail(id: string | undefined)` → `['patients', id]`
- `queryKeys.patients.subResource(id: string, name: string)` → `['patients', id, name]`

Hooks and any future invalidation calls MUST use this helper rather than inline literal arrays. The `list` key MUST include the page number so each page caches independently.

#### Scenario: Hook uses central key helper
- **WHEN** a developer opens `usePatients.ts`
- **THEN** the `queryKey` argument MUST be `queryKeys.patients.list(q, page)`, not an inline literal

#### Scenario: Pages key distinctly
- **WHEN** the same `q` is requested for page 1 and page 2
- **THEN** `queryKeys.patients.list(q, 1)` MUST NOT equal `queryKeys.patients.list(q, 2)` by deep comparison

#### Scenario: List and detail keys are distinct
- **WHEN** the same `patientId` is referenced by both a list query and a detail query
- **THEN** `queryKeys.patients.list()` MUST NOT be equal to `queryKeys.patients.detail(id)` by deep comparison
