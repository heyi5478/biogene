# frontend-api-client Specification

## Purpose
TBD - created by archiving change add-frontend-api-client-layer. Update Purpose after archive.
## Requirements

### Requirement: Frontend SHALL read the backend base URL from a Vite environment variable

The base URL for backend API calls MUST come from `import.meta.env.VITE_API_BASE_URL`. The repository MUST provide `.env.development` with `VITE_API_BASE_URL=http://localhost:8000` and `.env.example` documenting the variable. `vite-env.d.ts` MUST declare `VITE_API_BASE_URL: string` on `ImportMetaEnv`.

#### Scenario: Dev server reads base URL from .env.development
- **WHEN** a developer runs `npm run dev` in `frontend/` without setting any environment variable externally
- **THEN** the app MUST issue API requests against `http://localhost:8000` by loading `.env.development`

#### Scenario: Missing env variable
- **WHEN** the env variable `VITE_API_BASE_URL` is not set in any `.env*` file
- **THEN** the first call to the API client MUST throw an error whose message contains "VITE_API_BASE_URL is not set"
- **AND** the error MUST be visible in the browser console during development

### Requirement: Frontend SHALL provide a typed HTTP client module at src/lib/api.ts

The module `frontend/src/lib/api.ts` MUST export:
- `apiGet<T>(path: string, init?: RequestInit): Promise<T>` — issues a GET against `${VITE_API_BASE_URL}${path}`, parses JSON, returns `T`
- `apiPost<T>(path: string, body: unknown, init?: RequestInit): Promise<T>` — issues a POST with JSON body and `Content-Type: application/json`, parses JSON response, returns `T`
- `ApiError` — an `Error` subclass carrying `status: number`, `code?: string`, `body: unknown`
- (Optional, but allowed) `apiPut`, `apiDelete` with the same error contract

Non-2xx responses MUST throw `ApiError`. Network / parse failures MUST throw an `ApiError` with `status=0`.

#### Scenario: Successful GET returns parsed body
- **WHEN** the client calls `apiGet<PatientListItem[]>('/patients')` and the server responds 200 with a JSON array
- **THEN** the promise MUST resolve with the parsed array typed as `PatientListItem[]`

#### Scenario: Successful POST returns parsed body
- **WHEN** the client calls `apiPost<PatientListItem[]>('/patients/condition-query', body)` and the server responds 200 with a JSON array
- **THEN** the promise MUST resolve with the parsed array
- **AND** the request MUST have included header `Content-Type: application/json` and a body equal to `JSON.stringify(body)`

#### Scenario: 4xx response becomes ApiError
- **WHEN** the server responds 404 with body `{"error": "patient_not_found", "patientId": "abc"}`
- **THEN** the promise MUST reject with an `ApiError` instance whose `status=404`, `code="patient_not_found"`, and `body` equals the parsed body

#### Scenario: Network failure becomes ApiError
- **WHEN** `fetch` itself rejects (e.g. backend not running)
- **THEN** the promise MUST reject with an `ApiError` whose `status=0`

### Requirement: Frontend SHALL provide service functions that wrap API endpoints

The directory `frontend/src/services/` MUST host pure, React-agnostic service functions. The module `patients.ts` MUST export at minimum:
- `PATIENT_PAGE_SIZE` — the patient-list page size constant (`50`)
- `fetchPatients(q: string, page: number): Promise<PatientListPage>` — calls `apiGet<PatientListPage>('/patients?...')` with `limit` set to `PATIENT_PAGE_SIZE` and `offset` set to `(page - 1) * PATIENT_PAGE_SIZE`; when `q` is non-empty the request MUST also include a URL-encoded `q` parameter; when `q` is empty the request MUST omit the `q` parameter entirely
- `fetchPatient(patientId: string): Promise<Patient>` — calls `apiGet<Patient>('/patients/{patientId}')`
- `searchByConditions(req: ConditionRequest, page: number): Promise<PatientListPage>` — calls `apiPost<PatientListPage>('/patients/condition-query?...', req)` with `limit` set to `PATIENT_PAGE_SIZE` and `offset` set to `(page - 1) * PATIENT_PAGE_SIZE` on the query string, and `req` as the JSON body

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

