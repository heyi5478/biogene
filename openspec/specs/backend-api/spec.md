# backend-api Specification

## Purpose
TBD - created by archiving change add-fastapi-microservices-skeleton. Update Purpose after archive.
## Requirements

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

### Requirement: Gateway PatientBundle SHALL include opd visit records

The `PatientBundle` returned by `GET /patients` and `GET /patients/{patientId}` MUST include an `opd` array whose elements match `OpdRecord` (`patientId`, `visitDate`, `sex`, `birthday`, `diagCode`, `diagName`, optional `subDiag1`, optional `subDiag2`). Patients with no opd history MUST receive `opd: []`; the key MUST always be present.

#### Scenario: List response includes opd for every patient

- **WHEN** a client calls `GET http://localhost:8000/patients`
- **THEN** every element in the response array MUST contain the key `opd`
- **AND** for patients whose `patientId` appears in `db_{main,external,nbs}/opd.json`, the array MUST contain one element per matching row

#### Scenario: Single-patient response includes opd

- **WHEN** a client calls `GET http://localhost:8000/patients/{patientId}` with a known id
- **THEN** the returned JSON object MUST contain `opd`
- **AND** its length MUST equal the number of `opd.json` rows whose `patientId` matches

#### Scenario: Patient with no opd history

- **WHEN** a patient has no entry in any `opd.json`
- **THEN** the response's `opd` field MUST be an empty array (not `null`, not absent)

### Requirement: svc-patient SHALL expose opd visit endpoints

`svc-patient` (port 8001) MUST load `db_{main,external,nbs}/opd.json` at startup into an in-memory index keyed by `patientId`, and MUST expose:

- `GET /opd/{patient_id}` returning an `OpdBundle` (`{ "opd": [...] }`) — empty bundle if the id has no opd rows
- `POST /opd/batch` accepting `{ "patientIds": [...] }` and returning `dict[patientId, OpdBundle]` — patients with no rows receive an empty bundle

Response shape MUST mirror `svc-lab` / `svc-disease` bundle conventions so the gateway can flat-merge via `{**patient, **opd, **labs, **diseases}`.

#### Scenario: Single opd lookup

- **WHEN** the gateway calls `GET http://localhost:8001/opd/{patientId}`
- **THEN** svc-patient MUST return `{"opd": [...]}` where each row has the `patientId` matching the request

#### Scenario: Batch opd lookup

- **WHEN** the gateway calls `POST http://localhost:8001/opd/batch` with `{ "patientIds": ["a", "b"] }`
- **THEN** svc-patient MUST return `{"a": {"opd": [...]}, "b": {"opd": [...]}}`
- **AND** an unknown id in the request MUST receive an empty bundle `{"opd": []}`, not an error

### Requirement: Gateway SHALL fan out to svc-patient opd endpoints in parallel with lab and disease calls

The gateway's aggregation MUST include opd fetches in the same `asyncio.gather` critical path as lab and disease fetches, so the added fan-out does not lengthen the request tail.

#### Scenario: List endpoint concurrency

- **WHEN** the gateway handles `GET /patients`
- **THEN** opd, lab, and disease batch calls MUST be awaited together via `asyncio.gather`
- **AND** the overall latency MUST be bounded by the slowest of the three, not their sum

#### Scenario: Upstream opd failure surfaces as 502

- **WHEN** svc-patient returns 5xx or connection error on `/opd/batch` (or `/opd/{id}`)
- **THEN** the gateway MUST return HTTP 502 with body `{"error": "upstream_unavailable", "service": "svc-patient"}`
- **AND** MUST NOT return a partial bundle

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

### Requirement: Every service SHALL emit a structured access-log line for every HTTP request

Each of the four FastAPI services (`gateway`, `svc-patient`, `svc-lab`, `svc-disease`) MUST log exactly one INFO-level access line per HTTP request once the response is produced. The line MUST contain, in this order, the fields `request_id`, `method`, `path`, `status`, `elapsed_ms`, `client`, `ua`, and `req_bytes`. The `ua` value MUST be wrapped in double quotes. Values that are unavailable (e.g., no peer address, missing `Content-Length`, missing `User-Agent`) MUST be rendered as the single character `-`. The line MUST be emitted regardless of whether the response status is 2xx, 4xx, or 5xx.

