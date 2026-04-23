## Context

本專案是罕病／新生兒篩檢資料管理系統：FastAPI gateway（port 8000）+ Vite/React 19/TS 前端。前端已能單點檢視病人多模組檢驗、以及用條件查詢（`evaluateConditions`）找出符合 cohort。病人資料一次載入 (`usePatients()` TanStack Query) 為 `Patient[]`，每位病人包含 `sex`、`birthday` 與各模組的 record 陣列。

**關鍵背景（來自 `frontend/src/types/patient.ts` 審查）**：檢驗模組中，`opd.visitDate`、`aadc.date?`、`ald.date?`、`mma.date?`、`outbank.shipdate`、新生兒篩檢系列 `.collectDate` 有日期欄位；但 `aa`、`msms`、`biomarker`、`enzyme`、`lsd`、`mps2`、`gag`、`dnabank` **在型別上根本沒有日期欄位**——只有 `sampleName`。

各模組的欄位清單（含型別與中文 label）已集中在 `frontend/src/types/medical.ts:312-527` 的 `MODULE_FIELDS`——本次所有 UI 的「可選欄位」全部重用這個來源。

## Goals / Non-Goals

**Goals**
- 三個獨立但共用工具的能力：patient-export、patient-statistics、cohort-statistics
- 所有統計計算在前端進行（資料已載入），不增加後端端點
- 純函式層（`statsUtils`、`moduleDate`、`numericFields`）必須 framework-agnostic、可單獨單元測試
- UI 面上，所有入口維持在既有頁面內（`PatientSummary`、`ConditionResults`），**不新增 route**
- 初始 bundle 增量最小：XLSX／ZIP 皆以動態 `import()` 延遲載入

**Non-Goals**
- 不做伺服器端聚合／查詢
- 族群統計**不做圖表**（僅表格；Recharts 已裝留給日後）
- 不做跨模組單位換算，也不試圖整合不同單位的欄位
- 不持久化使用者的匯出／統計偏好（每次 Dialog 重置）
- 不改後端 schema、不改 `Patient` 型別
- 不改既有查詢行為（名單分頁 = 目前行為 100% 不動）

## Decisions

### D1. 日期欄位 registry 集中化而非到處寫 switch
**Decision**：在 `frontend/src/utils/moduleDate.ts` 定義 `MODULE_DATE_FIELD: Record<ModuleId, string | null>`，並提供 `getRecordDate(moduleId, rec)` accessor。

**Rationale**：日期欄位散落各模組且名稱不一（`visitDate` / `date` / `collectDate` / `shipdate`），多處檢驗模組根本沒有。集中成 registry 有三個好處：(1) UI 判斷「是否 disable 日期區間」只看一張表；(2) 未來後端補上 `sampleDate` 時只改一處；(3) 測試只需 mock 這個 registry。

**Alternatives considered**：在每個 export/stats 呼叫點用 `switch(moduleId)` 取日期——重複度高、同步容易漏。

### D2. 數值欄位來源一律從 `MODULE_FIELDS` 過濾，不自己列舉
**Decision**：`numericFields.ts` 只提供 `numericFieldsFor(moduleId) = MODULE_FIELDS[moduleId].filter(f => f.type === 'number')`。

**Rationale**：避免雙重維護（`medical.ts` 已是欄位 schema 的 source of truth，`ConditionBuilder` 也從這裡拉清單）。任何新欄位加進 `MODULE_FIELDS` 都自動出現在統計選單。

### D3. XLSX／JSZip 用動態 import，papaparse 用 eager
**Decision**：
- `papaparse` 靜態 import（~20KB gzip）
- `xlsx`（~350KB）、`jszip`（~95KB）只在 `csvExporter` / `xlsxExporter` 的 export function 內部 `await import('xlsx')` / `await import('jszip')`

**Rationale**：使用者大多不會點匯出；初始 bundle 不該為此膨脹 440KB。papaparse 很小且 CSV 欄位格式化常用，不延遲載入以簡化程式。

**Trade-off**：第一次按匯出會有一次 lazy-load 延遲（~幾百 ms，本機環境），以 loading indicator 處理。

### D4. 樣本標準差（n-1 分母），不是母體
**Decision**：`stddev` 使用 `sqrt(Σ(x-mean)² / (n-1))`；n < 2 時回 `null`。

**Rationale**：所有已收集資料都是「樣本」而非整體母體，臨床與研究約定使用樣本 SD。n=1 無法計算 SD，回 null 比回 0 更誠實。

### D5. 族群統計的年齡 `asOf`：優先用記錄日期，退回今天
**Decision**：對每筆 record 計算 `age = ageInYears(patient.birthday, recordDate ?? today)`，再送入 `bucketAge`；`recordDate` 取自 `getRecordDate(moduleId, rec)`。

**Rationale**：醫學上年齡應以採樣當下為準。但對無日期欄位的模組（enzyme/lsd 等），沒其他選擇；用今天做近似，並在 panel 下方加註腳讓使用者知道。

