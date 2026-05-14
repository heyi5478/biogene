## MODIFIED Requirements

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
- `fetchPatients(q?: string): Promise<PatientListItem[]>` — calls `apiGet<PatientListItem[]>('/patients?q={q}')`; the `q` parameter MUST be URL-encoded; when `q` is `undefined` or empty, the request MUST omit the `q` query parameter entirely
- `fetchPatient(patientId: string): Promise<Patient>` — calls `apiGet<Patient>('/patients/{patientId}')`
- `searchByConditions(req: ConditionRequest): Promise<PatientListItem[]>` — calls `apiPost<PatientListItem[]>('/patients/condition-query', req)`

`ConditionRequest` MUST be `{conditions: ConditionRow[], logic: 'AND' | 'OR'}`. Service functions MUST NOT import from `react` or `@tanstack/react-query`.

#### Scenario: fetchPatients without q
- **WHEN** a test calls `fetchPatients()` (no argument) with a mocked `/patients` endpoint
- **THEN** the request URL MUST end in `/patients` with no query string
- **AND** the return value MUST be the parsed array typed as `PatientListItem[]`

#### Scenario: fetchPatients with q
- **WHEN** a test calls `fetchPatients('陳')`
- **THEN** the request URL MUST contain `?q=` followed by the URL-encoded value of `陳`

#### Scenario: searchByConditions issues POST
- **WHEN** a test calls `searchByConditions({conditions: [...], logic: 'AND'})`
- **THEN** the request MUST be POST `/patients/condition-query` with the body equal to the input

### Requirement: Frontend SHALL provide React Query hooks for patient resources

The directory `frontend/src/hooks/queries/` MUST provide:
- `usePatients(q?: string)` — wraps `useQuery` with `queryKey: queryKeys.patients.list(q)` and `queryFn: () => fetchPatients(q)`
- `usePatient(patientId: string | undefined)` — wraps `useQuery` with `queryKey: queryKeys.patients.detail(patientId)`, `queryFn: () => fetchPatient(patientId!)`, and `enabled: Boolean(patientId)`
- `useConditionPatients(req: ConditionRequest, enabled: boolean)` — wraps `useQuery` with `queryKey: queryKeys.patients.condition(req)`, `queryFn: () => searchByConditions(req)`, and the supplied `enabled` flag (callers MUST pass `false` until the user submits a non-empty condition list)

`usePatients` and `useConditionPatients` MUST set `staleTime: 5 * 60 * 1000` and `gcTime: 30 * 60 * 1000` so navigation across the SPA does not re-issue requests within the stale window.

#### Scenario: usePatients keys per q
- **WHEN** a component renders `usePatients('陳')` then `usePatients('A')` in sequence
- **THEN** React Query Devtools MUST show two distinct queries with different keys
- **AND** each query's request URL MUST reflect its `q` value

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
- `queryKeys.patients.list(q?: string)` → `['patients', 'list', q ?? '']`
- `queryKeys.patients.condition(req: ConditionRequest)` → `['patients', 'condition', req]`
- `queryKeys.patients.detail(id: string | undefined)` → `['patients', id]`
- `queryKeys.patients.subResource(id: string, name: string)` → `['patients', id, name]`

Hooks and any future invalidation calls MUST use this helper rather than inline literal arrays. Note: `queryKeys.patients.all` (the previous flat list key) is removed by this change; callers MUST migrate to `queryKeys.patients.list()`.

#### Scenario: Hook uses central key helper
- **WHEN** a developer opens `usePatients.ts`
- **THEN** the `queryKey` argument MUST be `queryKeys.patients.list(q)`, not an inline literal

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
