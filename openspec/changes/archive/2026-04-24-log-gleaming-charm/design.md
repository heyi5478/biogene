# Design: log-gleaming-charm

## Context

The four FastAPI services currently share an identical minimal logging setup:

```python
log = logging.getLogger("<service>")
# ...
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
```

Only startup-time FK-validation messages and gateway upstream warnings are emitted. There is no request-level log, no request id, no catch-all exception handler, and level is hard-coded to INFO.

`shared/` currently contains only `schemas.py` (Pydantic models) and `data_loader.py` (thin re-export of `scripts/load_mock.py`) and declares a single dependency on `pydantic`. There is no existing logging or middleware helper to extend.

Gateway already wraps its `httpx` calls in `_get_json` / `_post_json` helpers and owns an `httpx.AsyncClient` managed by `lifespan`; request-id forwarding can be introduced by threading an optional `headers` kwarg through these helpers and the route functions.

The change is cross-cutting (touches `shared/` and all four services) and introduces a new dependency and a new env-var contract, which is why it warrants a design document.

## Goals / Non-Goals

**Goals:**
- Every HTTP request to any service produces one structured access-log line on completion.
- A single request id (UUID4 or client-supplied `X-Request-ID`) appears in the logs of every service that handled the request, including the three downstream services during a gateway fan-out.
- Unhandled exceptions in any handler are logged with full stack trace and returned to the client as `500 {"error": "internal", "requestId": "<id>"}`.
- One shared implementation used by all four services — no copy-paste.
- Log verbosity controllable via `LOG_LEVEL` env var without code changes.

**Non-Goals:**
- JSON-formatted logs (deferred; explicitly descoped after scope confirmation).
- Metrics / Prometheus / OpenTelemetry tracing.
- Log shipping to external systems (Loki, Datadog, CloudWatch).
- Refactoring the existing `StarletteHTTPException` passthrough handlers in gateway and svc-patient.
- Changing the 200 / 404 / 502 response shapes.
- Adding `exc_info` to the lifespan `ValueError` handler (the message already carries the full FK-violation list; a traceback would be noise).

## Decisions

### D1. Put the shared helpers in `shared/shared/logging.py`

New module exposing three functions:

```python
def configure_logging(service_name: str) -> logging.Logger
def install_middleware(app: FastAPI, log: logging.Logger) -> None
def install_exception_handlers(app: FastAPI, log: logging.Logger) -> None
```

Each service replaces its local `getLogger` + `basicConfig` lines with `log = configure_logging("<name>")` and calls the two `install_*` helpers after `app = FastAPI(...)`.

**Alternatives considered:**
- *Duplicate per service* — rejected: four copies of identical middleware drift over time.
- *Put in a new `backend/common/` sibling package* — rejected: `shared/` already exists, is already an editable-installed package consumed by all four services, and has the right blast radius.

### D2. `shared` depends on `fastapi>=0.110`

The middleware helper has to import `FastAPI`, `Request`, and `JSONResponse`. Every consumer already installs FastAPI, so the dependency is free at install time and makes the import explicit rather than duck-typed.

**Alternative considered:** *Accept `app` as `Any` and avoid the import* — rejected: loses IDE / type-checker support for no real gain.

### D3. Request ID: middleware generates if absent, handler forwards explicitly

Flow:
1. Middleware inspects incoming `X-Request-ID` header; if missing or empty, generates `uuid.uuid4().hex`.
2. Stores the value on `request.state.request_id`.
3. On response, sets `response.headers["X-Request-ID"]`.
4. Includes the id in the access-log line.

Gateway-specific forwarding: each route handler adds `request: Request` to its signature, reads `request.state.request_id`, and passes `headers={"X-Request-ID": rid}` into the existing `_get_json` / `_post_json` helpers (new optional kwarg). Downstream services' middleware will then see and log the same id.

**Alternatives considered:**
- *contextvars / automatic propagation* — rejected: adds complexity (reset semantics, async-safety); explicit parameter is five lines of plumbing and obvious at the call site.
- *Wrap `httpx.AsyncClient` with a default header* — rejected: the client is lifespan-scoped and shared across concurrent requests, so per-request defaults don't fit.

### D4. Access log fields

One log line per request, emitted after the response is produced, at INFO level:

```
request_id=<hex> method=GET path=/patients status=200 elapsed_ms=12.3 client=127.0.0.1 ua="curl/8.4" req_bytes=-
```

Field sources:
- `elapsed_ms`: `time.perf_counter()` delta, formatted to one decimal.
- `client`: `request.client.host` (may be `None` for unusual transports; print `-` in that case).
- `ua`: `request.headers.get("user-agent", "-")`, quoted to keep the field parseable.
- `req_bytes`: `request.headers.get("content-length", "-")`. **Not** derived by reading the body — reading would consume the stream before the handler runs.

### D5. Catch-all exception handler only catches `Exception`

Registered via `@app.exception_handler(Exception)`. FastAPI dispatches handlers by exception-type specificity, so existing `StarletteHTTPException` handlers in gateway and svc-patient continue to take precedence for `HTTPException` subclasses. svc-lab and svc-disease currently have no `StarletteHTTPException` handler and will keep using the FastAPI default for those.

**Response body**: `{"error": "internal", "requestId": "<id>"}` (pulled from `request.state.request_id` if available, else `"-"`).

**Logging**: `log.exception("unhandled error request_id=%s path=%s", rid, request.url.path)` — `log.exception` automatically includes the traceback.

### D6. `LOG_LEVEL` env var

`configure_logging` reads `os.getenv("LOG_LEVEL", "INFO").upper()` and passes it to `logging.basicConfig`. Invalid values raise `ValueError` from `logging.basicConfig`, which is acceptable fail-fast behaviour at startup.

**Alternative considered:** *Per-service env vars* (`GATEWAY_LOG_LEVEL`, ...) — rejected: four services in one repo, one knob is simpler; if divergence is ever needed later it can be added without breaking the default.

### D7. Gateway `_upstream_handler` keeps `log.warning`, gains `request_id`

Upstream failures are expected error paths, not programmer bugs, so a traceback is noise. The log line is extended to include `request_id=%s` so it correlates with the access log. Getting the id requires accepting `Request` in the handler signature — FastAPI exception handlers already receive it.

## Risks / Trade-offs

- **User-Agent may contain spaces / quotes in the log line** → Mitigation: wrap `ua` value in double quotes in the format string. For the POC scale this is acceptable; a structured-log upgrade (see Non-Goals) would replace string formatting entirely.
- **`request.client` can be `None`** (e.g., ASGI transports without a peer) → Mitigation: fall back to `-`.
- **Content-Length lies or is absent** for chunked requests → Mitigation: document the caveat; we use the header verbatim and print `-` when missing. We do not buffer the body to measure it.
- **Adding `fastapi` as a `shared` dep creates a cycle in spirit** (domain types + middleware bundled together) → Mitigation: acceptable at this scale; if `shared` ever needs to be consumed by non-FastAPI code, split into `shared-schemas` and `shared-web`.
- **Per-request log volume roughly doubles** (one line per service hop; a gateway request produces 4 access lines) → Mitigation: `LOG_LEVEL=WARNING` silences it in noisy environments.
- **`exc_info=True` in the catch-all during a storm of identical errors can flood logs** → Mitigation: accepted for now; rate-limiting is a future concern.
