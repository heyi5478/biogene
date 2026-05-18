## 1. Backend — paginate the gateway condition-query

- [x] 1.1 In `backend/gateway/gateway/app.py`, change `condition_query`'s signature to add `limit: int = Query(50, ge=1, le=200)` and `offset: int = Query(0, ge=0)` parameters, and set `response_model=PatientListPage`
- [x] 1.2 Change the empty-conditions and empty-`combined` early returns to the envelope `{"items": [], "total": 0, "limit": limit, "offset": offset}`
- [x] 1.3 After computing `combined`, set `total = len(combined)`, order it deterministically (`sorted(combined)`), slice `page_ids = sorted(combined)[offset : offset + limit]`, and hydrate ONLY `page_ids` via `/patients/batch` and the `/opd/batch` `/labs/batch` `/diseases/batch` fan-out
- [x] 1.4 Return the envelope `{"items": items, "total": total, "limit": limit, "offset": offset}`

## 2. Backend tests

- [x] 2.1 Update the array-indexing tests in `backend/gateway/tests/test_condition_query.py` (`test_single_basic_diagnosis_condition`, `test_and_across_modules`, `test_or_across_modules`) to read `r.json()["items"]`
- [x] 2.2 Update `test_empty_conditions_returns_empty_list` to expect `{"items": [], "total": 0, "limit": 50, "offset": 0}`
- [x] 2.3 Add a pagination test: a broad condition with `?limit&offset` yields `items` ≤ `limit`, the full `total`, and disjoint consecutive pages
- [x] 2.4 Add an offset-past-end test (empty `items`, full `total`, status 200) and an invalid-params test (`limit=0`, `limit=5000`, `offset=-1` → 422)
- [x] 2.5 Run `cd backend && pytest` — all green

## 3. Frontend — service / hook / key layer

- [x] 3.1 In `src/services/patients.ts`, change `searchByConditions` to accept a `page` and return `PatientListPage`, building `limit`/`offset` query params from `PATIENT_PAGE_SIZE` (mirror `fetchPatients`); drop the now-unused `PatientListItem` import if eslint flags it
- [x] 3.2 In `src/hooks/queries/keys.ts`, add a `page` dimension to `queryKeys.patients.condition` → `['patients', 'condition', req, page ?? 1]`
- [x] 3.3 In `src/hooks/queries/usePatients.ts`, change `useConditionPatients` to `(req, page, enabled)`, key it with `queryKeys.patients.condition(req, page)`, and add `placeholderData: keepPreviousData`

## 4. Frontend — Index page + ConditionResults pager

- [x] 4.1 In `src/pages/Index.tsx`, add a `conditionPage` state, pass it into `useConditionPatients`, and derive `conditionResults` (the page `items`), `conditionTotal`, and `conditionPageCount`
- [x] 4.2 Reset `conditionPage` to 1 in `handleConditionSearch` and `handleConditionClear`, and via a `useEffect` keyed on the `conditionRequest` memo
- [x] 4.3 Pass `total` / `page` / `pageCount` / `onPageChange` into `<ConditionResults>`
- [x] 4.4 In `src/components/ConditionResults.tsx`, add the `total` / `page` / `pageCount` / `onPageChange` props; use `total` for the hit-count summary and the empty-state guard; render `<PatientListPager>` beneath the results table

## 5. Frontend — deferred-cohort notices

- [x] 5.1 Add a「僅供參考,僅含目前頁面」notice above `<CohortStatsPanel>` in the 族群統計 tab content
- [x] 5.2 Add a「僅供參考」caption near the 匯出比較報告 button and gate the button on `total > 0`
- [x] 5.3 Keep passing the current page's `matchedPatients` to `CohortStatsPanel` / `CohortExportDialog` unchanged — those two components are NOT edited in this change

## 6. Frontend tests

- [x] 6.1 Add a default `POST /patients/condition-query` handler returning the `{items,total,limit,offset}` envelope to `src/test/handlers.ts`
- [x] 6.2 Update `src/services/patients.test.ts` (`searchByConditions`) for the new `page` argument and the envelope return shape, including a later-page `offset` assertion
- [x] 6.3 Update `src/hooks/queries/usePatients.test.tsx` (`useConditionPatients`) for the new `page` argument and the envelope shape
- [x] 6.4 Run `cd frontend && npx vitest run`, then `npm run lint` / format / typecheck — all green

## 7. Verification

- [x] 7.1 `docker compose up -d --build`; curl `POST /patients/condition-query?limit=50&offset=0` with a broad condition (`性別 = 男`) → HTTP 200, `items` ≤ 50, full `total`, response < 1s (502 gone)
- [x] 7.2 Verify `?offset` past the end → empty `items` with full `total`; `?limit=0` / `?limit=5000` / `?offset=-1` → 422
- [x] 7.3 Browser 條件查詢 tab: a broad condition returns fast; the pager appears and navigates without a skeleton flash; editing a condition or submitting resets to page 1; the 族群統計 tab and 匯出 area show the「僅供參考」notice
- [ ] 7.4 Final confirmation on stage after deploy (staggered start — stage RAM is tight)
