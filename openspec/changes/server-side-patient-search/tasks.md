## 1. Operational prerequisites

- [x] 1.1 Confirm Postgres is up and the `gimc` schemas/tables exist (`PGPASSWORD=gimc psql -h localhost -U gimc -d gimc -c "\dt main.*"` shows ≥15 tables)
- [x] 1.2 Run `make -C backend seed-pg` and verify with `make -C backend verify-pg` (7-check parity passes)
- [x] 1.3 Write `GIMC_DATA_BACKEND=postgres` into `backend/.env`
- [x] 1.4 Stop any running JSON-mode dev session and restart `bash backend/scripts/dev.sh` + `cd frontend && npm run dev` against the PG-mode backend
- [x] 1.5 Smoke-check that `curl -s http://localhost:8000/patients | jq length` returns the expected patient count from PG

## 2. Backend — shared condition evaluator

- [x] 2.1 Create `backend/shared/shared/condition.py` exporting `eval_condition(record, field, op, value, value2) -> bool` and `match_records(records, field, op, value, value2) -> bool`. Port `ConditionResults.tsx:237-279` operator semantics one-to-one (all 11 operators)
- [x] 2.2 Create `backend/shared/tests/test_condition.py` with at least one positive and one negative case per operator (12 × 2 = 24 cases minimum); include parity cases against representative records from `backend/mock-data/db_main/{aa,biomarker,opd,patient}.json`
- [x] 2.3 Run `pytest backend/shared/tests/test_condition.py` — all green

## 3. Backend — shared schemas

- [x] 3.1 Add `PatientListItem(_Base)` to `backend/shared/shared/schemas.py` with: base patient fields (mirror existing `Patient` model), plus `dnabankCount: int`, `outbankCount: int`, `lastVisitDate: str | None = None`, `conditionHits: list[str] | None = None`
- [x] 3.2 Add `ConditionRow(_Base)` with `moduleId: str`, `fieldId: str`, `operator: str`, `value: str = ""`, `value2: str = ""`
- [x] 3.3 Add `ConditionRequest(_Base)` with `conditions: list[ConditionRow]`, `logic: Literal["AND", "OR"]`
- [x] 3.4 Add `ConditionMatchResponse(_Base)` with `conditionMatches: list[list[str]]` (parallel to inbound conditions; inner lists are patientIds)
- [x] 3.5 Re-export the new models from `backend/shared/shared/__init__.py` if other shared exports follow that pattern

## 4. Backend — svc-patient

- [x] 4.1 In `backend/svc-patient/svc_patient/app.py`, change `GET /patients` to accept `q: str | None = None`. When `q` is non-empty, filter `_patients_list` so only items whose `name` contains `q` (case-sensitive substring) **or** whose lowercased `chartno`/`externalChartno`/`nbsId` contains `q.lower()` are returned (mirror `Index.tsx:81-91`)
- [x] 4.2 Add `POST /patients/condition-match` accepting `ConditionRequest` and returning `ConditionMatchResponse`. For each inbound condition: if `moduleId == "basic"`, evaluate against `[patient]` for every `_patients_list` entry; if `moduleId == "opd"`, evaluate against `_opd_by_id[pid]` for every patient; otherwise return an empty list for that condition
- [x] 4.3 Add pytest in `backend/svc-patient/tests/` covering: list with `q=None`, list with matching `q`, list with non-matching `q`, condition-match with a `basic.diagnosis contains` condition, condition-match with a `basic` condition that nobody matches (returns empty), condition-match with a `moduleId` not owned by svc-patient (returns empty list for that condition)

## 5. Backend — svc-lab

- [x] 5.1 In `backend/svc-lab/svc_lab/app.py`, add `POST /labs/condition-match` accepting `ConditionRequest` and returning `ConditionMatchResponse`. For each inbound condition, route by `moduleId` to one of `_index["aa" | "msms" | "biomarker" | "outbank" | "dnabank"]`; iterate every patientId in that index and run `match_records`; collect matching patientIds. Conditions whose `moduleId` is not in the lab module set return an empty list
- [x] 5.2 Add pytest in `backend/svc-lab/tests/` covering: condition match for an `aa` text condition, a `biomarker` numeric `gt` condition, and a `moduleId` not owned by svc-lab (returns empty)

## 6. Backend — svc-disease

- [x] 6.1 In `backend/svc-disease/svc_disease/app.py`, add `POST /diseases/condition-match` accepting `ConditionRequest` and returning `ConditionMatchResponse`. Route by `moduleId` across the disease modules indexed in `_index` (the keys in `_ALL_OUTPUT_KEYS`). NBS sub-tables (`cah_tgal`, `dmd_tsh`) keep their existing parent-join structure; conditions on those modules evaluate against the joined parent rows
- [x] 6.2 Add pytest in `backend/svc-disease/tests/` covering: an `aadc.conc gt` condition, a `bd.result eq` condition, and a `moduleId` not owned by svc-disease (returns empty)