**Alternatives considered**：
- 僅用今天：在長時間追蹤的病人上誤差可觀
- 要求一定有日期：直接排除一半模組不合理，enzyme 是使用者主要需求

### D6. 固定年齡分層而非使用者自訂
**Decision**：`AGE_BUCKETS = ['0-17', '18-39', '40-59', '60+']`（使用者已確認）。上界 inclusive。

**Rationale**：醫學常用切點、UI 極簡、表格可預先定死 5×3 欄位，容易閱讀與測試。使用者自訂 bucket 留作日後延伸。

### D7. 族群統計維持表格，不做圖表
**Decision**：僅以 `Table` 呈現 5×3 grid（含 `全部年齡` × `全部性別` 邊際）。

**Rationale**：使用者問題核心是「能看到數字」；圖表會引入色票、對比、資料密度等選擇，徒增範圍。Recharts 已經裝好，日後加 bar chart 代價很低。

### D8. 入口按鈕位置：PatientSummary 而非 ResultModules
**Decision**：「匯出」「統計」按鈕放在 `PatientSummary` 卡片右上角，緊鄰既有的 quick-jump chip。族群統計入口以 shadcn `Tabs` 放進 `ConditionResults`。

**Rationale**：
- `ResultModules` 是一個 flat list，沒有天然的 header 可放按鈕
- `PatientSummary` 是病人頁面唯一的「病人級別」元件，把病人級別操作放這裡語意最一致
- 族群操作天然屬於 cohort 結果頁，放 `ConditionResults` 的 Tabs 符合使用者心智路徑

### D9. 檔名格式 `{chartno||patientId}_{yyyyMMdd}.{ext}`
**Decision**：`ExportDialog` 預設檔名以 `patient.chartno ?? patient.externalChartno ?? patient.nbsId ?? patient.patientId` 為前綴，接當日日期。使用者可在 Dialog 輸入框覆寫。

**Rationale**：使用者常同時匯多位病人，預設含識別碼可避免覆蓋。`chartno` 在研究／臨床通訊中是主要識別，最不會混淆。

### D10. 邊界行為一律以 null 表達缺值，UI 以 `—` 呈現
**Decision**：`mean([]) = null`、`stddev(n<2) = null`、`ageInYears(invalid) = null`、`bucketAge(null) = null`。`formatCell`：
- `n = 0` → `—`
- `n = 1` → `v (n=1)`（無 SD）
- `n ≥ 2` → `mean ± sd (n=k)`

**Rationale**：前端其他處已使用 `—` 代表無資料，一致性優先。區分 n=0／n=1／n≥2 才能避免「0 ± 0 (n=0)」這種誤導顯示。

## Risks / Trade-offs

- **風險**：多數檢驗模組沒有日期欄位 → 日期區間過濾對 enzyme 等主要分析目標不可用
  → **緩解**：UI 明確 disable 日期輸入並顯示提示「此模組資料無採檢日期欄位」；族群統計加註腳說明年齡退回以今天為準；`moduleDate.ts` 作為未來補欄位的 single point of change

- **風險**：XLSX dynamic import 首次點擊會有延遲
  → **緩解**：點擊後立刻顯示 loading spinner；失敗重試機制（catch 後顯示 toast）

- **風險**：極小 cohort（n=1 或 n=2）時 SD 不穩定
  → **緩解**：`formatCell` 明確區分 n=0／1／≥2 的呈現，使用者自己能判斷

- **風險**：`calcAge` 目前在 `PatientSummary.tsx:13` 已存在一份
  → **緩解**：這次把它移到 `statsUtils.ageInYears`，`PatientSummary` 改 import；統一實作避免日後歧異

- **Trade-off**：族群統計一次只能選一組 module + field，無法同時看多個指標
  → 接受；多指標對比引入 UI 與資料對齊複雜度，不在這次範圍

- **Trade-off**：匯出不支援「多位病人合併」
  → 接受；使用者最核心需求是「單一病人多筆資料」；合併匯出留作日後（族群資料匯出功能）

## Migration Plan

無資料遷移。實作順序：

1. 加依賴並驗證 `npm install` 通過
2. 純函式層（`statsUtils` + 測試、`moduleDate`、`numericFields`）
3. 共用 UI：`ModuleFieldPicker`
4. Feature B（`StatsDialog` + `StatsSparkline`） + `PatientSummary` 接「統計」按鈕 + 把 `calcAge` 抽到 `statsUtils`
5. Feature A（`jsonExporter` → `csvExporter` → `xlsxExporter` + `ExportDialog`） + `PatientSummary` 接「匯出」按鈕
6. Feature C（`CohortStatsPanel`） + 把 `ConditionResults` 包進 Tabs
7. `npm run typecheck && npm run lint && npm test` 全綠

回復策略：每個 feature 是獨立 commit，任一有問題可個別 revert。

## Open Questions

（無——使用者已於 plan 階段確認格式、區間語意、年齡分層策略）
