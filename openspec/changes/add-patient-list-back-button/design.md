## Context

The Index page (`frontend/src/pages/Index.tsx`) is a single-route, state-driven page with two query modes: `patient` (free-text search) and `condition` (structured filter). Each mode has a list view and a detail view, toggled by local `useState` (`selectedPatient`, `conditionPatient`). Condition mode already renders a back button above the detail view (`Index.tsx:314-322`) that sets the selection state back to `null`, re-revealing the list. Patient mode has no equivalent — a documented UX gap, not a new feature.

## Goals / Non-Goals

**Goals:**
- Make the patient-mode list→detail flow symmetric with the condition-mode flow.
- Preserve all filter/search state so returning to the list feels instant, not a re-search.
- Reuse the existing visual pattern so the two back buttons look the same.

**Non-Goals:**
- Extracting a shared `<BackButton>` component. Two usages with different copy and handler don't justify the abstraction yet.
- Adding breadcrumbs, URL-based routing, or browser-history integration. The app is intentionally single-route and state-driven; changing that is a larger architectural decision out of scope here.
- Persisting query state across page refreshes (sessionStorage / URL params).
- Refactoring the condition-mode back button.

## Decisions

### Decision 1: Render the back button inline in Index.tsx, not as a new component

Two sites, two sets of copy. Per the project's "three-similar-lines-beats-premature-abstraction" rule, inline is cheaper than a component + its tests + its prop API. If a third back-button site appears later, extract then.

**Alternative considered:** `<BackButton onBack={...} label="..."/>`. Rejected — net lines added exceed net lines saved, and the two existing sites differ in context (label text, container classes).

### Decision 2: Gate visibility on `selectedPatient && results.length > 1`

`displayPatient = selectedPatient || (results.length === 1 ? results[0] : null)` — when a search returns exactly one patient, the detail view auto-opens without a list existing, so a back button would point to an empty prior state. The gate guarantees the button only appears when there is a meaningful list to go back to.

**Alternative considered:** always render the button whenever `displayPatient` is truthy and call `handleClearAll()`. Rejected — clearing the search wipes the user's query; they'd have to re-type it.

### Decision 3: Click handler is `() => setSelectedPatient(null)` only

Clearing just the selection (not search/module/tab state) mirrors the condition-mode handler (`setConditionPatient(null)`) and matches the user's mental model: "go back" means "undo the last pick," not "restart."

## Risks / Trade-offs

- **Minor inconsistency if a future refactor removes the `results.length > 1` branch of the list rendering** → the gate condition would need to be updated alongside it. Mitigation: the gate uses the same `results.length > 1` expression as the list render at `Index.tsx:240`, so a grep will find both.
- **No keyboard shortcut / browser-back integration** → users who instinctively hit the browser Back button will leave the SPA entirely. Accepted: matches existing condition-mode behaviour; SPA history routing is out of scope.