## 7. Backend — gateway list endpoint

- [x] 7.1 In `backend/gateway/gateway/app.py:list_patients`, accept `q: str | None = None` and forward `?q=` to `svc-patient` on the inbound `GET /patients` call
- [x] 7.2 Continue fanning out to `svc-patient /opd/batch`, `svc-lab /labs/batch`, and `svc-disease /diseases/batch` to compute `dnabankCount` (= `len(labs.dnabank)`), `outbankCount` (= `len(labs.outbank)`), and `lastVisitDate` (= `max(opd[*].visitDate)` or `None`). Project the merged data into `PatientListItem[]` — drop every module detail array before returning
- [x] 7.3 Update `response_model` to `list[PatientListItem]`
- [x] 7.4 Add pytest in `backend/gateway/tests/` (create the directory if needed) covering: list response shape (no module arrays present, summary fields present), list with `q` filtering through to svc-patient, single patient with no opd has `lastVisitDate=None`

## 8. Backend — gateway condition-query endpoint

- [x] 8.1 In `backend/gateway/gateway/app.py`, add `@app.post("/patients/condition-query", response_model=list[PatientListItem])` accepting `ConditionRequest`
- [x] 8.2 Group inbound `conditions` by which downstream service owns the `moduleId`: `basic`/`opd` → svc-patient, `aa`/`msms`/`biomarker`/`outbank`/`dnabank` → svc-lab, the rest → svc-disease. POST each subset to the corresponding `/condition-match` endpoint via `_post_json` in parallel via `asyncio.gather`
- [x] 8.3 For each of the original conditions, look up the per-service result (a list of patientIds) and convert to a `set[str]`. Combine across conditions with `set.intersection` (`logic == "AND"`) or `set.union` (`logic == "OR"`)
- [x] 8.4 Build `PatientListItem[]` for the final patientIds: re-use the same fan-out helper as the list endpoint, but limited to those ids. Attach `conditionHits` per row by iterating each matched condition and looking up the first matching record's value, formatted `{moduleCode}/{fieldLabel}={value}` (port `getHitSummary` from `ConditionResults.tsx:281-299` to Python; the module code/field label table can live in `shared/condition.py` or a small `shared/module_metadata.py`)
- [x] 8.5 Add pytest covering: empty conditions returns `[]`, single basic.diagnosis condition, AND across modules (basic + biomarker), OR across modules, downstream 5xx surfaces as 502, `conditionHits` populated correctly

## 9. Backend — verification

- [x] 9.1 `pytest backend/` — all green
- [x] 9.2 Manual smoke (recorded in PR description):
    - `curl 'http://localhost:8000/patients?q=陳' | jq length`
    - `curl 'http://localhost:8000/patients' | jq '.[0] | keys'` (no module arrays)
    - `curl -X POST http://localhost:8000/patients/condition-query -H 'Content-Type: application/json' -d '{"conditions":[{"moduleId":"basic","fieldId":"diagnosis","operator":"contains","value":"Fabry","value2":""}],"logic":"AND"}' | jq length`
    - `curl http://localhost:8000/patients/4e645243-fe58-5f74-b0bf-4271b5fdc0bf | jq 'keys | length'` (still 32+, full bundle)

## 10. Frontend — types

- [x] 10.1 In `frontend/src/types/patient.ts`, add the `PatientListItem` interface (base patient fields + `dnabankCount: number`, `outbankCount: number`, `lastVisitDate: string | null`, optional `conditionHits?: string[]`)
- [x] 10.2 In `frontend/src/types/medical.ts`, re-export `PatientListItem`
- [x] 10.3 Add a TS-level test (or compile-time assertion) that `PatientListItem` does NOT contain any module detail array property

## 11. Frontend — HTTP client and services

- [x] 11.1 Add `apiPost<T>(path, body, init?)` to `frontend/src/lib/api.ts` mirroring `apiGet` error handling (returns `Promise<T>`, throws `ApiError` on non-2xx, `status=0` on network failure). Sets `Content-Type: application/json` and serialises body via `JSON.stringify`
- [x] 11.2 In `frontend/src/services/patients.ts`, change `fetchPatients()` to `fetchPatients(q?: string): Promise<PatientListItem[]>`; URL-encode `q` and omit the query string entirely when `q` is `undefined` or empty
- [x] 11.3 Add `searchByConditions(req: ConditionRequest): Promise<PatientListItem[]>` in `frontend/src/services/patients.ts` calling `apiPost('/patients/condition-query', req)`
- [x] 11.4 Update `frontend/src/services/patients.test.ts` MSW handlers: support `?q=` on `GET /patients`, add `POST /patients/condition-query`, add `GET /patients/:id` (full bundle)
- [x] 11.5 Add MSW handler tests for `apiPost` happy/sad paths

## 12. Frontend — query keys and hooks

