## Why

The existing condition query already filters across all patients and surfaces a multi-patient match list (`ConditionResults` 名單 tab) plus cohort statistics, but there is **no way to export that match list** — clinicians who want to compare metabolic / NBS results across the matched cohort must drill into each patient one by one and export them individually, then assemble the comparison manually. This blocks the canonical clinical workflow of "篩出某疾病/某檢驗的病人 → 直接拿到一份比較表給醫師看"。

## What Changes

- Add a "匯出比較報告 (XLSX)" button to the `名單` tab of `ConditionResults`, enabled when the matched-patient count > 0.
- Introduce a `CohortExportDialog` (XLSX-only) that lets users select which modules to include and edit a filename prefix; defaults select every module that has at least one record across the cohort.
- Introduce a `cohortXlsxExporter` that emits a single workbook with one sheet per selected module: leading columns `patientId / name / chartno`, then one column per `MODULE_FIELDS[moduleId].label`. Patients with multiple records in a module produce multiple rows; selected patients with no records in that module still appear as a single row with module columns blank.
- Extract two shared helpers (`uniqueSheetName`, `todayStamp`) so the existing single-patient `xlsxExporter` and `ExportDialog` and the new cohort versions share one source of truth.
- No backend changes. No new route. No change to condition-query semantics or to single-patient export behaviour.

## Capabilities

### New Capabilities
- `cohort-export`: multi-patient (cohort) export from condition-query results — entry button, dialog, XLSX writer, filename convention.

### Modified Capabilities
- `cohort-statistics`: the `名單` tab requirements gain a new requirement that an export entry point is rendered alongside the condition summary chips and is gated on cohort size. Existing `名單` and `族群統計` behaviours are preserved.

## Impact

- **Frontend code** (only):
  - Modified: `frontend/src/components/ConditionResults.tsx`, `frontend/src/components/export/ExportDialog.tsx`, `frontend/src/utils/exporters/xlsxExporter.ts`, `frontend/src/utils/exporters/index.ts`.
  - Added: `frontend/src/components/export/CohortExportDialog.tsx`, `frontend/src/utils/exporters/cohortXlsxExporter.ts`, `frontend/src/utils/exporters/_sheetName.ts`, `frontend/src/utils/dateStamp.ts`.
- **Dependencies**: none added; reuses existing `xlsx@0.18.5` (already lazy-loaded for single-patient XLSX export).
- **Bundle**: no growth in initial bundle — `xlsx` import remains lazy.
- **Backend / API / data**: untouched (gateway, svc-patient, svc-lab, svc-disease, mock data, schemas).
- **Existing flows**: single-patient export, condition query, cohort statistics — all unchanged behaviourally.
