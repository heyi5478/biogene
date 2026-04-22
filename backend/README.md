# Backend — FastAPI microservices

Four FastAPI processes back the frontend. The gateway on port 8000 is the
only service the browser talks to; it fans out to three internal services
loaded with the JSON mock data under `backend/mock-data/`.

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
sibling editable install — the shared package contains `schemas.py` and the
`data_loader` thin wrapper over `backend/scripts/load_mock.py`.

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

At startup every service calls `shared.data_loader.validate()` which walks
the mock-data JSON files and checks FK integrity. On failure the service
logs the offending row and exits non-zero before binding its port.

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
