## Why

`GET /patients` returns the entire patient table (~40k rows cached today, ~184k in the database) in a single unpaginated response. Serializing it exceeds the gateway's 5s upstream timeout, so every patient query — including the unfiltered list that loads on page open — fails with `502 upstream_unavailable`. Patient search is currently unusable on staging.

## What Changes

- **BREAKING**: `GET /patients` (gateway and svc-patient) returns a paginated envelope `{items, total, limit, offset}` instead of a bare `PatientListItem[]` array. Callers MUST read `.items`.
- `GET /patients` accepts `limit` (default 50, max 200) and `offset` (default 0) query parameters. `q` filtering is applied before the page slice; the response reports `total` — the full filtered count, not the page size.
- New endpoint `POST /patients/batch` on svc-patient resolves patient base rows by id list, so the gateway's `condition-query` no longer fetches the whole table to resolve matched patients.
- The gateway's `POST /patients/condition-query` external contract is unchanged (still returns `PatientListItem[]` of all matches); only its internal base-row resolution switches from a full `GET /patients` to `POST /patients/batch`.
- Frontend: `fetchPatients`, `usePatients`, and the `queryKeys.patients.list` key gain pagination parameters; a new `PatientListPage` type is added; `usePatients` gains an `enabled` guard so it no longer fetches the full table on mount before any search is submitted.
- The Index page renders a pagination control (Prev/Next + numbered pages + ellipsis) for multi-page results, and derives the result-count summary and single-result auto-selection from the envelope `total`.

## Capabilities

### New Capabilities

_None — pagination modifies existing capabilities rather than introducing a new one._

### Modified Capabilities

- `backend-api`: `GET /patients` (gateway + svc-patient) becomes a paginated envelope with `limit`/`offset`/`total`; the `q`-search and svc-patient list scenarios are updated for paging; a new requirement covers `POST /patients/batch`.
- `frontend-api-client`: `fetchPatients`, `usePatients`, the `queryKeys.patients.list` key, and the patient types module gain pagination parameters and the `PatientListPage` envelope shape; `usePatients` becomes disabled until a non-empty query is submitted.
- `frontend-patient-data`: the Index page consumes paged results, renders a pagination control for multi-page result sets, and derives the result-count summary and single-result auto-selection from the envelope `total`.

## Impact

- **APIs (BREAKING wire-format change)**: `GET /patients` on the gateway and on svc-patient; new `POST /patients/batch` on svc-patient.
- **Backend code**: `backend/shared/shared/schemas.py` (new `PatientPage`, `PatientListPage`); `backend/svc-patient/svc_patient/app.py` (`GET /patients`, new `POST /patients/batch`); `backend/gateway/gateway/app.py` (`GET /patients`, `condition-query` base-row resolution).
- **Frontend code**: `src/types/patient.ts`, `src/services/patients.ts`, `src/hooks/queries/usePatients.ts`, `src/hooks/queries/keys.ts`, `src/pages/Index.tsx`, `src/components/PatientList.tsx`; new `src/components/PatientListPager.tsx` (wraps the existing unused `src/components/ui/pagination.tsx`).
- **Tests**: backend `test_list_patients.py`, `test_search_and_condition.py` (plus new paging cases and `test_batch_patients.py`); frontend `services/patients.test.ts`, `hooks/queries/usePatients.test.tsx`, `src/test/handlers.ts`, plus a new pager unit test and an E2E spec.
- **No dependency changes**; the gateway httpx timeout and container configuration are unchanged.
- **Rollout note**: on redeploy svc-patient loads ~184k rows at startup (vs ~40k today) — startup time and the ~843 MiB container memory limit are worth watching. Re-architecting the in-memory cache is out of scope for this change.
