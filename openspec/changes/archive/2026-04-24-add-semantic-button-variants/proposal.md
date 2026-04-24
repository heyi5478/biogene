## Why

Four user-facing action buttons —「清除全部條件」(FilterPanel footer and ConditionBuilder footer)、「統計」and「匯出」(PatientSummary toolbar) — currently share the same `outline` variant as the surrounding navigation jump buttons, so they give no visual signal about the severity or intent of the action. The project already defines `--warning`, `--success`, `--info` HSL tokens in `index.css`, but these tokens are not wired into Tailwind nor exposed as Button variants, so there is no reusable way for any component to render a semantic colored button. Additionally, a `danger` token (red-orange, distinct from `destructive`'s pure red) is introduced as a reusable mid-severity signal for future call-sites that need a red-family warning that is not "permanent deletion."

## What Changes

- Register `warning`, `success`, `info`, `danger` colors (plus their `-foreground` pairs) in `tailwind.config.ts` so the CSS tokens defined in `index.css` become usable Tailwind utilities.
- Add a new `--danger` / `--danger-foreground` token pair to `index.css` for both light and dark themes (red-orange hue, ~20°, distinct from `--destructive`'s pure red).
- Adjust `--info` HSL in `index.css` (light + dark) so it is visually distinct from `--primary` (they currently share the exact same blue).
- Add four new variants to the shared `Button` component: `warning`, `danger`, `success`, `info`, following the same filled-background pattern as `default` / `destructive`.
- Apply variants to the four target buttons, reusing the existing `destructive` variant for the two clear-all buttons so that destructive/irreversible actions share one consistent visual signal:
  - `FilterPanel.tsx` 清除全部條件 → `variant="destructive"`
  - `ConditionBuilder.tsx` 清除全部條件 → `variant="destructive"`
  - `PatientSummary.tsx` 統計 → `variant="success"`
  - `PatientSummary.tsx` 匯出 → `variant="info"`

The new `danger` variant is registered for future use and not bound to any current call-site. No breaking changes: existing variants (`default`, `destructive`, `outline`, `secondary`, `ghost`, `link`) are untouched; all other callers of `<Button>` continue to render identically.

## Capabilities

### New Capabilities
- `shared-ui-buttons`: Documents the shared `Button` component's semantic variant contract (default / destructive / outline / secondary / ghost / link / warning / danger / success / info) and the semantic color tokens each variant consumes. Establishes the baseline so future changes can extend or modify the variant set without re-deriving the contract from source.

### Modified Capabilities
<!-- None. No existing capability spec covers button UI; no behavior of existing specs (backend-api, patient-export, cohort-statistics, etc.) changes as a result of this presentational tweak. -->

## Impact

- **Affected files (6):** `frontend/tailwind.config.ts`, `frontend/src/index.css`, `frontend/src/components/ui/button.tsx`, `frontend/src/components/FilterPanel.tsx`, `frontend/src/components/ConditionBuilder.tsx`, `frontend/src/components/PatientSummary.tsx`
- **Affected users:** Anyone viewing the patient query UI — four buttons change from neutral outline to colored filled styling.
- **Dependencies:** None added. Uses existing `class-variance-authority`, Tailwind, and CSS custom properties already in the project.
- **Risk:** Low. Presentational change only; no data, API, or behavioral changes. Dark mode support is preserved because the adjusted `--info` value is defined for both themes.
