## ADDED Requirements

### Requirement: svc-patient SHALL expose a patient base-row batch endpoint

`svc-patient` (port 8001) MUST expose `POST /patients/batch` accepting `{ "patientIds": [...] }` and returning `dict[patientId, Patient]` — a mapping from each requested id that exists to its patient base row. An id that no patient matches MUST be omitted from the response object (a `Patient` has required fields, so no placeholder row is possible); an unknown id MUST NOT produce an error. This endpoint lets the gateway resolve a known set of patients' base rows without fetching the whole patient table.

#### Scenario: Batch base-row lookup
- **WHEN** the gateway calls `POST http://localhost:8001/patients/batch` with `{ "patientIds": ["a", "b"] }` where both ids exist
- **THEN** svc-patient MUST return `{"a": {<patient a base row>}, "b": {<patient b base row>}}`
- **AND** each value MUST carry the patient's original `source` field

#### Scenario: Unknown id is omitted
- **WHEN** the request includes a `patientId` that no patient matches
- **THEN** that id MUST be absent from the response object
- **AND** the response status MUST be 200 (not an error)

#### Scenario: Empty id list
- **WHEN** the gateway calls `POST /patients/batch` with `{ "patientIds": [] }`
- **THEN** svc-patient MUST return an empty object `{}` with status 200

## MODIFIED Requirements

### Requirement: Backend SHALL expose a single HTTP gateway on port 8000 as the frontend's only entry point

The backend MUST run a FastAPI application named `gateway` that listens on `127.0.0.1:8000` (or `0.0.0.0:8000` when containerised). The gateway SHALL be the only service reachable from the frontend; `svc-patient`, `svc-lab`, and `svc-disease` MUST NOT be exposed to the frontend directly.

#### Scenario: Frontend sends request through gateway
- **WHEN** the frontend issues `GET http://localhost:8000/patients`
- **THEN** the gateway MUST accept the request and return an HTTP 200 with a paginated JSON object of shape `{items, total, limit, offset}`

#### Scenario: Internal service not reachable from frontend origin
- **WHEN** the frontend attempts `GET http://localhost:8001/patients` (svc-patient)
- **THEN** the request MUST fail CORS (the service MUST NOT configure CORS for browser origins)

### Requirement: Gateway list endpoint SHALL return a slim PatientListItem array

The endpoint `GET /patients` MUST return a paginated envelope of shape `{ "items": PatientListItem[], "total": int, "limit": int, "offset": int }`. It MUST accept `limit` (default 50, minimum 1, maximum 200) and `offset` (default 0, minimum 0) query parameters; out-of-range values MUST be rejected with HTTP 422. `items` MUST contain at most `limit` elements — the requested page of results. `total` MUST be the count of all matching patients across every page, not the page size. `limit` and `offset` MUST echo the effective values used.

Each element of `items` MUST contain the patient's base fields (`patientId`, `source`, `name`, `birthday`, `sex`, optional `chartno`, optional `externalChartno`, optional `nbsId`, optional `category`, `linkedPatientIds`, optional `diagnosis`, optional `diagnosis2`, optional `diagnosis3`) plus the summary fields `dnabankCount: int`, `outbankCount: int`, `lastVisitDate: string | null`. No element MUST include any module detail array (no `aa`, `msms`, `biomarker`, `aadc`, `ald`, `mma`, `mps2`, `lsd`, `enzyme`, `gag`, `dnabank`, `outbank`, `opd`, `bd`, `cah`, `dmd`, `g6pd`, `smaScid`, `gcms`).

#### Scenario: Paginated response shape
- **WHEN** a client calls `GET /patients?limit=50&offset=0`
- **THEN** the response MUST be an object with keys `items`, `total`, `limit`, `offset`
- **AND** `items` MUST contain at most 50 elements
- **AND** every element MUST contain `dnabankCount`, `outbankCount`, and `lastVisitDate`
- **AND** no element MUST contain a key whose value is an array of module records

#### Scenario: total reflects the full result set
- **WHEN** the dataset contains 120 patients and a client calls `GET /patients?limit=50&offset=0`
- **THEN** `items` MUST contain 50 elements
- **AND** `total` MUST be 120

#### Scenario: offset past the end yields an empty page
- **WHEN** a client calls `GET /patients` with an `offset` greater than or equal to `total`
- **THEN** `items` MUST be an empty array
- **AND** `total` MUST still report the full count
- **AND** the status MUST be 200

