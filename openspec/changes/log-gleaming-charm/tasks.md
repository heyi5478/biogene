## 1. Shared logging module

- [x] 1.1 Add `fastapi>=0.110` to `dependencies` in `backend/shared/pyproject.toml`
- [x] 1.2 Create `backend/shared/shared/logging.py` exporting `configure_logging`, `install_middleware`, and `install_exception_handlers`
- [x] 1.3 Implement `configure_logging(service_name)` — reads `LOG_LEVEL` (default `INFO`, case-insensitive), calls `logging.basicConfig` with the existing `%(asctime)s %(name)s %(levelname)s %(message)s` format, returns `logging.getLogger(service_name)`
- [x] 1.4 Implement `install_middleware(app, log)` — single `@app.middleware("http")` that (a) derives `request_id` from `X-Request-ID` or generates `uuid.uuid4().hex`, (b) stores it on `request.state.request_id`, (c) times the call with `time.perf_counter()`, (d) sets `response.headers["X-Request-ID"]`, (e) emits the access-log line with fields `request_id method path status elapsed_ms client ua req_bytes` (unavailable values printed as `-`, `ua` wrapped in double quotes)
- [x] 1.5 Implement `install_exception_handlers(app, log)` — register `@app.exception_handler(Exception)` that calls `log.exception("unhandled error request_id=%s path=%s", rid, request.url.path)` and returns `JSONResponse(500, {"error": "internal", "requestId": rid or "-"})`
- [x] 1.6 Reinstall the shared package so the new dependency is picked up: `pip install -e backend/shared` inside the backend venv

## 2. Wire services into the shared helpers

- [x] 2.1 `backend/svc-patient/svc_patient/app.py` — replace the local `logging.getLogger(...)` + `logging.basicConfig(...)` lines with `log = configure_logging("svc-patient")`; call `install_middleware(app, log)` and `install_exception_handlers(app, log)` right after `app = FastAPI(...)`
- [x] 2.2 `backend/svc-lab/svc_lab/app.py` — same treatment with `configure_logging("svc-lab")`
- [x] 2.3 `backend/svc-disease/svc_disease/app.py` — same treatment with `configure_logging("svc-disease")`
- [x] 2.4 `backend/gateway/gateway/app.py` — same treatment with `configure_logging("gateway")`, keeping the existing `StarletteHTTPException` and `_Upstream502` handlers in place
- [x] 2.5 Confirm all four services still start via `bash backend/scripts/dev.sh` and print their existing startup messages (`mock-data FK validation passed`, `indexed ...`)

## 3. Gateway request-id forwarding

- [x] 3.1 In `backend/gateway/gateway/app.py`, add an optional `headers: dict | None = None` kwarg to `_get_json` and `_post_json`, passing it through to `client.get` / `client.post`
- [x] 3.2 Add `request: Request` parameter to `list_patients` and `get_patient`; build `headers = {"X-Request-ID": request.state.request_id}` and pass to every downstream call inside those handlers
- [x] 3.3 Update `_upstream_handler` to include `request_id=<rid>` in its warning log line (pull from `request.state.request_id` with a `-` fallback)

## 4. Verification

- [x] 4.1 Start the stack (`bash backend/scripts/dev.sh`) and hit `GET http://127.0.0.1:8000/healthz`; confirm one access-log line appears in the gateway terminal containing `method=GET path=/healthz status=200` and a non-empty `request_id`
- [x] 4.2 Send `curl -H "X-Request-ID: trace-xyz" http://127.0.0.1:8000/patients/<known-id>`; confirm the same `request_id=trace-xyz` appears in the gateway, svc-patient, svc-lab, and svc-disease terminals, and the response includes header `X-Request-ID: trace-xyz`
- [x] 4.3 Temporarily add `raise RuntimeError("boom")` to a route handler; confirm the response is `500 {"error": "internal", "requestId": "<id>"}` and the terminal shows an ERROR line with a traceback; revert the temporary change
- [x] 4.4 Restart with `LOG_LEVEL=WARNING bash backend/scripts/dev.sh`; hit `/healthz`; confirm no INFO access-log line appears
- [x] 4.5 Stop `svc-lab` and call `GET /patients/<known-id>`; confirm 502 with `{"error": "upstream_unavailable", "service": "svc-lab"}` and the gateway log shows the upstream warning containing `request_id=...`
- [x] 4.6 Call `GET /patients/does-not-exist`; confirm the response is still `404 {"error": "patient_not_found", "patientId": "does-not-exist"}` (existing behaviour preserved)
- [x] 4.7 Run `python -m unittest backend.shared.tests.test_data_loader` and confirm it passes
