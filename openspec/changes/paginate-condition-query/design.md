## Context

`POST /patients/condition-query` is served by the gateway (`backend/gateway/gateway/app.py`, `condition_query`). It buckets the inbound conditions by owning service, calls each service's `condition-match` for per-condition matched patient-id lists, combines them with AND (intersection) / OR (union) into a `combined` set, then **hydrates every matched patient** — resolving base rows via `POST /patients/batch` and fanning out `/opd/batch` `/labs/batch` `/diseases/batch` to build each `PatientListItem` with its `conditionHits`.

`combined` is unbounded. A broad condition such as `性別 = 男` matches ~90k of ~184k patients; the four batch calls then carry ~5.5MB request bodies and svc-patient spends 80–155s validating/serialising that many records — well past the gateway's 5s httpx timeout (`app.py:65`) → `502 upstream_unavailable`. The abandoned job keeps svc-patient's single worker busy, so retries and healthz also fail until it drains.

The archived `paginate-patient-query` change paginated `GET /patients` and added `POST /patients/batch`, but explicitly listed paginating condition-query as a Non-Goal because cohort statistics and export consume the full matched set. This change paginates condition-query and accepts an interim degradation of those two features.

## Goals / Non-Goals

**Goals:**
- `POST /patients/condition-query` returns a bounded page that completes well within the 5s timeout, regardless of how many patients the conditions match.
- The 條件查詢 results table can navigate result pages and shows the true hit count.
- Reuse the `GET /patients` pagination shape and the existing `PatientListPager` end-to-end — no new patterns.

**Non-Goals:**
- A cohort-wide statistics/export path. The 族群統計 tab and 匯出 dialog are knowingly degraded to current-page-only with a notice; the proper fix is a separate change.
- "Snapshot conditions at submit." `useConditionPatients` stays keyed on the live condition request; per-keystroke re-fire remains, but each query is now a single bounded page.
- svc-patient changes, schema additions, or changing the gateway's 5s timeout.

## Decisions

### Offset/limit envelope, mirroring `GET /patients`
condition-query returns `{items, total, limit, offset}` and accepts `limit` (default 50, max 200) / `offset` (default 0) as query parameters alongside the existing `ConditionRequest` JSON body — FastAPI reads a Pydantic parameter from the body and bare `Query` scalars from the query string. This is the exact contract `list_patients` already uses. *Alternative:* a new `ConditionQueryRequest` model carrying pagination in the body — rejected; query params keep the body a pure `ConditionRequest` and match the sibling endpoint.

### Reuse `PatientListPage`, no new schema
`shared/schemas.py` already has `PatientListPage` (`items: list[PatientListItem]`, `total`, `limit`, `offset`), and `PatientListItem` already carries the optional `conditionHits` field condition-query sets. The response model is reused verbatim. *Alternative:* a dedicated `ConditionQueryPage` — rejected; identical shape, no benefit.

### Gateway slices; svc-patient is untouched
The per-condition matched-id lists are cheap (ids only); the gateway is the only layer that knows the AND/OR-combined set, so it does the slicing. The gateway computes `total = len(combined)`, then hydrates only `sorted(combined)[offset:offset+limit]`. svc-patient's `condition-match` and `/patients/batch` are unchanged — they simply receive smaller id lists. *Alternative:* push pagination into svc-patient — impossible, it never sees the combined set.

### Deterministic ordering before slicing
`combined` is a Python `set` with non-stable iteration order, so consecutive requests for the same `offset` could return overlapping or missing rows. The gateway sorts by `patientId` (`sorted(combined)`) before slicing. *Alternative:* sort by a clinical field (chartno, name) — out of scope; a stable arbitrary order suffices for this fix and `patientId` is always present.

### Cohort statistics / export: interim current-page scope
`ConditionResults` passes its (now paged) `matchedPatients` to `CohortStatsPanel` and `CohortExportDialog` unchanged — so both now describe only the current page. Rather than degrade silently, each gains a visible「僅供參考,僅含目前頁面」notice, and the export button's enable flips from `matchedPatients.length > 0` to `total > 0`. A cohort-wide path (server-side aggregation, or a separate capped full-cohort fetch) is deferred. *Alternative considered earlier:* cap the result at ~500 and keep cohort features whole — rejected by the user in favour of true table pagination.

### Page validity without a submit-snapshot
`useConditionPatients` stays keyed on the live `conditionRequest`. Editing a condition while paged deep would leave `conditionPage` stale/out-of-range. Fix: `Index.tsx` resets `conditionPage` to 1 on submit, on clear, and via a `useEffect` keyed on the `conditionRequest` memo (which changes only on a real condition/logic edit, not on a page change). *Alternative:* introduce `submittedConditionReq` and key the query on the snapshot — deferred (out of scope per the proposal); the reset effect is the minimal correct fix.

## Risks / Trade-offs

- **BREAKING response shape** → the gateway and frontend must deploy together; this change updates both layers and all affected tests as one unit. Rollback = revert the change.
- **族群統計 / 匯出 silently narrowed to one page** → mitigated by the visible「僅供參考」notice on both; a follow-up change restores cohort-wide scope. Accepted by the user.
- **Per-keystroke re-fire persists** (no submit-snapshot) → each fire is now a single bounded page (cheap) rather than a full-cohort hydration, so the cascading-outage behaviour is gone; the residual cost is acceptable, and the `conditionRequest`-keyed reset effect keeps the page index valid.
- **A cold svc-patient can still 502 the condition-match leg** → the full-table scan in `condition-match` (~2–3s warm) can exceed 5s on the swap-thrashing stage host. This is the known intermittent 502 (host RAM), recovers on retry, and is out of scope.

## Migration Plan

Deploy the gateway and the frontend together — the response-shape change is not backward compatible. Rollback = revert the change. No database migration is involved. After deploy, verify on stage by repeating the original failing query (`性別 = 男` in 條件查詢) and confirming a paged HTTP 200 instead of a 502.
