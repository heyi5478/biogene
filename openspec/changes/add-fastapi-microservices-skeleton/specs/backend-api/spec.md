## ADDED Requirements

### Requirement: Backend SHALL expose a single HTTP gateway on port 8000 as the frontend's only entry point

The backend MUST run a FastAPI application named `gateway` that listens on `127.0.0.1:8000` (or `0.0.0.0:8000` when containerised). The gateway SHALL be the only service reachable from the frontend; `svc-patient`, `svc-lab`, and `svc-disease` MUST NOT be exposed to the frontend directly.

#### Scenario: Frontend sends request through gateway
- **WHEN** the frontend issues `GET http://localhost:8000/patients`
- **THEN** the gateway MUST accept the request and return an HTTP 200 with a JSON array

#### Scenario: Internal service not reachable from frontend origin
- **WHEN** the frontend attempts `GET http://localhost:8001/patients` (svc-patient)
- **THEN** the request MUST fail CORS (the service MUST NOT configure CORS for browser origins)

### Requirement: Gateway SHALL aggregate patient bundles by fanning out to downstream services

For `GET /patients` and `GET /patients/{patientId}`, the gateway MUST fetch patient base records from `svc-patient`, lab records from `svc-lab`, and disease-module records from `svc-disease` in parallel using `httpx.AsyncClient`, then merge them into `PatientBundle` objects whose shape is compatible with the frontend's `Patient` TypeScript type.

#### Scenario: Aggregated list response
- **WHEN** a client calls `GET /patients`
- **THEN** the gateway MUST return a JSON array where each element contains the patient's base fields AND nested arrays `aa`, `msms`, `biomarker`, and the relevant disease-module arrays (e.g. `aadc`, `ald`, `bd`, `cah`, `dmd`) filled from the patient's `patientId`

#### Scenario: Single-patient aggregated response
- **WHEN** a client calls `GET /patients/{patientId}` with a known patientId
- **THEN** the gateway MUST return a single JSON object (not array) with the same bundle shape
- **AND** the status MUST be 200

#### Scenario: Unknown patientId
- **WHEN** a client calls `GET /patients/{patientId}` with an id that is not present in svc-patient
- **THEN** the gateway MUST return HTTP 404 with an error body `{"error": "patient_not_found", "patientId": "<id>"}`

#### Scenario: Downstream service fails
- **WHEN** the gateway receives a 5xx or connection error from any of svc-patient, svc-lab, svc-disease during an aggregate call
- **THEN** the gateway MUST return HTTP 502 with an error body identifying which downstream failed
- **AND** the gateway MUST NOT return a partial bundle

### Requirement: Backend SHALL split responsibilities across four services

The backend MUST run four FastAPI applications:
- `gateway` (port 8000): aggregation + CORS; owns no data
- `svc-patient` (port 8001): serves `patient.json` across `db_main`, `db_external`, `db_nbs`
- `svc-lab` (port 8002): serves common lab tables (`aa`, `msms`, `biomarker`, `outbank`, `dnabank`) across all three databases
- `svc-disease` (port 8003): serves disease-module tables — `db_main/{aadc,ald,mma,mps2,lsd,enzyme,gag}` and `db_nbs/{bd,cah,cah_tgal,dmd,dmd_tsh,g6pd,sma_scid}`

Each service MUST be independently startable via `uvicorn <package>.app:app --port <port>`.

#### Scenario: svc-patient returns merged patient list
- **WHEN** a client (gateway) calls `GET http://localhost:8001/patients`
- **THEN** svc-patient MUST return all patients from `db_main/patient.json`, `db_external/patient.json`, and `db_nbs/patient.json`, each carrying its original `source` field

#### Scenario: svc-lab returns lab records for one patient
- **WHEN** gateway calls `GET http://localhost:8002/labs/{patientId}`
- **THEN** svc-lab MUST return `{"aa": [...], "msms": [...], "biomarker": [...], "outbank": [...], "dnabank": [...]}` where each array contains only rows whose `patientId` matches

