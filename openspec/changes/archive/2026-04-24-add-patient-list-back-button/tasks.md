## 1. Implementation

- [x] 1.1 In `frontend/src/pages/Index.tsx`, inside the `{displayPatient && (...)}` branch of the patient-mode render (currently ~line 245), insert a conditional back button rendered above `<PatientSummary patient={displayPatient} … />`. The condition MUST be `selectedPatient && results.length > 1`. The button MUST mirror the condition-mode pattern at `Index.tsx:314-322`: `variant="ghost"`, `size="sm"`, `className="mb-1 h-7 px-2 text-xs"`, leading `<ArrowLeft className="mr-1 h-3.5 w-3.5" />`, label `返回病人名單`, onClick `() => setSelectedPatient(null)`.
- [x] 1.2 Confirm `Button` and `ArrowLeft` are already imported at the top of the file (they are — used elsewhere). Do not add redundant imports.

## 2. Verification

- [x] 2.1 Run `npm run typecheck` in `frontend/` — MUST pass.
- [x] 2.2 Run `npm run lint` in `frontend/` — MUST pass.
- [x] 2.3 Manually exercise the patient-mode flow in `npm run dev`:
  - Search that returns >1 patients → pick one → back button visible → click back → list restored with query/modules/tab intact → pick a different patient → works.
  - Search that returns exactly 1 patient → detail auto-renders → back button NOT rendered.
  - Search that returns 0 patients → empty state → no back button.
- [x] 2.4 Manually exercise the condition-mode flow to confirm the existing "返回條件查詢結果" button is unaffected.
- [x] 2.5 If an existing Vitest / Playwright test covers the patient-list flow, run it and confirm no regression. If not, no new test is required for this change (small UI affordance, covered by manual verification).
