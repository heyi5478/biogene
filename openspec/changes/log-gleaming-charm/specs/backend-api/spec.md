# backend-api — log-gleaming-charm delta

## ADDED Requirements

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
