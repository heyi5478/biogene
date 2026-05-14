## Context

The system currently has three FastAPI services (`svc-patient`, `svc-lab`, `svc-disease`) that load every row of `db_main` / `db_external` / `db_nbs` into in-memory caches keyed by `patientId` at startup, behind a single `gateway` BFF on port 8000. The frontend SPA calls `gateway` exactly once for the patient list and runs both modes of "search" in the browser. The dual-backend `data_loader.py` lets the cache come from either JSON fixtures or Postgres while keeping service code byte-equal — that contract is locked in by the `postgres-data-backend` spec and we will not break it.

Postgres is provisioned (16, four alembic versions applied) but the `patient` tables in all three schemas are empty; mock-data → PG seeding has never run in this environment. Today the dev-mode default is JSON, so service code is exercised end-to-end, but the PG path has not been hit by a running app.

The condition-search engine in `ConditionResults.tsx:189-335` covers eleven operators (`contains / eq / neq / gt / gte / lt / lte / between / before / after / has_data / no_data`) and is the only authoritative source of evaluation semantics. Whatever we move to the server must reproduce its behaviour exactly, because Playwright e2e and unit tests rely on the existing matching results.

Stakeholders: SPA users (geneticists running 13-patient queries today, plausibly ≥1k after real data lands), the on-call backend engineer (PG mode is now the operational backend), and any future client of `GET /patients` (currently only the SPA, but the endpoint is documented in `backend-api`).

## Goals / Non-Goals

**Goals:**
- Both search modes (text / condition) run server-side; the SPA never receives data outside the result set it asked for.
- `GET /patients` payload shrinks ≥80% (mock dataset baseline: 22 KB → ≤4 KB) by dropping inlined module arrays.
- The existing `GET /patients/{id}` endpoint becomes the single source of full-bundle data for the UI.
- Postgres is the operational data backend; JSON mode keeps working for tests and offline dev.
- `evaluateConditions` semantics are preserved bit-for-bit (verified by porting tests, not by re-deriving them).

**Non-Goals:**
- Pagination, virtualization, or limit/offset on the list endpoint (out of scope; deferred until the dataset warrants it).
- Shareable URL state for the search input.
- True SQL `ILIKE` / `WHERE` predicates against PG. The cache-then-filter pattern is sufficient for the current and near-term scale, and rewriting `data_loader` would break the `postgres-data-backend` bit-equal contract.
- Reworking `condition` query UX, ConditionBuilder, or condition templates. Only the data path under them changes.
- Removing JSON mock mode — both backends remain supported.

## Decisions

### 1. Filter location: in-memory on the existing service caches

Each downstream service already builds a `dict[str, list[dict]]` index by `patientId` in its lifespan handler. The new endpoints filter on these dicts in Python.

**Why:** Preserves the `postgres-data-backend` bit-equal contract (service code is unchanged across JSON vs PG; only `data_loader.load_all` differs). For the current 13-patient dataset and even for a thousand-patient dataset the filter cost is sub-millisecond. Adding query helpers to `data_loader` would require parallel JSON / PG implementations of every predicate the condition engine expresses — a 10× implementation cost compared to porting the JS evaluator once.

**Alternatives considered:**
- **SQLAlchemy `WHERE` predicates pushed into PG.** Rejected for now: requires giving up bit-equal across backends, and the cache pattern already has all the data resident. Worth revisiting once `patient` row counts exceed ~10k or once we add full-text search.
- **Filter in the gateway** after fanning out today's full bundles. Rejected: misplaces the responsibility (the data owners are the downstream services), and still pays the fan-out cost on every search.

### 2. Condition evaluator lives in `backend/shared/shared/condition.py`

A single Python module exports `eval_condition(record, field, op, value, value2) -> bool` and `match_records(records, ...) -> bool`, ported one-to-one from `ConditionResults.tsx:237-279`. All three services import it.

**Why:** The eleven operators are identical across modules; duplicating them per service would invite drift. Putting the evaluator in `shared` matches where `data_loader` and `schemas` already live.

**Alternatives:** Generating SQL per operator (rejected with decision 1) or duplicating per service (rejected for drift risk).

### 3. Condition routing: gateway parses & dispatches; services match per-condition only

The gateway accepts `POST /patients/condition-query`, splits the conditions list by `moduleId` into three sub-lists (basic+opd → svc-patient, lab modules → svc-lab, disease/NBS modules → svc-disease), fans them out in parallel to each service's `POST /{patients,labs,diseases}/condition-match`, receives back per-condition `patientIds` sets, and combines them in Python with `set.intersection` (AND) or `set.union` (OR). The final id set is then projected through svc-patient's cache to build `PatientListItem[]`.

**Why:** Each service owns the modules it indexes, so the per-condition match can be local. Gateway is the only place that has visibility across all three services, so the AND/OR fold belongs there. Services don't need to know about logic — they only return per-condition matches, which keeps their API minimal and testable.

**Alternatives:**
- **Send all conditions to all services.** Wasteful — most conditions touch only one service.
- **Have one service own the join.** Rejected — would couple services and violate the "no inter-service calls" rule from `backend-api`.

### 4. Slim `PatientListItem` shape, distinct from `Patient`

Backend defines a new Pydantic model `PatientListItem` (base patient fields + `dnabankCount`, `outbankCount`, `lastVisitDate`, optional `conditionHits`). Frontend mirrors it as a TypeScript interface. `Patient` (full bundle) is unchanged and remains the response model for `GET /patients/{id}`.

