#!/usr/bin/env bash
# Container entrypoint. SERVICE picks which FastAPI app uvicorn runs;
# `migrate` runs alembic upgrade head and exits (one-shot job pattern).
#
# Bind 0.0.0.0 inside the container — Kubernetes / docker-compose / etc.
# do the real network policy. --reload is dev-only and never enabled here.

set -euo pipefail

case "${SERVICE:-gateway}" in
  gateway)
    exec uvicorn gateway.app:app --host 0.0.0.0 --port "${PORT:-8000}" "$@"
    ;;
  svc-patient)
    exec uvicorn svc_patient.app:app --host 0.0.0.0 --port "${PORT:-8001}" "$@"
    ;;
  svc-lab)
    exec uvicorn svc_lab.app:app --host 0.0.0.0 --port "${PORT:-8002}" "$@"
    ;;
  svc-disease)
    exec uvicorn svc_disease.app:app --host 0.0.0.0 --port "${PORT:-8003}" "$@"
    ;;
  migrate)
    exec alembic upgrade head
    ;;
  seed)
    # mock-data isn't baked into the image; mount it at /app/mock-data.
    exec python /app/scripts/seed_from_json.py
    ;;
  shell)
    exec /bin/bash
    ;;
  *)
    echo "ERROR: unknown SERVICE='${SERVICE}'" >&2
    echo "Valid: gateway | svc-patient | svc-lab | svc-disease | migrate | seed | shell" >&2
    exit 64
    ;;
esac
