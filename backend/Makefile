# my-project backend developer targets.
#
# Run from `backend/` (or use `make -C backend <target>` from repo root).
# Most targets shell out to the venv-pinned executables; activate the venv
# first or rely on the explicit path used here.

VENV    ?= .venv
PYTHON  ?= $(VENV)/bin/python3
ALEMBIC ?= $(VENV)/bin/alembic
PIP     ?= $(VENV)/bin/pip

.PHONY: help install seed-pg alembic-up alembic-check verify-pg

help:
	@echo "Targets:"
	@echo "  install        Install/refresh editable packages into $(VENV)"
	@echo "  alembic-up     Apply pending migrations (alembic upgrade head)"
	@echo "  alembic-check  Diff metadata against DB; non-zero on drift"
	@echo "  seed-pg        Load mock-data JSON into the gimc database"
	@echo "  verify-pg      Run backend/etl/verify.py against gimc"

install:
	$(PIP) install -e shared
	$(PIP) install -e gateway
	$(PIP) install -e svc-patient
	$(PIP) install -e svc-lab
	$(PIP) install -e svc-disease

alembic-up:
	$(ALEMBIC) upgrade head

# Confirm the live DB matches the SQLAlchemy declarative metadata.
# alembic --autogenerate exits 0 either way, so we capture the output and
# fail if it contains any "Detected" lines (added/removed/altered).
alembic-check:
	@TMP=$$(mktemp); \
	$(ALEMBIC) check 2>&1 | tee "$$TMP"; \
	rc=$$?; \
	rm -f "$$TMP"; \
	exit $$rc

seed-pg:
	$(PYTHON) scripts/seed_from_json.py

verify-pg:
	$(PYTHON) etl/verify.py
