## Context

The frontend already has two well-separated export concerns: single-patient export (`PatientActions` → `ExportDialog` → `exportPatient` → `xlsxExporter / csvExporter / jsonExporter`, governed by the `patient-export` spec), and the condition-query result UI (`ConditionResults` with the `名單` and `族群統計` tabs, governed by the `cohort-statistics` spec). The condition engine (`evaluateConditions` in `ConditionResults.tsx:282`) already returns a `MatchedPatient[]`, and the `Patient` objects in that list are the exact same references TanStack Query caches via `usePatients()` — i.e. they already carry every module array we want to export.

What is missing is purely a **delivery affordance** for that cohort: a button on the 名單 tab that turns the matched list into a single shareable artifact a clinician can hand to a doctor for cross-patient comparison.

This design intentionally does not introduce a new page, route, navigation entry, filter UI, or backend endpoint. The decision rationale is captured below.

## Goals / Non-Goals

**Goals:**
- One-click multi-patient comparison-report export from the existing condition-query result.
- Output format optimized for cross-patient comparison: one workbook, one sheet per module, leading patient-identifier columns, then per-record measurement columns.
- Reuse all currently working pieces: condition engine, matched-patient list, `MODULE_FIELDS` label map, `xlsx` lib (lazy), `Dialog` / `Checkbox` / `Input` / `Button` UI primitives, `useActionState` + `useFormStatus` form pattern.
- Preserve every existing single-patient export behaviour byte-for-byte.

**Non-Goals:**
- New `/cohort` route or page (the previous draft proposed this; rejected because condition query already supplies multi-patient filtering).
- Multi-patient CSV or PDF export (XLSX only in v1).
- Export from the 族群統計 tab (statistics export is a separate concern; future change).
- Server-side filter or new gateway endpoint (in-memory + 60s React-Query cache is sufficient; client-side filter already runs in `evaluateConditions`).
- Sub-table flattening (CAH→CAH_TGAL, DMD→DMD_TSH) — only the parent module rows are emitted in v1.
- Schema, mock-data, or backend changes.

## Decisions

### D1. Add export to existing `ConditionResults`, do not build a new page
**Choice:** Place the entry point inside `ConditionResults.tsx`'s 名單 tab, beside the condition summary chips.
**Alternatives considered:**
- A new `/cohort` page with its own simplified filter UI (disease module dropdown, instrument module dropdown, diagnosis text). Rejected: duplicates `ConditionBuilder`, splits the cohort workflow across two surfaces.
- Embedding the export inside the 族群統計 tab. Rejected: the 名單 tab is where the cohort identity is visible (chips + count + table); placing the button there makes "I see this cohort, I export this cohort" trivially obvious.

**Rationale:** The condition engine already does cross-patient filtering with arbitrary operators (`gt`, `contains`, `eq`, `has_data`, ...) and ships predefined `CONDITION_TEMPLATES` covering disease/instrument-style queries. Adding a parallel filter UI would be strict duplication and a long-term divergence risk.

### D2. XLSX-only in v1
**Choice:** Single output format. No format radio in the dialog.
**Alternatives considered:** Match `ExportDialog` and offer CSV (zip) / JSON / XLSX.
**Rationale:** Comparison and statistical work happens in Excel; a workbook with one sheet per module is the natural cross-patient layout. CSV would either flatten everything (loses module separation) or produce a zip-of-CSVs with the same row structure as XLSX (more clicks, no extra value). JSON is for machine consumers, which is not the target. We can extend later via the `format` discriminant in `CohortExportOptions`.

### D3. Sheet layout: leading identifier columns + per-field columns; one row per record
**Choice:** Each sheet's columns are `patientId, name, chartno` followed by `MODULE_FIELDS[moduleId].label` in declared order. Each record in `patient[moduleId]` produces one row. A patient selected for export but with zero records in this module produces a single row with identifier columns filled and module columns blank.
**Alternatives considered:**
- One row per patient (collapsing multi-record modules by latest / mean / first). Rejected: clinical comparison often needs to see every record (e.g. multiple AA samples over time); collapsing loses information without consent.
- Wide format pivoting record values into columns. Rejected: variable record counts produce ragged sheets that Excel users find harder to filter/sort.

