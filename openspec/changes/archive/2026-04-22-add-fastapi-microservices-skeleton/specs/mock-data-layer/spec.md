## ADDED Requirements

### Requirement: load_mock.py SHALL expose a stable Python API for FastAPI services to consume

In addition to its existing CLI behavior, `backend/scripts/load_mock.py` MUST provide two importable functions with stable signatures:

- `load_all() -> dict[str, dict[str, list[dict]]]` — returns the full mock dataset keyed by `database_name -> table_name -> list_of_rows`
- `validate(data: dict | None = None) -> None` — when `data` is None, internally calls `load_all()`; raises `ValueError` (with offending file/row/field) if any FK constraint fails; returns `None` on success

These two functions MUST be importable as `from backend.shared.data_loader import load_all, validate` (the `shared` module re-exports them to decouple services from script layout).

#### Scenario: Service imports and validates at startup
- **WHEN** a FastAPI service executes `from backend.shared.data_loader import validate` during `lifespan` startup and calls `validate()`
- **THEN** the call MUST complete without exception on valid mock data
- **AND** MUST NOT require spawning a subprocess or parsing CLI output

#### Scenario: Service loads data once and caches in memory
- **WHEN** a service calls `load_all()` inside its `lifespan` context
- **THEN** the return value MUST be a plain Python `dict` that the service can keep as an in-process cache
- **AND** subsequent HTTP requests MUST NOT re-read JSON files from disk

#### Scenario: Validation failure raises typed error
- **WHEN** a sample row references a non-existent `patientId` and `validate()` is called
- **THEN** it MUST raise `ValueError` whose message identifies the database, table, row index, and offending key
- **AND** the existing CLI entrypoint (`python backend/scripts/load_mock.py`) MUST still exit non-zero as before