#### Scenario: Successful request produces an access-log line

- **WHEN** a client sends `GET /healthz` to any of the four services
- **THEN** that service MUST emit one INFO log line containing `method=GET path=/healthz status=200` along with non-empty `request_id` and `elapsed_ms` fields

#### Scenario: Failing request still produces an access-log line

- **WHEN** a client sends `GET /patients/does-not-exist` to the gateway and the gateway returns 404
- **THEN** the gateway MUST emit one access-log line with `status=404` for that request

#### Scenario: Missing User-Agent is rendered as a dash

- **WHEN** a request arrives without a `User-Agent` header
- **THEN** the access-log line MUST contain `ua="-"`

### Requirement: Every response SHALL carry an `X-Request-ID` header that matches the request's correlation id

Each service MUST read the inbound `X-Request-ID` header. If the header is present and non-empty, the service MUST reuse its value as the correlation id; otherwise the service MUST generate a new id (UUID4 hex). The chosen id MUST be stored on the request state, included in the access-log line, surfaced in any error response body produced by the catch-all handler, and echoed on the response via the `X-Request-ID` header.

#### Scenario: Client-supplied request id is preserved

- **WHEN** a client sends a request to any service with header `X-Request-ID: test-abc-123`
- **THEN** the response MUST include header `X-Request-ID: test-abc-123`
- **AND** the access-log line for that request MUST contain `request_id=test-abc-123`

#### Scenario: Missing request id is generated

- **WHEN** a client sends a request without `X-Request-ID`
- **THEN** the response MUST include an `X-Request-ID` header whose value is a non-empty string
- **AND** the access-log line MUST contain the same generated value

### Requirement: Gateway SHALL forward the request id to every downstream service call

When `gateway` fans out to `svc-patient`, `svc-lab`, or `svc-disease` while handling a request, it MUST include the request's correlation id in the `X-Request-ID` header of every outbound `httpx` call. Consequently, the access-log lines produced by all services involved in a single frontend request MUST share the same `request_id` value.

#### Scenario: Request id appears in every service's log for one fan-out

- **WHEN** a client sends `GET /patients/<known-id>` to the gateway with header `X-Request-ID: trace-xyz`
- **THEN** the gateway, svc-patient, svc-lab, and svc-disease MUST each emit an access-log line containing `request_id=trace-xyz`

### Requirement: Services SHALL return a structured 500 response for unhandled exceptions

Each service MUST register a catch-all exception handler for `Exception`. When a handler raises anything other than `HTTPException`, the service MUST respond with HTTP status 500 and a JSON body of the shape `{"error": "internal", "requestId": "<id>"}`, where `<id>` is the request's correlation id (or `"-"` if unavailable). The service MUST also log the failure at ERROR level with the full stack trace (via `log.exception`), including the request id and request path in the log message.

#### Scenario: Unhandled exception returns structured 500

- **WHEN** a request handler raises an unhandled `RuntimeError`
- **THEN** the service MUST respond with HTTP 500 and body `{"error": "internal", "requestId": "<id>"}` matching the request's correlation id
- **AND** the service MUST log an ERROR line that includes both the request id, the request path, and a traceback

#### Scenario: `HTTPException` is not affected by the catch-all

- **WHEN** a handler raises `HTTPException(status_code=404, detail={"error": "patient_not_found", "patientId": "x"})`
- **THEN** the response body MUST still be `{"error": "patient_not_found", "patientId": "x"}` with status 404 (existing behaviour preserved)

### Requirement: Log verbosity SHALL be configurable via the `LOG_LEVEL` environment variable

Each service MUST read `LOG_LEVEL` from the environment during startup and configure the root logger at that level. When the variable is unset, the level MUST default to `INFO`. Accepted values are the standard Python logging level names (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`), matched case-insensitively.

#### Scenario: Default level is INFO

- **WHEN** a service is started without setting `LOG_LEVEL`
- **THEN** access-log lines (INFO level) MUST appear in the process's log output

#### Scenario: WARNING level silences INFO access logs

- **WHEN** a service is started with `LOG_LEVEL=WARNING`
- **THEN** access-log lines MUST NOT appear in the process's log output
- **AND** WARNING and ERROR lines (e.g., gateway upstream failures, catch-all handler errors) MUST still appear
