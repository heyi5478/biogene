## Why

In the patient-search flow on the Index page, when a query returns multiple patients and the user picks one to view details, the detail view renders without any way to go back to the list — the user is stranded on a single patient and cannot pick a different one without clearing filters and re-running the search. The condition-query flow already solves this (`frontend/src/pages/Index.tsx:314-322` renders a "返回條件查詢結果" back button); patient mode is inconsistent and must match.

## What Changes

- Add a "返回病人名單" back button at the top of the patient-mode detail view on the Index page.
- The button MUST be visible only when a detail is being shown after picking from a multi-result list (i.e. `selectedPatient` is set AND the current query returned more than one patient). When the query returned exactly one patient (auto-selected), no list exists to return to, so the button MUST NOT render.
- Clicking the button returns the user to the `PatientList` with filter/search/module-selection/active-tab state preserved.
- Visual treatment (icon, size, variant, copy pattern) mirrors the existing condition-mode back button so the two flows feel uniform.

## Capabilities

### New Capabilities
- `patient-query-navigation`: list → detail → list navigation affordances for the patient and condition query flows on the Index page.

### Modified Capabilities
<!-- none -->

## Impact

- Code: `frontend/src/pages/Index.tsx` only (one JSX block inserted inside the existing `{displayPatient && …}` fragment).
- No new dependencies, no new components, no routing changes — the app is single-page and state-driven.
- No API, backend, or shared-type changes.
- Existing behaviour of condition-mode back button is unchanged (used as the reference pattern).
