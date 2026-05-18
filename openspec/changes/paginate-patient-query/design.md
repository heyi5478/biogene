## Context

`GET /patients` is served by svc-patient (`backend/svc-patient/svc_patient/app.py`) and proxied/enriched by the gateway (`backend/gateway/gateway/app.py`). svc-patient loads every patient row into an in-memory list at startup; `GET /patients` returns the whole list (optionally `q`-filtered) as `list[Patient]`. The gateway fans out per-patient batch calls and returns `list[PatientListItem]`. Neither layer bounds the result size.

The dataset grew via the recent 1.0→2.0 ETL merge: svc-patient's in-memory cache holds ~40k rows, the database has ~184k. Serializing the full list takes 23–119s; the gateway abandons the call at its 5s httpx timeout and returns `502 upstream_unavailable`. The frontend compounds this — `usePatients` has no `enabled` guard, so it fetches the full list on every mount even before a search is submitted.

The gateway's `POST /patients/condition-query` also calls the full `GET /patients` to resolve matched patients' base rows, so it fails the same way.

## Goals / Non-Goals

**Goals:**
- `GET /patients` returns a bounded page (≤50 rows) that completes well within the 5s timeout.
- The UI can display the true hit count and navigate result pages.
- `condition-query` stops depending on a full-table fetch.
- The frontend stops fetching before a query is submitted.

**Non-Goals:**
- Paginating `condition-query` results — cohort statistics and export consume the full matched set; minimal fix only.
- Re-architecting svc-patient's in-memory full-table cache.
- Changing the gateway's 5s timeout or container resource limits.
- Server-side sorting or cursor-based pagination.

## Decisions

### Offset/limit envelope, not page-number
`GET /patients` returns `{items, total, limit, offset}`. Slicing is offset-native (`filtered[offset:offset+limit]`) and an out-of-range offset degrades to `[]` for free. The 1-based UI page number is converted to an offset in exactly one place (the frontend service). `total` is required so the UI shows the real hit count and computes page count — a bare capped array cannot convey it. *Alternative:* `page`/`pageSize` — rejected; needs extra clamping and still must carry `total`.

### Two concrete envelope models, not a generic `Page[T]`
`shared/schemas.py` gains `PatientPage` (`items: list[Patient]`, used by svc-patient) and `PatientListPage` (`items: list[PatientListItem]`, used by the gateway). *Alternative:* a Pydantic generic `Page[T]` — rejected; the project has no existing generics and parametrized generics produce awkward OpenAPI component names. Two small concrete classes match house style.

### `POST /patients/batch` returns found rows only
The new endpoint mirrors the existing `POST /opd/batch` (id list in, dict out) but returns `dict[str, Patient]` containing only ids that exist. A `Patient` has required fields, so a missing id cannot get a placeholder; omission is the only valid option, and `condition-query` already tolerates it (`pid in base_by_pid`). *Alternative:* reworking `condition-query` to not need base rows — rejected; it genuinely needs base patient fields for its response.

### condition-query keeps its external contract
Only the internal base-row resolution changes (full `GET /patients` → `POST /patients/batch`). `condition-query` still returns `list[PatientListItem]` of all matches; cohort statistics and export downstream of it are untouched.

### Frontend: `enabled` guard + `keepPreviousData`
`usePatients(q, page)` sets `enabled: q !== ''` — no fetch until a query is submitted, removing the wasteful on-mount full-table request. `placeholderData: keepPreviousData` keeps the current page visible while the next loads, avoiding a skeleton flash on page navigation. The query key includes `page` so each page caches independently.

### Full pager UI
A new `PatientListPager` component wraps the already-present-but-unused shadcn `pagination.tsx`, rendering Prev/Next plus numbered page links with ellipsis (fixed boundary pages + a sibling window around the current page) — chosen so a multi-hundred-page result stays navigable.

## Risks / Trade-offs

- **BREAKING response shape** → Backend and frontend must deploy together; this change updates both layers and all affected tests as one unit.
- **svc-patient loads ~184k rows on restart** → Startup `load_all()` time and resident memory grow ~4.5×, approaching the ~843 MiB container limit; the readiness/health-check grace period may need widening. Flagged for the deploy owner. Pagination itself does not increase the footprint.
- **A very broad condition can still match tens of thousands** → `condition-query` is not paginated, so such a query stays heavy. Accepted: an uncommon path, and it is strictly better than today because base rows now resolve via O(1) id lookups in `/patients/batch` instead of full-table serialization.
- **E2E pagination test needs >50 seeded matches** → The seed dataset may be too small; the test may need a dedicated seed or instead assert pager-absence on small result sets.

## Migration Plan

Deploy `shared`, `svc-patient`, `gateway`, and the frontend together — the response-shape change is not backward compatible. Rollback = revert all four. No database migration is involved. After deploy, verify on staging by repeating the original failing search ("王") and confirming a paged HTTP 200 instead of a 502.
