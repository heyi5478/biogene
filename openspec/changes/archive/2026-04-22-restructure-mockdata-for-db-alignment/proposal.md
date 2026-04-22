## Why

即將開發的 Python/FastAPI 後端（見 [PLAN.md](../../../PLAN.md)）需要可直接讀取的 mock data，而目前 [frontend/src/data/mockData.ts](../../../frontend/src/data/mockData.ts) 是 5 位假病人的單一扁平 `Patient[]`，與真實 MySQL 架構（`2.0`、`2.0 外院資料庫`、`new_born_screening` 三個資料庫，多 table 名稱重疊但語意不同）落差太大；同時缺少 NBS 專屬模組（bd / cah+tgal / dmd+tsh / g6pd / sma_scid），且以 `chartno` 為主鍵無法承載「無病歷號」的外院病人。本次調整建立可被前後端共用的 JSON mock，對齊真實 schema，讓後端從 day-1 就用得上、前端 UI 不破壞，未來換成真 DB 只需替換 repository 層。

## What Changes

- **新增** `backend/mock-data/{db_main,db_external,db_nbs}/*.json`：依資料庫/table 拆檔，共約 36 個 JSON 檔，作為前後端共用的 single source of truth。
- **新增** `backend/scripts/generate_mock.py`：deterministic UUID v5 產生器（種子 = `f"{source}:{naturalKey}"`），重新產生 mock 時 `patientId` 與 FK 維持穩定。
- **新增** `backend/scripts/load_mock.py`：JSON FK 完整性驗證器（patient FK、cah/dmd sub-table FK），並可被 FastAPI startup 共用。
- **新增** 5 個 NBS 專屬模組型別與 UI 區塊：`bd`、`cah`（含 `tgal` sub-rows）、`dmd`（含 `tsh` sub-rows）、`g6pd`、`smaScid`；並在 [medical.ts](../../../frontend/src/types/medical.ts) `MODULE_DEFINITIONS` 新增 `'nbs'` group。
- **BREAKING** `Patient` 介面：新增 `patientId`（UUID v5，新主鍵）、`source`（`'main' | 'external' | 'nbs'`）、`externalChartno?`、`nbsId?`、`category?`、`linkedPatientIds?`；`chartno` 與 `diagnosis` 改 optional。所有 sample 表用 `patientId` 為 FK，**不再用** `chartno`。
- **改寫** [frontend/src/data/mockData.ts](../../../frontend/src/data/mockData.ts)：從 570 行 inline 資料改為 ~80 行 JSON import + `patientId` join，輸出的 `mockPatients: Patient[]` shape 不變。
- **修改** [ConditionResults.tsx](../../../frontend/src/components/ConditionResults.tsx)、[PatientSummary.tsx](../../../frontend/src/components/PatientSummary.tsx)、[ResultModules.tsx](../../../frontend/src/components/ResultModules.tsx)、[Index.tsx](../../../frontend/src/pages/Index.tsx)：支援 nullable chartno（fallback 到 `externalChartno`/`nbsId`）、加入 NBS 模組渲染與條件查詢、新增 `'nbs'` tab、`<TableRow key>` 改用 `patientId`。

## Capabilities

### New Capabilities

- `mock-data-layer`: JSON-based mock data system，依真實資料庫/table 結構組織於 `backend/mock-data/`，作為前後端共用的 single source of truth；含 deterministic UUID v5 產生器與 FK 完整性驗證器。
- `nbs-screening-modules`: 新生兒篩檢專屬 5 個模組（bd、cah+tgal、dmd+tsh、g6pd、sma_scid）的型別、欄位、UI 渲染與條件查詢支援；`MODULE_DEFINITIONS` 新增 `'nbs'` group，UI 新增 `'nbs'` tab。

### Modified Capabilities

<!-- 目前 openspec/specs/ 下只有 ci-pipeline 與 e2e-testing，與本次變動無關。Patient 識別與 mock data 結構是首次以 spec 形式建立，皆放入 New Capabilities。 -->

## Impact

- **修改檔案（前端）**：[frontend/src/types/medical.ts](../../../frontend/src/types/medical.ts)、[frontend/src/data/mockData.ts](../../../frontend/src/data/mockData.ts)、[frontend/src/pages/Index.tsx](../../../frontend/src/pages/Index.tsx)、[frontend/src/components/ConditionResults.tsx](../../../frontend/src/components/ConditionResults.tsx)、[frontend/src/components/PatientSummary.tsx](../../../frontend/src/components/PatientSummary.tsx)、[frontend/src/components/ResultModules.tsx](../../../frontend/src/components/ResultModules.tsx)
- **新增檔案（後端 mock seed + scripts）**：`backend/mock-data/db_main/*.json`（14 檔）、`backend/mock-data/db_external/*.json`（9 檔）、`backend/mock-data/db_nbs/*.json`（13 檔，含 sub-tables）、`backend/scripts/generate_mock.py`、`backend/scripts/load_mock.py`
- **不變動**：[FilterPanel.tsx](../../../frontend/src/components/FilterPanel.tsx)、[SearchSummary.tsx](../../../frontend/src/components/SearchSummary.tsx)（不讀 sample 陣列）、`vite.config.ts`（proxy 設定屬於 [PLAN.md](../../../PLAN.md) Step 3，不在本範圍）、後端 FastAPI 服務本身（屬 PLAN.md Step 5–6）
- **API 影響**：本次只建立 mock data 與型別。後端 API 端點（`/api/query/*`、`/api/patient-detail/*`）未在此 change 中實作；但 mock data 的 schema 即未來 API response 的 schema，會被後續 svc-patient/svc-lab/svc-disease 直接消費。
- **相依套件**：無新增。後端 scripts 僅用 Python 標準庫（`json`、`uuid`、`pathlib`）。
- **風險**：(1) JSON join loader 若邏輯錯，會破壞既有條件查詢 → 由 §G 驗證流程（既有 condition templates 命中數比對）把關；(2) `Patient` 型別變動可能讓未列入清單的元件 type-check fail → 由 `npx tsc --noEmit` 把關；(3) NBS sub-table（tgal/tsh）資料量稀少時 UI 可能出現空 section → ResultModules 加 `length === 0` guard。
- **後續銜接**：本 change 完成後，[PLAN.md](../../../PLAN.md) Step 5–6（建立 4 個 FastAPI 服務）可直接讀取本次產出的 JSON；Pydantic schemas 對應本次更新後的 [medical.ts](../../../frontend/src/types/medical.ts) 結構。
