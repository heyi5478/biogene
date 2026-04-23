## Why

前端已可瀏覽單一病人的檢驗資料、也可用條件查詢篩出符合病人，但目前**沒有任何匯出或統計功能**。使用者（研究／臨床端）希望能把病人多筆資料帶走做離線分析，並能直接在 UI 上得到基本描述統計（mean / SD / 範圍），尤其是「enzyme 缺乏病人，依性別與年齡分層 mean ± SD」這類族群分析，目前只能手動對 JSON 算。

## What Changes

- 新增**匯出**能力：在 `PatientSummary` 卡片加「匯出」按鈕，可選 CSV（每模組一個檔 + zip）、JSON（完整 PatientBundle）、XLSX（每模組一個工作表）三種格式，並可選擇要匯出的模組
- 新增**單病人統計**能力：`PatientSummary` 增「統計」按鈕；Dialog 讓使用者選模組 + 數值欄位，套用可選的日期區間與數值區間，輸出 n / mean / SD / min / max；當模組有日期欄位且 n ≥ 2 時，附上 Recharts sparkline
- 新增**族群統計**能力：`ConditionResults` 包成 Tabs，第二分頁「族群統計」以 cohort（條件查詢結果）為輸入，依固定年齡分層（0-17, 18-39, 40-59, 60+）× 性別（男／女）× 邊際合計，輸出 `mean ± SD (n=k)` 的 5×3 表格
- 新增純函式工具：`statsUtils`（mean, stddev, summarize, ageInYears, bucketAge, filter*）、`moduleDate` registry（`MODULE_DATE_FIELD`）、`numericFields` helper；都放在 `frontend/src/utils/`
- 新增依賴：`papaparse`（eager）、`xlsx` / `jszip`（皆動態 import 以控制初始 bundle）

**不做**：後端任何變動、伺服器端聚合、跨模組單位換算、族群統計的圖表（僅表格）、匯出偏好的持久化、新增 route。

## Capabilities

### New Capabilities
- `patient-export`: 將單一病人的多模組檢驗資料匯出為 CSV／JSON／XLSX，並可選模組子集
- `patient-statistics`: 對單一病人、指定模組 + 數值欄位，於可選日期與數值區間內計算描述性統計；若資料含日期則顯示時序 sparkline
- `cohort-statistics`: 以條件查詢結果為 cohort，依固定年齡分層 × 性別輸出 `mean ± SD (n=k)` 的交叉表（含邊際合計）

### Modified Capabilities
（無——既有 `frontend-patient-data` 的 requirements 皆保持成立：`usePatients()` 契約、條件查詢結果同位、camelCase 型別等全部不變；本次僅是在既有元件裡新增 UI 入口，不改變任何既有 scenario）

## Impact

- **新增檔案**：
  - `frontend/src/utils/statsUtils.ts`、`moduleDate.ts`、`numericFields.ts`
  - `frontend/src/utils/exporters/{index,jsonExporter,csvExporter,xlsxExporter}.ts`
  - `frontend/src/components/stats/{ModuleFieldPicker,StatsDialog,StatsSparkline,CohortStatsPanel}.tsx`
  - `frontend/src/components/export/ExportDialog.tsx`
  - `frontend/src/utils/__tests__/statsUtils.test.ts`
- **修改檔案**：
  - `frontend/src/components/PatientSummary.tsx`（加入口按鈕，把既有 `calcAge` 移除改 import 自 `statsUtils`）
  - `frontend/src/components/ConditionResults.tsx`（包 Tabs、加「族群統計」分頁）
  - `frontend/package.json`（新依賴 `papaparse`、`xlsx`、`jszip`、`@types/papaparse`）
- **不動**：`Index.tsx`、`FilterPanel.tsx`、`usePatients.ts`、`backend/**`
- **bundle**：初始 bundle 增 ~20KB gzip（papaparse）；XLSX / ZIP 路徑動態載入，首次點擊時 lazy-load ~440KB gzip
- **風險**：多數檢驗模組（enzyme / lsd / aa / msms / biomarker / mps2 / gag）在 TS 型別上無採檢日期欄位——日期過濾與 sparkline 對這些模組不可用，UI 需明示限制；族群統計的年齡在無記錄日期時退回「今天」
