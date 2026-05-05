# Backend — FastAPI microservices

Four FastAPI processes back the frontend. The gateway on port 8000 is the
only service the browser talks to; it fans out to three internal services
that read either the JSON fixtures under `backend/mock-data/` (dev default)
or the alembic-managed `gimc` PostgreSQL database. The `GIMC_DATA_BACKEND`
env var picks which — see `.env.example`.

| Service       | Port | Role                                                   | Python package |
| ------------- | ---- | ------------------------------------------------------ | -------------- |
| `gateway`     | 8000 | Frontend-facing; CORS, aggregation, fan-out via httpx  | `gateway`      |
| `svc-patient` | 8001 | Merged patient base records (all three databases)       | `svc_patient`  |
| `svc-lab`     | 8002 | AA / MS-MS / biomarker / outbank / dnabank             | `svc_lab`      |
| `svc-disease` | 8003 | AADC / ALD / MMA / MPS2 / LSD / enzyme / GAG + NBS screens | `svc_disease` |

## One-time setup

Python 3.10+. Run from the repo root:

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -U pip
pip install -e backend/shared
pip install -e backend/gateway
pip install -e backend/svc-patient
pip install -e backend/svc-lab
pip install -e backend/svc-disease
```

Each service has its own `pyproject.toml` and depends on `shared` as a
sibling editable install. The `shared` package holds the Pydantic response
schemas (`schemas.py`), the SQLAlchemy 2.0 declarative models (`models/`),
the async + sync engine helpers (`db.py`), and the dual-backend `data_loader`
facade (JSON via `scripts/load_mock.py` or PG via `shared.db`).

## Makefile targets

`backend/Makefile` is the canonical entry point for dev workflows. Run from
repo root with `make -C backend <target>`, or `cd backend/` first:

| Target | Purpose |
| --- | --- |
| `install` | `pip install -e` all five packages into the active venv |
| `alembic-up` | `alembic upgrade head` — apply pending migrations |
| `alembic-check` | Diff `metadata` against the live DB; non-zero on drift |
| `seed-pg` | Load `mock-data/` into PG via `scripts/seed_from_json.py` |
| `verify-pg` | Run `etl/verify.py`'s 7-check parity suite against `gimc` |

`alembic-up` / `seed-pg` / `verify-pg` require `DATABASE_URL` to point at a
reachable PostgreSQL instance. `setup-postgres.sh` provisions one locally;
`docker-compose.yml` provisions one in a container.

## Running

Start all four services in parallel from the repo root:

```bash
bash backend/scripts/dev.sh
```

`Ctrl-C` propagates to every child. To run a single service by hand:

```bash
uvicorn gateway.app:app     --host 127.0.0.1 --port 8000 --reload
uvicorn svc_patient.app:app --host 127.0.0.1 --port 8001 --reload
uvicorn svc_lab.app:app     --host 127.0.0.1 --port 8002 --reload
uvicorn svc_disease.app:app --host 127.0.0.1 --port 8003 --reload
```

At startup every service calls `shared.data_loader.validate()` to check FK
integrity — for the JSON backend this is an in-memory sweep over the
mock-data dicts; for the PG backend it's a per-sample-table
`LEFT JOIN … IS NULL` query. On the first violation the service logs the
offending row and exits non-zero before binding its port.

## Endpoints — frontend view (gateway only)

```bash
# Full patient bundle list
curl -s http://localhost:8000/patients | jq 'length'

# One patient, aggregated
curl -s http://localhost:8000/patients/4e645243-fe58-5f74-b0bf-4271b5fdc0bf | jq '.aa | length'

# Healthcheck
curl -s http://localhost:8000/healthz
```

## Endpoints — internal services

```bash
# svc-patient
curl -s http://localhost:8001/patients | jq 'length'
curl -s http://localhost:8001/patients/4e645243-fe58-5f74-b0bf-4271b5fdc0bf

# svc-lab (single + bulk)
curl -s http://localhost:8002/labs/4e645243-fe58-5f74-b0bf-4271b5fdc0bf
curl -s -X POST http://localhost:8002/labs/batch \
     -H 'content-type: application/json' \
     -d '{"patientIds":["4e645243-fe58-5f74-b0bf-4271b5fdc0bf"]}'

# svc-disease (single + bulk)
curl -s http://localhost:8003/diseases/4e645243-fe58-5f74-b0bf-4271b5fdc0bf
curl -s -X POST http://localhost:8003/diseases/batch \
     -H 'content-type: application/json' \
     -d '{"patientIds":["4e645243-fe58-5f74-b0bf-4271b5fdc0bf"]}'
```

## CORS

The gateway is the only service configured for CORS; it allows origin
`http://localhost:5173` (Vite dev server). The three internal services
have no CORS middleware — browser calls to them are blocked by design.
Override the origin by setting `GATEWAY_CORS_ORIGIN` before starting the
gateway.

## Error model

* `404` from `GET /patients/{id}` — body `{"error": "patient_not_found", "patientId": "<id>"}`
* `502` when any downstream service fails — body `{"error": "upstream_unavailable", "service": "<name>"}`
  (the gateway never returns a partial bundle; fail-fast).

## Mock-data CLI

Run the bare validator without starting any service:

```bash
python3 backend/scripts/load_mock.py
```

Exits non-zero and prints the offending file / row / patientId on any FK
violation.

## Docker

The backend ships as a single multi-stage image — one image, one venv, all
four services + alembic + the seed script. The `SERVICE` env var picks
which entrypoint runs at container start (see `scripts/docker-entrypoint.sh`).

```bash
# Build (run from repo root)
docker build -t my-project-backend backend/

# Gateway
docker run --rm -p 8000:8000 \
    -e DATABASE_URL=postgresql+asyncpg://gimc:gimc@db:5432/gimc \
    -e GIMC_DATA_BACKEND=postgres \
    -e SERVICE=gateway \
    my-project-backend

# Migration (one-shot — exits when alembic upgrade head completes)
docker run --rm \
    -e DATABASE_URL=postgresql+asyncpg://gimc:gimc@db:5432/gimc \
    -e SERVICE=migrate \
    my-project-backend
```

Valid `SERVICE` values: `gateway`, `svc-patient`, `svc-lab`, `svc-disease`,
`migrate`, `seed` (one-shot mock-data load — requires `mock-data/` mounted
at `/app/mock-data`), `shell` (drops to bash for debugging).

For full-stack orchestration (PG + migrate + 4 services + frontend) use the
top-level [`docker-compose.yml`](../docker-compose.yml) instead of running
containers by hand.