**Rationale:** Long-format with explicit identifier columns is the universal "comparison table" shape — it sorts, filters, and pivots cleanly in Excel. The blank-record-row keeps the cohort visible: the user can see "病人 X 沒有 AA 資料" rather than silently missing.

### D4. Extract `uniqueSheetName` and `todayStamp` as shared utilities
**Choice:** Move `uniqueSheetName` from `xlsxExporter.ts:3` to a new `_sheetName.ts`; move `todayStamp` from `ExportDialog.tsx:29` to a new `dateStamp.ts`. Both single-patient and cohort code import from the shared location.
**Alternatives considered:** Copy-paste into the cohort modules.
**Rationale:** Two callers is the threshold where divergence starts to bite (Excel sheet-name escape rules and date-format conventions are precisely the kind of detail that drifts when duplicated). The extraction is small (one function each) and mechanical — low risk, immediate dedup.

### D5. Filename convention `cohort_YYYYMMDD.xlsx`
**Choice:** Default prefix `cohort_${todayStamp()}`; user can edit. Final filename `${prefix}.xlsx`.
**Alternatives considered:** Use the first matched patient's `chartno` (mirrors single-patient pattern). Rejected: there is no single primary patient in a cohort; using one patient's identifier in a multi-patient file is misleading.

### D6. Default module selection mirrors cohort presence
**Choice:** A module is checked by default iff at least one patient in the cohort has `patient[moduleId].length > 0`. The user can override.
**Alternatives considered:** All modules checked by default; only modules referenced in the active conditions checked.
**Rationale:** Mirrors the single-patient `defaultSelectedModules` logic (`ExportDialog.tsx:46`) — the user expects a sensible non-empty starting set. Conditions reference fields, not necessarily intent ("filter by Phe but I also want to see MS/MS C0/C2 alongside"), so binding defaults to conditions is too narrow.

### D7. Dialog state lives in `ConditionResults`, not lifted to `Index.tsx`
**Choice:** `useState<boolean>` for `exportOpen` inside `ConditionResults.tsx`. `Index.tsx` is unchanged.
**Rationale:** The dialog has no cross-component dependencies; lifting state would require new props and is gratuitous coupling.

## Risks / Trade-offs

- **Risk:** Wide sheets when modules carry many fields (`msms` has ~17 fields → 20 columns per sheet).
  → **Mitigation:** Acceptable in Excel (16k column limit) and in the long-format convention. Document; revisit only if clinicians complain.

- **Risk:** Row explosion for large cohorts × multi-record modules (e.g. 100 patients × 5 OPD records each = 500 rows in OPD sheet).
  → **Mitigation:** Well within Excel limits; no UI freezing because export is async and `xlsx.writeFile` runs in a single tick on the produced workbook. Re-evaluate if cohort sizes routinely exceed a few thousand patients.

- **Risk:** Refactor of `uniqueSheetName` / `todayStamp` accidentally regresses single-patient export.
  → **Mitigation:** Functions are small, pure, and have existing scenario coverage in the `patient-export` spec (XLSX sheet count, naming). Verify by running through that scenario after the move.

- **Risk:** Clinicians double-click "匯出比較報告" and start two exports.
  → **Mitigation:** `useFormStatus` in the dialog already disables the submit button while pending (mirrors `ExportDialog.tsx:67-74`). Entry button itself does not need a guard — clicking it just opens the modal idempotently.

- **Trade-off:** No cohort-stats export in v1. Clinicians who want both the comparison and the stats table must export the comparison and screenshot the stats. Acceptable for a first pass; a follow-up change can extend to the 族群統計 tab.

- **Trade-off:** No sub-table flattening means CAH_TGAL / DMD_TSH sub-results are not in the workbook. v1 deliberately scoped to declared `MODULE_FIELDS`; sub-tables would need a separate sheet design.
