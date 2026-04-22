#!/usr/bin/env bash
# Start all four FastAPI services in parallel for local development.
# Ctrl-C propagates to every child.
#
# Pre-req: each service's editable install is already in PATH's active
# Python environment. See backend/README.md for first-time setup.

set -euo pipefail

pids=()

trap 'echo; echo "Stopping..."; for p in "${pids[@]}"; do kill "$p" 2>/dev/null || true; done; wait 2>/dev/null || true' INT TERM EXIT

uvicorn svc_patient.app:app --host 127.0.0.1 --port 8001 --reload &
pids+=($!)

uvicorn svc_lab.app:app --host 127.0.0.1 --port 8002 --reload &
pids+=($!)

uvicorn svc_disease.app:app --host 127.0.0.1 --port 8003 --reload &
pids+=($!)

uvicorn gateway.app:app --host 127.0.0.1 --port 8000 --reload &
pids+=($!)

echo "svc-patient  -> http://127.0.0.1:8001"
echo "svc-lab      -> http://127.0.0.1:8002"
echo "svc-disease  -> http://127.0.0.1:8003"
echo "gateway      -> http://127.0.0.1:8000"
echo "Press Ctrl-C to stop."

wait
