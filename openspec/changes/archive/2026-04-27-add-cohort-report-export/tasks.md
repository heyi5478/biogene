## 1. Extract shared utilities

- [x] 1.1 Create `frontend/src/utils/exporters/_sheetName.ts` exporting `uniqueSheetName(base: string, used: Set<string>): string` (move the implementation verbatim from `xlsxExporter.ts:3-21`).
- [x] 1.2 Update `frontend/src/utils/exporters/xlsxExporter.ts` to delete the local `uniqueSheetName` and import it from `./_sheetName`.
- [x] 1.3 Create `frontend/src/utils/dateStamp.ts` exporting `todayStamp(): string` (move the implementation verbatim from `ExportDialog.tsx:29-35`).
- [x] 1.4 Update `frontend/src/components/export/ExportDialog.tsx` to delete the local `todayStamp` and import it from `@/utils/dateStamp`.
- [x] 1.5 Run typecheck (`tsc --noEmit` or repo's existing script) and confirm no errors introduced by the moves.

## 2. Cohort XLSX exporter

- [x] 2.1 Create `frontend/src/utils/exporters/cohortXlsxExporter.ts` with signature `exportCohortXlsx(patients: Patient[], modules: ModuleId[], filename: string): Promise<void>`.
- [x] 2.2 Implement lazy `await import('xlsx')`; create workbook; for each `moduleId` build one sheet with leading columns `patientId / name / chartno` (apply `chartno || externalChartno || nbsId || patientId` fallback) followed by `MODULE_FIELDS[moduleId]` labels.
- [x] 2.3 For non-`basic` modules: per patient, emit one row per record; if `patient[moduleId]` is empty/missing, emit one blank-data row preserving identifier columns.
- [x] 2.4 For `basic` module: emit exactly one row per patient, reading `MODULE_FIELDS.basic` field ids directly from the patient object.
- [x] 2.5 Use `uniqueSheetName(moduleId, used)` from `./_sheetName` to derive sheet names.
- [x] 2.6 Call `XLSX.writeFile(wb, filename)` to trigger the download.

## 3. Exporter dispatcher

- [x] 3.1 In `frontend/src/utils/exporters/index.ts`, add `export type CohortExportFormat = 'xlsx';` and `export interface CohortExportOptions { format: CohortExportFormat; modules: ModuleId[]; filenamePrefix: string; }`.
- [x] 3.2 Add `export async function exportPatients(patients: Patient[], opts: CohortExportOptions): Promise<void>` that switches on `opts.format`, calls `exportCohortXlsx(patients, modules, ${filenamePrefix}.xlsx)` for `'xlsx'`, and uses an exhaustiveness `never` guard in the default branch (mirroring the existing `exportPatient` switch shape).
- [x] 3.3 Confirm `exportPatient` and its options are unchanged.

## 4. CohortExportDialog component

- [x] 4.1 Create `frontend/src/components/export/CohortExportDialog.tsx` with props `{ open: boolean; onOpenChange: (open: boolean) => void; patients: Patient[] }`.
- [x] 4.2 Compute `EXPORTABLE_MODULES` as `MODULE_DEFINITIONS.map(m => m.id).filter(id => id !== 'basic')` (same set as single-patient dialog), plus include `'basic'` explicitly so cohort can opt into per-patient identifier sheet — confirm in dialog UI; if `basic` is undesirable per spec discussion, omit. (Default decision: omit `basic` to mirror single-patient dialog and avoid duplicate identifier data.)
- [x] 4.3 Compute `cohortRecordCount(moduleId)` = sum across patients of `(patient[moduleId]?.length ?? 0)`; render checkbox row label as `${def.code} (${cohortRecordCount})`.
- [x] 4.4 Default `selected` set = every module whose `cohortRecordCount > 0`.
- [x] 4.5 Default filename prefix = `cohort_${todayStamp()}` (import from `@/utils/dateStamp`).
- [x] 4.6 Render `Dialog` with title `匯出比較報告 — ${patients.length} 位病人`, module checkbox grid (same styling as `ExportDialog`), `全選／全不選` toggle, filename `Input`, and `Cancel`/`Submit` footer using the `useActionState` + `useFormStatus` pattern from `ExportDialog.tsx`.
- [x] 4.7 Submit calls `await exportPatients(patients, { format: 'xlsx', modules: [...selected], filenamePrefix: prefix.trim() })`; on success close dialog; on failure `toast.error` and keep dialog open.
- [x] 4.8 Disable submit when `selected.size === 0` or `prefix.trim().length === 0`.
- [x] 4.9 Reset `selected` and `prefix` on every `open === true` transition (`useEffect` mirror of `ExportDialog.tsx:104-110`).

## 5. Wire export button into ConditionResults

- [x] 5.1 In `frontend/src/components/ConditionResults.tsx`, add `const [exportOpen, setExportOpen] = useState(false);` near the top of the component.
- [x] 5.2 Inside the `listContent` chip row (`ConditionResults.tsx:62-75`), append a `Button` with text `匯出比較報告`, `Download` icon from `lucide-react`, `disabled={matchedPatients.length === 0}`, `onClick={() => setExportOpen(true)}`. Place it on the far right (e.g. `ml-auto`).
- [x] 5.3 At the bottom of the `Tabs` JSX (after `</Tabs>` is fine, or just before `return` close), render `<CohortExportDialog open={exportOpen} onOpenChange={setExportOpen} patients={matchedPatients.map(m => m.patient)} />`.
- [x] 5.4 Confirm the 族群統計 tab does NOT render the export button (it only lives inside `listContent`).
- [x] 5.5 Confirm `Index.tsx` requires no changes (no new props, no new state).

## 6. Manual verification

- [x] 6.1 Start frontend (`npm run dev` in `frontend/`) and backend gateway + svc-* per existing dev startup.
- [x] 6.2 Open the app, set `FilterPanel` to condition mode, apply template `Phe 偏高（PKU 相關）`. Confirm 名單 tab shows the matched count and the "匯出比較報告" button is enabled.
- [x] 6.3 Switch to 族群統計 tab — confirm the button is NOT present in that tab content.
- [x] 6.4 Use a query that matches zero patients; confirm the button is disabled.
- [x] 6.5 Re-apply a non-empty query, click the button. Confirm dialog title shows `N 位病人`, defaults check modules with cohort data, prefix shows `cohort_YYYYMMDD`.
- [x] 6.6 Toggle `全不選`, confirm submit becomes disabled. Re-select a couple of modules, edit prefix, submit.
- [x] 6.7 Open the downloaded `.xlsx` and verify: one sheet per selected module, all sheet names ≤ 31 chars and unique; first three columns are `patientId / name / chartno`; multi-record patients produce multiple rows; selected patients with no records in that module appear as a single row with module columns blank; module columns header text matches `MODULE_FIELDS[moduleId].label`.
- [x] 6.8 Edit prefix to a custom value (e.g. `pku-cohort_2026Q1`); confirm filename matches `pku-cohort_2026Q1.xlsx`.
- [x] 6.9 Regression: open a single patient via the standard search flow and run the existing `ExportDialog` for CSV, JSON, and XLSX; confirm all three downloads still work and produce the same outputs as before this change.

## 7. OpenSpec validation

- [x] 7.1 Run `openspec validate add-cohort-report-export --strict` and resolve any reported issues.
- [x] 7.2 Run `openspec status --change add-cohort-report-export` and confirm `isComplete: true`.