- [x] 12.1 Update `frontend/src/hooks/queries/keys.ts`: replace `patients.all` with `patients.list(q?: string)`, add `patients.condition(req)`. Keep `patients.detail(id)` and `patients.subResource(id, name)`
- [x] 12.2 Update `frontend/src/hooks/queries/usePatients.ts`: accept `q?: string`, key on `queryKeys.patients.list(q)`, set `staleTime: 5*60*1000` and `gcTime: 30*60*1000`
- [x] 12.3 Add `useConditionPatients(req: ConditionRequest, enabled: boolean)` in the same file (or a sibling), keying on `queryKeys.patients.condition(req)` with the same stale/gc times
- [x] 12.4 Update `frontend/src/hooks/queries/usePatients.test.tsx` to cover `q` propagation, `staleTime` (no refetch within window), and condition hook gating
- [x] 12.5 Verify `frontend/src/hooks/queries/usePatient.test.tsx` still green (this hook becomes a real caller now)

## 13. Frontend — Index page rewiring

- [x] 13.1 In `frontend/src/pages/Index.tsx`, replace `usePatients()` with `usePatients(submittedQuery)`. Remove the `.filter()` block at lines 81-91; `results` is now `patients ?? []` (or `[]` if `submittedQuery` is empty, to preserve the "開始查詢" empty state)
- [x] 13.2 Replace `selectedPatient: Patient | null` state with `selectedPatientId: string | null`. Wire `usePatient(selectedPatientId)` to obtain the bundle for `PatientSummary` / `ResultModules`. When the search returns exactly one item, auto-set `selectedPatientId` to that item's `patientId`
- [x] 13.3 Render a loading placeholder (Skeleton) while `usePatient` is pending after a selection
- [x] 13.4 Replace `evaluateConditions(patients ?? [], conditions, conditionLogic)` with `useConditionPatients({conditions, logic: conditionLogic}, conditionSubmitted)`. `conditionResults` is the hook's resolved `data ?? []`
- [x] 13.5 Apply the same id-based selection pattern in condition mode: `conditionPatientId: string | null` + `usePatient(conditionPatientId)`

## 14. Frontend — leaf component prop changes

- [x] 14.1 In `frontend/src/components/PatientList.tsx`, change `patients: Patient[]` → `patients: PatientListItem[]`, change `onSelect: (patient: Patient) => void` → `onSelect: (patientId: string) => void`, update the click handler to call `onSelect(p.patientId)`
- [x] 14.2 In `frontend/src/components/ConditionResults.tsx`, change `MatchedPatient.patient` from `Patient` to `PatientListItem`; change `onSelectPatient: (p: Patient) => void` → `onSelectPatient: (id: string) => void`. Update `onClick={() => onSelectPatient(patient)}` → `onSelectPatient(patient.patientId)`
- [x] 14.3 In `frontend/src/components/ConditionResults.tsx`, delete `getModuleData`, `evalCondition`, `getHitSummary`, and `evaluateConditions` (lines 189-335). Render `hitSummary` from `patient.conditionHits ?? []` instead
- [x] 14.4 In `frontend/src/components/PatientSummary.tsx`, leave `Patient` prop type unchanged. The component only renders after `usePatient(id)` resolves so module arrays are guaranteed
- [x] 14.5 In `frontend/src/components/CohortStatsPanel.tsx` and `CohortExportDialog.tsx` (if they currently take `Patient[]`): they may need to switch to `PatientListItem[]` since `ConditionResults` no longer holds full `Patient` objects. If a stat/export needs detail, fetch detail per id; otherwise drop the dependency on module arrays (verify by reading the components — adjust scope if either currently reads module arrays)

## 15. Frontend — UI verification

- [x] 15.1 `npm run typecheck` clean
- [x] 15.2 `npm test` (vitest) all green
- [x] 15.3 `npm run test:e2e` (Playwright) — `patient-search-by-name.spec.ts` should pass unchanged
- [x] 15.4 Add `frontend/tests/patient-search-by-condition.spec.ts`: open page, switch to condition mode, configure `basic / diagnosis / contains / "Fabry"`, click search, assert at least one patient row appears with the `Fabry` diagnosis visible
- [x] 15.5 Manual chrome-devtools MCP smoke: load `http://localhost:8080`, observe `GET /patients` baseline payload size shrunk to ~3-5 KB; type `陳` + search → see a new `GET /patients?q=陳` request; click the resulting patient → see `GET /patients/{id}`; switch to condition mode + Fabry condition → see `POST /patients/condition-query`

## 16. Cleanup and docs

- [x] 16.1 Update `README.md` "Smoke Tests" section: replace the `curl /patients | jq 'length'` example with one that demonstrates the slim list and the `?q=` flag; add an example for `POST /patients/condition-query`
- [x] 16.2 Confirm no dead exports remain (`evaluateConditions` re-exported anywhere?) — `grep -r "evaluateConditions" frontend/src` should match nothing after this change
- [x] 16.3 Confirm `queryKeys.patients.all` is no longer referenced (`grep -r "patients\.all" frontend/src` should match nothing after this change)
