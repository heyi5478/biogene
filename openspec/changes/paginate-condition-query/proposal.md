## Why

`POST /patients/condition-query` returns the full set of matched patients in a single unpaginated response. A broad condition (e.g. `性別 = 男`, ~90k of ~184k patients) makes the gateway hydrate every match — ~5.5MB batch bodies that svc-patient takes 80–155s to serialize — far past the gateway's 5s upstream timeout, so the 條件查詢 tab fails with `502 upstream_unavailable` and the abandoned job blocks svc-patient's single worker. The archived `paginate-patient-query` change explicitly deferred this case; this change closes that gap.

## What Changes

- **BREAKING**: `POST /patients/condition-query` (gateway) returns a paginated envelope `{items, total, limit, offset}` (`PatientListPage`) instead of a bare `PatientListItem[]`. Callers MUST read `.items`.
- The endpoint accepts `limit` (default 50, max 200) and `offset` (default 0) query parameters. The gateway still computes the full match set and reports `total` (the full hit count), but orders it deterministically and hydrates only the `[offset:offset+limit]` slice — every downstream batch body is bounded to ≤ `limit` ids, keeping each call inside the 5s timeout.
- Frontend: `searchByConditions`, `useConditionPatients`, and the `queryKeys.patients.condition` key gain a page parameter; `useConditionPatients` gains `placeholderData: keepPreviousData`.
- The Index page threads a `conditionPage` state, and `ConditionResults` renders the existing `PatientListPager` for multi-page condition results; the matched-count summary reflects `total`.
- **Interim degradation (deferred):** the 族群統計 tab and the 匯出比較報告 dialog now operate on the **current results page only**, not the full matched cohort. Each gains a「僅供參考,僅含目前頁面」notice. A proper cohort-wide statistics/export path is out of scope here and deferred to a follow-up change.

## Capabilities

### New Capabilities

_None — pagination modifies existing capabilities rather than introducing a new one._

### Modified Capabilities

- `backend-api`: `POST /patients/condition-query` becomes a paginated `{items, total, limit, offset}` envelope, accepts `limit`/`offset` query parameters, and orders the match set deterministically before slicing.
- `frontend-api-client`: `searchByConditions` gains a `page` parameter and returns `PatientListPage`; `useConditionPatients` gains a `page` parameter plus `keepPreviousData`; `queryKeys.patients.condition` gains a page dimension.
- `frontend-patient-data`: the Index page sources condition results from `useConditionPatients(req, conditionPage, …)` and reads the resolved page's `items`; the pagination-control requirement extends to condition-query mode.
- `cohort-statistics`: the 族群統計 tab now receives only the current results page (interim) and MUST render a「僅供參考,僅含目前頁面」notice; cohort-size wording is scoped to the current page.
- `cohort-export`: the 匯出比較報告 entry point is gated on `total` rather than the page length, the dialog receives only the current results page (interim), and a「僅供參考」notice is shown.

## Impact

- **API (BREAKING wire-format change)**: `POST /patients/condition-query` on the gateway.
- **Backend code**: `backend/gateway/gateway/app.py` (`condition_query`). No `shared/schemas.py` change — `PatientListPage` is reused as-is. No svc-patient change; the gateway's 5s httpx timeout is unchanged.
- **Frontend code**: `src/services/patients.ts`, `src/hooks/queries/usePatients.ts`, `src/hooks/queries/keys.ts`, `src/pages/Index.tsx`, `src/components/ConditionResults.tsx`. Reuses the existing `PatientListPager`. `CohortStatsPanel` / `CohortExportDialog` are not modified — only the data they receive and the added notices.
- **Tests**: backend `backend/gateway/tests/test_condition_query.py` (envelope shape + new paging cases); frontend `src/services/patients.test.ts`, `src/hooks/queries/usePatients.test.tsx`, `src/test/handlers.ts`.
- **No dependency changes.**
- **Deferred**: a cohort-wide statistics/export path not limited to the current page — tracked as a separate future change.
