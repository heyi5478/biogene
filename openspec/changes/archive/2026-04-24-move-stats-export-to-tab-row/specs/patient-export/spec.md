## ADDED Requirements

### Requirement: PatientActions SHALL expose an export entry point

`frontend/src/components/PatientActions.tsx` MUST render a "匯出" button that opens an `ExportDialog` scoped to the currently displayed `patient`. The component MUST accept the patient as a prop and MUST own the dialog's open/close state locally. The "匯出" button MUST sit adjacent to the "統計" button inside `PatientActions`.

`PatientActions` MUST be rendered on the same row as the `TabsList` in `frontend/src/pages/Index.tsx`, positioned to the right of the tab triggers, so that the export entry point is always visible while the user browses any tab (`全部 / 基本資料 / 門診 / 檢驗 / 檢體 / 新生兒篩檢`).

The "匯出" button MUST be enabled whenever a patient is displayed; it MUST NOT be disabled, hidden, or gated by which tab is active.

#### Scenario: Export button renders inside PatientActions on every tab

- **WHEN** a patient is selected (either via single-match search or `PatientList` click) and any tab is active
- **THEN** `PatientActions` MUST render a "匯出" button on the tab row
- **AND** `PatientSummary` MUST NOT render a "匯出" button
- **AND** the button MUST be enabled

#### Scenario: Clicking the export button opens the ExportDialog

- **WHEN** the user clicks the "匯出" button in `PatientActions`
- **THEN** an `ExportDialog` MUST open with the same `patient` reference passed into `PatientActions`
- **AND** the dialog MUST NOT alter any state outside itself until the user confirms

## REMOVED Requirements

### Requirement: PatientSummary SHALL expose an export entry point

**Reason**: 匯出 按鈕不再由 `PatientSummary` 承載入口；為與「統計」按鈕統一並與模組跳轉按鈕做語義切分，改由新元件 `PatientActions` 在 Tab 列右側渲染。

**Migration**: 呼叫端改為在 `Index.tsx` 的 `<Tabs>` 內使用 `<PatientActions patient={displayPatient} />`；原 `PatientSummary` 內的「匯出」按鈕、`exportOpen` state、`ExportDialog` 渲染皆移除。新要求見本 change 的 `PatientActions SHALL expose an export entry point`。
