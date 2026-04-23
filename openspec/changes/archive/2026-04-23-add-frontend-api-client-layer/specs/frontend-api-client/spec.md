## ADDED Requirements

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
- `ApiError` — an `Error` subclass carrying `status: number`, `code?: string`, `body: unknown`
- (Optional, but allowed) `apiPost`, `apiPut`, `apiDelete` with the same error contract

Non-2xx responses MUST throw `ApiError`. Network / parse failures MUST throw an `ApiError` with `status=0`.

#### Scenario: Successful GET returns parsed body
- **WHEN** the client calls `apiGet<Patient[]>('/patients')` and the server responds 200 with a JSON array
- **THEN** the promise MUST resolve with the parsed array typed as `Patient[]`

#### Scenario: 4xx response becomes ApiError
- **WHEN** the server responds 404 with body `{"error": "patient_not_found", "patientId": "abc"}`
- **THEN** the promise MUST reject with an `ApiError` instance whose `status=404`, `code="patient_not_found"`, and `body` equals the parsed body

#### Scenario: Network failure becomes ApiError
- **WHEN** `fetch` itself rejects (e.g. backend not running)
- **THEN** the promise MUST reject with an `ApiError` whose `status=0`

### Requirement: Frontend SHALL provide service functions that wrap API endpoints

The directory `frontend/src/services/` MUST host pure, React-agnostic service functions. This change MUST add at minimum:
- `patients.ts`:
  - `fetchPatients(): Promise<Patient[]>` — calls `apiGet<Patient[]>('/patients')`
  - `fetchPatient(patientId: string): Promise<Patient>` — calls `apiGet<Patient>('/patients/{patientId}')`

Service functions MUST NOT import from `react` or `@tanstack/react-query` — they are usable from any context (hooks, tests, Node scripts).

#### Scenario: fetchPatients calls the gateway list endpoint
- **WHEN** a test calls `fetchPatients()` with a mocked `/patients` endpoint returning a valid array
- **THEN** the return value MUST be the parsed array typed as `Patient[]`
- **AND** the implementation MUST NOT reach into React or React Query APIs

### Requirement: Frontend SHALL provide React Query hooks for patient resources

The directory `frontend/src/hooks/queries/` MUST provide:
- `usePatients()` — wraps `useQuery` with `queryKey: ['patients']` and `queryFn: fetchPatients`
- `usePatient(patientId: string | undefined)` — wraps `useQuery` with `queryKey: ['patients', patientId]`, `queryFn: () => fetchPatient(patientId!)`, and `enabled: Boolean(patientId)`

Query keys MUST follow the convention defined below.

#### Scenario: usePatients exposes list data
- **WHEN** a component renders `const { data } = usePatients();` and the `/patients` endpoint resolves
- **THEN** `data` MUST be `Patient[]` once loaded
- **AND** React Query Devtools MUST show the query under key `['patients']`

#### Scenario: usePatient disabled when id is undefined
- **WHEN** a component renders `usePatient(undefined)`
- **THEN** no network request MUST be issued
- **AND** the query status MUST be `pending` with `fetchStatus: 'idle'`

### Requirement: Frontend SHALL define query key conventions in a central module

The module `frontend/src/hooks/queries/keys.ts` MUST export a `queryKeys` helper organising keys as:
- `queryKeys.patients.all` → `['patients']`
- `queryKeys.patients.detail(id)` → `['patients', id]`
- `queryKeys.patients.subResource(id, name)` → `['patients', id, name]`

Hooks and any future invalidation calls MUST use this helper rather than inline literal arrays, to keep key shape consistent and refactor-safe.

#### Scenario: Hook uses central key helper
- **WHEN** a developer opens `usePatients.ts`
- **THEN** the `queryKey` argument MUST be `queryKeys.patients.all` (or an equivalent call), not an inline `['patients']` literal

### Requirement: Patient type SHALL live in a dedicated types module

This change MUST create `frontend/src/types/patient.ts` as the authoritative source for the `Patient` TypeScript type and its sample/record sub-types (`PatientSource`, `OpdRecord`, `AaSample`, `MsmsSample`, `BiomarkerSample`, `AadcSample`, `AldSample`, `MmaSample`, `Mps2Sample`, `LsdSample`, `EnzymeSample`, `GagSample`, `DnabankRecord`, `OutbankRecord`, `BdSample`, `TgalSubSample`, `CahSample`, `TshSubSample`, `DmdSample`, `G6pdSample`, `SmaScidSample`). The existing `frontend/src/types/medical.ts` MUST re-export those types (`export type { Patient, PatientSource, ... } from '@/types/patient'`) so existing imports from `@/types/medical` keep working. Field names and casing MUST match the backend gateway response exactly (camelCase, as produced by `backend.shared.schemas`).

#### Scenario: New service consumer imports Patient
- **WHEN** a developer adds a new hook or service that references `Patient`
- **THEN** the recommended import MUST be `import type { Patient } from '@/types/patient'`
- **AND** no existing component importing from `@/types/medical` MUST break (via re-export compatibility)

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