#### Scenario: searchByConditions issues a paginated POST
- **WHEN** a test calls `searchByConditions({conditions: [...], logic: 'AND'}, 1)`
- **THEN** the request MUST be POST `/patients/condition-query` with `limit=50` and `offset=0` on the query string and the body equal to the condition request
- **AND** the return value MUST be the parsed `PatientListPage` envelope

#### Scenario: searchByConditions requests a later page
- **WHEN** a test calls `searchByConditions({conditions: [...], logic: 'AND'}, 3)`
- **THEN** the request URL MUST include `offset=100` (page 3 at page size 50)

### Requirement: Frontend SHALL provide React Query hooks for patient resources

The directory `frontend/src/hooks/queries/` MUST provide:
- `usePatients(q: string, page: number)` — wraps `useQuery` with `queryKey: queryKeys.patients.list(q, page)`, `queryFn: () => fetchPatients(q, page)`, `enabled: q !== ''` (no request is issued until a non-empty query is submitted), and `placeholderData` set to React Query's `keepPreviousData` so the current page stays visible while the next page loads
- `usePatient(patientId: string | undefined)` — wraps `useQuery` with `queryKey: queryKeys.patients.detail(patientId)`, `queryFn: () => fetchPatient(patientId!)`, and `enabled: Boolean(patientId)`
- `useConditionPatients(req: ConditionRequest, page: number, enabled: boolean)` — wraps `useQuery` with `queryKey: queryKeys.patients.condition(req, page)`, `queryFn: () => searchByConditions(req, page)`, the supplied `enabled` flag (callers MUST pass `false` until the user submits a non-empty condition list), and `placeholderData` set to React Query's `keepPreviousData` so the current page stays visible while the next page loads

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
- **WHEN** a component renders `useConditionPatients({conditions: [], logic: 'AND'}, 1, false)`
- **THEN** no network request MUST be issued
- **AND** the query status MUST be `pending` with `fetchStatus: 'idle'`

#### Scenario: useConditionPatients keys per page
- **WHEN** a component renders `useConditionPatients(req, 1, true)` then `useConditionPatients(req, 2, true)` for the same `req`
- **THEN** React Query MUST track two distinct queries with different keys
- **AND** each query's request URL MUST reflect its `offset`

#### Scenario: usePatient disabled when id is undefined
- **WHEN** a component renders `usePatient(undefined)`
- **THEN** no network request MUST be issued
- **AND** the query status MUST be `pending` with `fetchStatus: 'idle'`

### Requirement: Frontend SHALL define query key conventions in a central module

The module `frontend/src/hooks/queries/keys.ts` MUST export a `queryKeys` helper organising keys as:
- `queryKeys.patients.list(q?: string, page?: number)` → `['patients', 'list', q ?? '', page ?? 1]`
- `queryKeys.patients.condition(req: ConditionRequest, page?: number)` → `['patients', 'condition', req, page ?? 1]`
- `queryKeys.patients.detail(id: string | undefined)` → `['patients', id]`
- `queryKeys.patients.subResource(id: string, name: string)` → `['patients', id, name]`

Hooks and any future invalidation calls MUST use this helper rather than inline literal arrays. The `list` and `condition` keys MUST include the page number so each page caches independently.

#### Scenario: Hook uses central key helper
- **WHEN** a developer opens `usePatients.ts`
- **THEN** the `queryKey` argument MUST be `queryKeys.patients.list(q, page)`, not an inline literal

#### Scenario: Pages key distinctly
- **WHEN** the same `q` is requested for page 1 and page 2
- **THEN** `queryKeys.patients.list(q, 1)` MUST NOT equal `queryKeys.patients.list(q, 2)` by deep comparison

#### Scenario: Condition pages key distinctly
- **WHEN** the same `req` is requested for page 1 and page 2
- **THEN** `queryKeys.patients.condition(req, 1)` MUST NOT equal `queryKeys.patients.condition(req, 2)` by deep comparison