#### Scenario: svc-disease returns disease-module records for one patient
- **WHEN** gateway calls `GET http://localhost:8003/diseases/{patientId}`
- **THEN** svc-disease MUST return an object with keys for each owned module (`aadc`, `ald`, `mma`, `mps2`, `lsd`, `enzyme`, `gag`, `bd`, `cah`, `cah_tgal`, `dmd`, `dmd_tsh`, `g6pd`, `smaScid`) containing only rows linked to that patientId
- **AND** NBS sub-tables (`cah_tgal`, `dmd_tsh`) MUST be joined by their parent id (`cahId`, `dmdId`), not by `patientId`

### Requirement: Each service SHALL validate FK integrity on startup

On FastAPI `lifespan` startup, every service MUST call `backend.shared.data_loader.validate()` which wraps `backend/scripts/load_mock.py`. If any FK violation is detected, the service MUST log the offending rows and exit with a non-zero status before accepting traffic.

#### Scenario: Clean mock data
- **WHEN** all JSON files have valid FK references and a service is started
- **THEN** the startup log MUST contain "mock-data FK validation passed"
- **AND** the service MUST begin listening on its configured port

#### Scenario: Dangling FK
- **WHEN** a sample row references a non-existent patientId and a service is started
- **THEN** the service MUST log the offending file path, row index, and patientId
- **AND** exit with non-zero status before binding the port

### Requirement: Gateway SHALL configure CORS for the Vite development origin

The gateway MUST register FastAPI's `CORSMiddleware` allowing origin `http://localhost:5173`, methods `GET, POST, PUT, DELETE, OPTIONS`, and headers `*`. Production origins are out of scope for this change.

#### Scenario: Preflight from Vite dev server
- **WHEN** the browser sends `OPTIONS /patients` with `Origin: http://localhost:5173`
- **THEN** the gateway MUST respond with `Access-Control-Allow-Origin: http://localhost:5173`
- **AND** status 200 or 204

#### Scenario: Disallowed origin
- **WHEN** the browser sends a request with `Origin: http://evil.example.com`
- **THEN** the gateway MUST NOT include `Access-Control-Allow-Origin` in the response

### Requirement: Every service SHALL provide a /healthz endpoint

Each of `gateway`, `svc-patient`, `svc-lab`, `svc-disease` MUST expose `GET /healthz` that returns HTTP 200 with body `{"status": "ok", "service": "<service-name>"}` when the service has completed startup validation.

#### Scenario: Healthcheck after successful startup
- **WHEN** a client calls `GET /healthz` on any running service
- **THEN** the response MUST be 200 with `status=ok` and the correct service name

### Requirement: Response schemas SHALL match the frontend Patient type using camelCase field names

All JSON responses MUST preserve the exact camelCase field names present in the mock-data JSON files (e.g. `patientId`, `dbsLysoGb3`, `externalChartno`, `linkedPatientIds`). Pydantic models in `backend/shared/schemas.py` MUST NOT rename fields to snake_case in the wire format.

#### Scenario: Gateway returns patient bundle
- **WHEN** `GET /patients/{patientId}` returns a body
- **THEN** the body MUST contain keys `patientId`, `source`, and (depending on source) `chartno` | `externalChartno` | `nbsId`
- **AND** nested lab arrays MUST use the original JSON field names unchanged

### Requirement: Shared schemas and data loader SHALL live in backend/shared

The directory `backend/shared/` MUST contain:
- `schemas.py`: Pydantic v2 models for every record type served by any service
- `data_loader.py`: a thin wrapper over `backend/scripts/load_mock.py` exposing `load_all()` and `validate()` as the stable import path for services

All three svc-* services and the gateway MUST import from `backend.shared` rather than duplicating schemas or loader logic.

#### Scenario: Adding a new module
- **WHEN** a future change adds a new disease module (e.g. `foo`)
- **THEN** the contributor MUST add `FooRecord` to `backend/shared/schemas.py` exactly once
- **AND** import it from the owning service (svc-disease)