**Why:** Keeps the type system honest about which payload a caller has. Components that need module detail (`ResultModules`, `PatientSummary`) take `Patient`; components that only render rows (`PatientList`, `ConditionResults` table) take `PatientListItem`. `PatientSummary` already uses `dnabank.length`, `outbank.length`, and `opd[0].visitDate` — the summary fields are picked to cover its needs without having to fetch detail.

**Alternatives:** Make all module arrays `optional` on the existing `Patient` type. Rejected — every consumer would have to handle `undefined`, defeating the purpose of the slim shape.

### 5. Selection flow: pass id, not object

`PatientList.onSelect` and `ConditionResults.onSelectPatient` change to `(id: string) => void`. `Index.tsx` keeps `selectedPatientId` in state and uses `usePatient(id)` to fetch the bundle on demand. `PatientSummary` and `ResultModules` only render after detail loads.

**Why:** Rows in the list now carry `PatientListItem`, which lacks module arrays — selecting an object would be a lie. Going through id keeps a clear data flow: list = `usePatients(q)`, detail = `usePatient(id)`. Single-result auto-detail (`results.length === 1` in `Index.tsx:93-94`) is preserved by deriving `selectedPatientId` from the single row.

**Alternatives:** Pass the list item and lazy-fetch missing fields inside `PatientSummary`. Rejected — couples a leaf component to a query and complicates testing.

### 6. React Query hooks: per-search keying with stale time

`usePatients(q)` keys on `['patients', 'list', q ?? '']`. `useConditionPatients(req, enabled)` keys on `['patients', 'condition', req]` and is gated by `enabled` so empty condition lists don't fire. Both queries set `staleTime: 5 * 60 * 1000` and `gcTime: 30 * 60 * 1000` so navigating around the SPA doesn't re-hit the gateway constantly.

**Why:** `staleTime` was missing today (every remount refetched). Per-`q` keys make React Query do the right thing automatically — cached results for previous searches stay around, only the new key fires a request.

### 7. PG enablement is a precondition, not part of the change

The change assumes `make -C backend seed-pg` has been run and `GIMC_DATA_BACKEND=postgres` is set. The implementation does not touch `data_loader` or alembic — those are owned by `postgres-data-backend` and are already complete.

## Risks / Trade-offs

- **[Risk] Behavioural drift between the JS and Python condition evaluators** → Mitigation: port `ConditionResults.tsx:237-279` line-by-line, then add `backend/shared/tests/test_condition.py` cases derived from the existing frontend `evaluateConditions` test fixtures (if any) or hand-built parity tests. Run the same Playwright `condition` flow before and after to confirm match counts are unchanged.
- **[Risk] In-memory filter doesn't scale** → Mitigation: 13 patients today, sub-millisecond at any plausible near-term size. When row count crosses ~10k or a real text-search use case appears, swap the filter for SQLAlchemy `WHERE` clauses; the public API surface (`?q=`, `POST /condition-query`) stays the same so the SPA need not change.
- **[Risk] Breaking external `GET /patients` consumers** → Mitigation: only known consumer is the SPA, which is updated in the same change. The proposal flags this as **BREAKING**. If a hidden consumer surfaces, restoring inlined module arrays as a backward-compatible response variant is straightforward (gateway can attach them when a `?include=detail` flag is present, but we won't add that pre-emptively).
- **[Risk] Cache staleness across services** → Mitigation: caches are loaded once at startup, same as today. A patient created after startup is invisible until restart in either the old or new design — no change to that property.
- **[Risk] CORS preflight on `POST /patients/condition-query`** → Mitigation: gateway's `CORSMiddleware` already lists `POST` in `allow_methods`; preflight is one extra round trip per condition search, accepted.
- **[Trade-off] Two response shapes for a "patient"** (`PatientListItem` vs `Patient`). Worth it for type honesty; the additional Pydantic model and TS interface are cheap.

## Migration Plan

1. **Seed PG** (one-time, manual): `make -C backend seed-pg`; verify with `make -C backend verify-pg`.
2. **Set backend env**: write `GIMC_DATA_BACKEND=postgres` into `backend/.env`.
3. **Implement backend** (in order): `shared/condition.py` + tests → `shared/schemas.py` (new models) → svc-patient `?q=` + `condition-match` → svc-lab `condition-match` → svc-disease `condition-match` → gateway `?q=` + `condition-query` + slim list response. Each step has its own pytest before moving on.
4. **Implement frontend** (in order): `lib/api.ts` `apiPost` → `services/patients.ts` → `hooks/queries/keys.ts` + `usePatients(q)` + `useConditionPatients` + wired-up `usePatient` → `Index.tsx` rewiring → `PatientList`, `ConditionResults`, `PatientSummary` prop changes → `types/patient.ts` `PatientListItem`. MSW mocks updated alongside.
5. **Test parity**: run `npm test`, `npm run test:e2e`, `pytest`. Manual smoke via the chrome-devtools MCP (search a name, switch to condition mode with a `Fabry` predicate, click into a patient, confirm `GET /patients/{id}` fires).
6. **No rollback step.** This is an additive-then-replacement migration in a single change; if something breaks, revert the change branch.

## Open Questions

- None blocking. The biggest judgement call (in-memory filter vs SQL) is documented in decision 1 and revisitable when scale demands.