#### Scenario: List and detail keys are distinct
- **WHEN** the same `patientId` is referenced by both a list query and a detail query
- **THEN** `queryKeys.patients.list()` MUST NOT be equal to `queryKeys.patients.detail(id)` by deep comparison

### Requirement: Patient type SHALL live in a dedicated types module

The module `frontend/src/types/patient.ts` MUST be the authoritative source for:
- The `Patient` TypeScript type (full bundle: base fields + every module array, mirroring the gateway's `PatientBundle` Pydantic model) and its sample/record sub-types (`PatientSource`, `OpdRecord`, `AaSample`, `MsmsSample`, `BiomarkerSample`, `AadcSample`, `AldSample`, `MmaSample`, `Mps2Sample`, `LsdSample`, `EnzymeSample`, `GagSample`, `DnabankRecord`, `OutbankRecord`, `BdSample`, `TgalSubSample`, `CahSample`, `TshSubSample`, `DmdSample`, `G6pdSample`, `SmaScidSample`).
- The `PatientListItem` TypeScript interface mirroring the gateway's `PatientListItem` Pydantic model: base patient fields plus `dnabankCount: number`, `outbankCount: number`, `lastVisitDate: string | null`, optional `conditionHits?: string[]`. `PatientListItem` MUST NOT contain any module detail arrays.

The existing `frontend/src/types/medical.ts` MUST re-export `Patient`, `PatientListItem`, and the sample/record sub-types so existing imports from `@/types/medical` keep working. Field names MUST match the backend gateway response exactly (camelCase).

#### Scenario: New service consumer imports PatientListItem
- **WHEN** a developer adds a hook that calls `fetchPatients`
- **THEN** the recommended import MUST be `import type { PatientListItem } from '@/types/patient'`
- **AND** no existing component importing from `@/types/medical` MUST break

#### Scenario: PatientListItem has no module arrays
- **WHEN** TypeScript checks the `PatientListItem` interface
- **THEN** the type MUST NOT have any property whose type is an array of module record types (e.g. `AaSample[]`, `OpdRecord[]`)

### Requirement: QueryClient SHALL be configured with project-wide defaults

The `QueryClient` instance in `frontend/src/App.tsx` MUST be constructed with defaults:
- `queries.staleTime: 60_000`
- `queries.retry: 1`
- `queries.refetchOnWindowFocus: false`

Individual hooks MAY override these via `useQuery` options.

#### Scenario: Default staleTime applies
- **WHEN** a component calls `usePatients()` twice in under 60 seconds
- **THEN** the second render MUST reuse cached data without issuing a second network request

### Requirement: UI behavior SHALL remain unchanged by this change

This change MUST NOT modify any file under `frontend/src/pages/`, `frontend/src/components/`, or `frontend/src/data/mockData.ts`'s runtime exports. Index.tsx MUST continue to consume `mockPatients` as before. The change is purely additive infrastructure.

#### Scenario: Regression check after change
- **WHEN** the change is merged and the dev server is started
- **THEN** the Index page rendering, search, and condition filtering MUST behave identically to the pre-change state
- **AND** existing Playwright E2E tests MUST pass without modification

### Requirement: Frontend SHALL define a paginated patient-list envelope type

The module `frontend/src/types/patient.ts` MUST define a generic page envelope type `Page<T>` with the fields `items: T[]`, `total: number`, `limit: number`, `offset: number`, and a `PatientListPage` alias equal to `Page<PatientListItem>` that mirrors the gateway's paginated `GET /patients` response. The existing `frontend/src/types/medical.ts` MUST re-export both `Page` and `PatientListPage` so existing `@/types/medical` imports keep working.

#### Scenario: PatientListPage mirrors the gateway envelope
- **WHEN** a developer types the resolved value of a paginated `GET /patients` call
- **THEN** `PatientListPage` MUST expose `items: PatientListItem[]`, `total: number`, `limit: number`, and `offset: number`

#### Scenario: Page type is re-exported from medical.ts
- **WHEN** a module imports `Page` or `PatientListPage` from `@/types/medical`
- **THEN** the import MUST resolve to the definitions declared in `@/types/patient`
