# syntax=docker/dockerfile:1.7
#
# One image, four entrypoints. SERVICE env var selects which FastAPI app
# uvicorn runs (see scripts/docker-entrypoint.sh). PostgreSQL is NOT in
# this image — point DATABASE_URL at an externally managed PG instance.
#
# Build (from repo root):
#     docker build -t my-project-backend backend/
# Run (gateway):
#     docker run --rm -p 8000:8000 \
#         -e DATABASE_URL=postgresql+asyncpg://gimc:gimc@db:5432/gimc \
#         -e GIMC_DATA_BACKEND=postgres \
#         -e SERVICE=gateway \
#         my-project-backend

# ───────── Stage 1: build venv with all five packages installed ─────────
FROM python:3.11-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

COPY shared       ./shared
COPY gateway      ./gateway
COPY svc-patient  ./svc-patient
COPY svc-lab      ./svc-lab
COPY svc-disease  ./svc-disease

# `shared` first so the four services resolve it from the venv, not from
# a sibling editable install.
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install ./shared && \
    /opt/venv/bin/pip install ./gateway ./svc-patient ./svc-lab ./svc-disease

# ───────── Stage 2: slim runtime ─────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    SERVICE=gateway

RUN useradd --create-home --shell /bin/bash --uid 1000 gimc

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

# Alembic config + migrations ride along so a one-shot container can run
# `SERVICE=migrate` against stage/prod databases.
COPY --chown=gimc:gimc alembic.ini  ./alembic.ini
COPY --chown=gimc:gimc alembic      ./alembic
COPY --chown=gimc:gimc scripts      ./scripts

RUN ln -s /app/scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh && \
    chmod +x /app/scripts/docker-entrypoint.sh

USER gimc

EXPOSE 8000 8001 8002 8003

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
