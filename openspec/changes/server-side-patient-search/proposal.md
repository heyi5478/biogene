## Why

Today the gateway's `GET /patients` returns every patient with all 14 module sub-arrays inlined (~22 KB per response, 32 top-level keys per patient), and both search modes filter purely in the browser — `Index.tsx` runs `.filter()` for the patient query and `ConditionResults.evaluateConditions` walks 11 operators across the full bundle for the condition query. Measured on the 13-patient mock dataset, ~88% of every list payload is module detail the search itself never reads. The design will not scale beyond the current dataset, makes the patient list endpoint disproportionately expensive, and leaves `GET /patients/{id}` (and the matching `usePatient` hook) wired up but unreachable from the UI. We are reshaping the search API now so search work moves to the server before the dataset grows past mock size.

## What Changes

- **BREAKING** `GET /patients` response shape changes from "full bundle list" to a slim `PatientListItem[]` (base fields plus `dnabankCount`, `outbankCount`, `lastVisitDate`); module detail arrays are removed from this endpoint.
- **BREAKING** `GET /patients` accepts `?q=<text>` and filters on `name`, `chartno`, `externalChartno`, `nbsId` server-side; an absent `q` returns the full unfiltered list.
- Add `POST /patients/condition-query` accepting `{conditions[], logic: "AND"|"OR"}` and returning `PatientListItem[]` with per-row `conditionHits[]`.
- Add inter-service `POST /{patients,labs,diseases}/condition-match` endpoints that take a `ConditionRequest` and return the patient-id sets matched by each condition; gateway combines them via AND (intersection) / OR (union).
- Wire the existing `GET /patients/{id}` endpoint into the UI: `PatientList` and `ConditionResults` row clicks now select an id and `usePatient(id)` fetches the full bundle on demand.
- Frontend search becomes server-driven: `Index.tsx` no longer runs `.filter()` or `evaluateConditions`; `usePatients(q)` and `useConditionPatients(req)` own list data; `ConditionResults` no longer owns the evaluation engine.
- Postgres becomes the operational data backend (`GIMC_DATA_BACKEND=postgres` after `make seed-pg`); JSON mode remains supported because the dual-backend bit-equal contract from `postgres-data-backend` is unchanged — service code reads from in-memory caches loaded by `data_loader.load_all` regardless of backend.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `backend-api`: list endpoint shape is slim instead of full bundle; new `q` query parameter and `POST /patients/condition-query` endpoint; new internal `condition-match` endpoints on each downstream service.
- `frontend-api-client`: service layer gains a `q` parameter and a condition-search call; React Query hooks accept search inputs and key on them; `apiPost` is added to `lib/api.ts`; query-key conventions distinguish list (with `q`) from condition queries from detail.
- `frontend-patient-data`: Index page no longer client-filters and no longer ships the full patient list to `ConditionResults`; the in-component condition evaluation engine is removed; selection flow goes through `patientId` and a detail fetch instead of passing the full object.

## Impact

- Backend: `backend/gateway/gateway/app.py`, `backend/svc-patient/svc_patient/app.py`, `backend/svc-lab/svc_lab/app.py`, `backend/svc-disease/svc_disease/app.py`, `backend/shared/shared/schemas.py`; new `backend/shared/shared/condition.py` with the 11-operator evaluator (Python port of `ConditionResults.tsx:237-279`).
- Frontend: `frontend/src/lib/api.ts`, `frontend/src/services/patients.ts`, `frontend/src/hooks/queries/{keys,usePatients,usePatient}.ts`, `frontend/src/pages/Index.tsx`, `frontend/src/components/{PatientList,PatientSummary,ConditionResults}.tsx`, `frontend/src/types/patient.ts`.
- Tests: MSW mocks in `frontend/src/services/patients.test.ts` and `hooks/queries/*.test.tsx`; new Playwright `frontend/tests/patient-search-by-condition.spec.ts`; new backend pytest suites under `backend/{shared,svc-*,gateway}/tests`.
- Operations: requires `make -C backend seed-pg` once and `GIMC_DATA_BACKEND=postgres` in `backend/.env` (PG schema is already migrated, but the three `patient` tables are currently empty).
- Consumers: any external client of `GET /patients` that depended on inlined module arrays must switch to `GET /patients/{id}`. No such consumer is known besides the SPA.
