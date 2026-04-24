## ADDED Requirements

### Requirement: PatientActions SHALL expose a single-patient statistics entry point

`frontend/src/components/PatientActions.tsx` MUST render a "統計" button that opens a `StatsDialog` for the currently displayed patient. The component MUST accept the patient as a prop and MUST own the open/close state of the dialog locally. The button MUST remain adjacent to the "匯出" button within `PatientActions` so users see both global actions together.

The `PatientActions` component MUST be placed on the same row as the `TabsList` in `frontend/src/pages/Index.tsx`, rendered to the right of the tab triggers.

`frontend/src/components/PatientSummary.tsx` MUST NOT declare a `calcAge` helper; age calculations used inside the summary MUST continue to use `ageInYears` from `frontend/src/utils/statsUtils.ts`.

#### Scenario: Stats button renders inside PatientActions

- **WHEN** a patient is displayed in the Index page
- **THEN** a "統計" button MUST be rendered by `PatientActions` on the tab row
- **AND** `PatientSummary` MUST NOT render a "統計" button

#### Scenario: Clicking the stats button opens the StatsDialog

- **WHEN** the user clicks the "統計" button in `PatientActions`
- **THEN** a `StatsDialog` MUST mount with the same `patient` prop that was passed to `PatientActions`

#### Scenario: calcAge duplication remains absent from PatientSummary

- **WHEN** the codebase is searched for `calcAge` function declarations in `frontend/src/components/PatientSummary.tsx`
- **THEN** exactly zero declarations MUST exist
- **AND** `ageInYears` from `statsUtils.ts` MUST continue to be the age-calculation source used in the summary

## REMOVED Requirements

### Requirement: PatientSummary SHALL expose a single-patient statistics entry point

**Reason**: 統計 按鈕不再由 `PatientSummary` 承載入口；改由新元件 `PatientActions` 在 Tab 列右側渲染，以分離「全域動作」與「模組跳轉」兩類按鈕的語義。

**Migration**: 呼叫端改為在 `Index.tsx` 的 `<Tabs>` 內使用 `<PatientActions patient={displayPatient} />`；原 `PatientSummary` 內的「統計」按鈕、`statsOpen` state、`StatsDialog` 渲染皆移除。新要求見本 change 的 `PatientActions SHALL expose a single-patient statistics entry point`。
