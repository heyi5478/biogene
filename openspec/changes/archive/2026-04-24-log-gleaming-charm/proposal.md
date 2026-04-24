# Proposal: log-gleaming-charm

## Why

Backend runtime observability is effectively a black box. The four FastAPI services (`gateway`, `svc-patient`, `svc-lab`, `svc-disease`) only log startup-time FK validation and gateway upstream warnings — no HTTP access log, no stack traces on unhandled errors, no way to correlate a single frontend request across the four services. Debugging any failure that escapes startup requires guesswork, and any non-`HTTPException` raised inside a handler is silently swallowed into a generic 500.

## What Changes

- Add HTTP access-log middleware to every service, recording `request_id`, `method`, `path`, `status`, `elapsed_ms`, `client` (IP), `ua` (User-Agent), and `req_bytes` (Content-Length).
- Generate an `X-Request-ID` per request (honour the inbound header if present) and echo it in the response header; `gateway` forwards it to downstream services so a single request id appears in all four services' logs.
- Add a catch-all `Exception` handler that logs with `log.exception(...)` (full stack trace) and returns `500 {"error": "internal", "requestId": "<id>"}`. Existing `StarletteHTTPException` handlers (gateway, svc-patient) are preserved.
- Introduce `LOG_LEVEL` environment variable (default `INFO`) replacing the hard-coded `logging.basicConfig(level=logging.INFO, ...)` in every service.
- Centralise the middleware, logger configuration, and exception-handler helpers in a new `shared/shared/logging.py` module so the four services share one implementation.
- Add `fastapi>=0.110` to the `shared` package's dependencies (needed by the middleware helper; all four consumers already have it).

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `backend-api`: requirements added for structured access logging, request-id propagation, catch-all exception handling, and `LOG_LEVEL` configuration.

## Impact

- **Code**:
  - New: `backend/shared/shared/logging.py`.
  - Modified: `backend/shared/pyproject.toml` (add `fastapi>=0.110`).
  - Modified: `backend/gateway/gateway/app.py`, `backend/svc-patient/svc_patient/app.py`, `backend/svc-lab/svc_lab/app.py`, `backend/svc-disease/svc_disease/app.py` — swap the local `logging.basicConfig` for the shared helpers and (gateway only) forward `X-Request-ID` through `httpx`.
- **APIs**: all responses gain an `X-Request-ID` header; 500 responses change shape from FastAPI default `{"detail": ...}` to `{"error": "internal", "requestId": "<id>"}`. Existing 200/404/502 shapes are unchanged.
- **Dependencies**: `shared` now depends on `fastapi` (already transitively present in every consumer's venv, so no net install cost).
- **Ops**: new env var `LOG_LEVEL`; log volume increases by one line per request per service hop.
- **Tests**: `backend/shared/tests/test_data_loader.py` is unaffected; no existing test covers logging behaviour.