#### Scenario: Invalid pagination parameters are rejected
- **WHEN** a client calls `GET /patients?limit=0`, `GET /patients?limit=5000`, or `GET /patients?offset=-1`
- **THEN** the gateway MUST respond with HTTP 422

#### Scenario: Summary fields reflect underlying data
- **WHEN** a patient has 2 dnabank rows, 1 outbank row, and an opd visit on `2025-12-10`
- **THEN** that patient's list item MUST have `dnabankCount: 2`, `outbankCount: 1`, `lastVisitDate: "2025-12-10"`

#### Scenario: Patient with no opd
- **WHEN** a patient has no opd rows
- **THEN** that patient's list item MUST have `lastVisitDate: null`

### Requirement: Gateway SHALL support text search via the `q` query parameter on the list endpoint

The endpoint `GET /patients` MUST accept an optional `q` query parameter alongside `limit` and `offset`. The `q` filter MUST be applied before pagination: the gateway MUST first determine the full set of matching patients, then return the `offset`-based page of at most `limit` items, with `total` set to the size of the full matching set. When `q` is absent or empty, the matching set MUST be every patient. When `q` is non-empty, the matching set MUST contain only patients whose `name`, `chartno`, `externalChartno`, or `nbsId` includes `q` (case-insensitive for the latin fields, exact substring for `name`).

#### Scenario: No q parameter
- **WHEN** a client calls `GET /patients?limit=50&offset=0`
- **THEN** `total` MUST equal the number of patients known to svc-patient
- **AND** `items` MUST contain the first 50 of them (or all of them if fewer than 50)

#### Scenario: q matches a name substring
- **WHEN** the dataset includes a patient named `陳志明` and a client calls `GET /patients?q=陳`
- **THEN** `total` MUST count only patients whose name contains `陳` or whose chartno/externalChartno/nbsId contains `陳`
- **AND** that patient MUST appear in `items` when it falls within the requested page

#### Scenario: q matches a chartno prefix
- **WHEN** the dataset includes chartno `A1234567` and a client calls `GET /patients?q=A12`
- **THEN** the patient with that chartno MUST be part of the matching set counted by `total`

#### Scenario: q matches nothing
- **WHEN** a client calls `GET /patients?q=zzzz_no_match`
- **THEN** `items` MUST be an empty array `[]`
- **AND** `total` MUST be 0
- **AND** the status MUST be 200

### Requirement: Backend SHALL split responsibilities across four services

The backend MUST run four FastAPI applications:
- `gateway` (port 8000): aggregation + CORS; owns no data
- `svc-patient` (port 8001): serves `patient.json` across `db_main`, `db_external`, `db_nbs`
- `svc-lab` (port 8002): serves common lab tables (`aa`, `msms`, `biomarker`, `outbank`, `dnabank`) across all three databases
- `svc-disease` (port 8003): serves disease-module tables — `db_main/{aadc,ald,mma,mps2,lsd,enzyme,gag}` and `db_nbs/{bd,cah,cah_tgal,dmd,dmd_tsh,g6pd,sma_scid}`

Each service MUST be independently startable via `uvicorn <package>.app:app --port <port>`.

#### Scenario: svc-patient returns a paginated patient list
- **WHEN** a client (gateway) calls `GET http://localhost:8001/patients?limit=50&offset=0`
- **THEN** svc-patient MUST return a paginated envelope `{items, total, limit, offset}` whose `items` are patients drawn from `db_main/patient.json`, `db_external/patient.json`, and `db_nbs/patient.json`, each carrying its original `source` field
- **AND** `total` MUST be the full count of patients across the three files matching any supplied `q`

#### Scenario: svc-lab returns lab records for one patient
- **WHEN** gateway calls `GET http://localhost:8002/labs/{patientId}`
- **THEN** svc-lab MUST return `{"aa": [...], "msms": [...], "biomarker": [...], "outbank": [...], "dnabank": [...]}` where each array contains only rows whose `patientId` matches

#### Scenario: svc-disease returns disease-module records for one patient
- **WHEN** gateway calls `GET http://localhost:8003/diseases/{patientId}`
- **THEN** svc-disease MUST return an object with keys for each owned module (`aadc`, `ald`, `mma`, `mps2`, `lsd`, `enzyme`, `gag`, `bd`, `cah`, `cah_tgal`, `dmd`, `dmd_tsh`, `g6pd`, `smaScid`) containing only rows linked to that patientId
- **AND** NBS sub-tables (`cah_tgal`, `dmd_tsh`) MUST be joined by their parent id (`cahId`, `dmdId`), not by `patientId`
