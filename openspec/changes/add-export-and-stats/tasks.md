## 1. 依賴與環境

- [x] 1.1 在 `frontend/package.json` 新增依賴：`papaparse ^5.4.1`、`xlsx ^0.18.5`、`jszip ^3.10.1`
- [x] 1.2 在 `frontend/package.json` devDependencies 新增 `@types/papaparse ^5.3.15`
- [x] 1.3 執行 `cd frontend && npm install`，確認無衝突
- [x] 1.4 確認 `npm run typecheck` 在未改任何程式碼時仍通過（baseline）

## 2. 純函式工具層

- [x] 2.1 新增 `frontend/src/utils/statsUtils.ts`，實作 `mean`、`stddev`（n-1 分母）、`summarize`、`ageInYears`、`bucketAge`、`AGE_BUCKETS`、`filterByDateRange`、`filterByValueRange`、`extractNumericField`、`formatCell`
- [x] 2.2 新增 `frontend/src/utils/moduleDate.ts`，定義 `MODULE_DATE_FIELD: Record<ModuleId, string | null>`（參照 `patient.ts` 驗證過的欄位名）與 `getRecordDate` accessor
- [x] 2.3 新增 `frontend/src/utils/numericFields.ts`，匯出 `numericFieldsFor(moduleId)` 從 `MODULE_FIELDS` 過濾 `type === 'number'`
- [x] 2.4 新增 `frontend/src/utils/__tests__/statsUtils.test.ts`：覆蓋 `[12,14,16]`、`n=0`、`n=1`、`bucketAge` 邊界（17/18/59/60）、`ageInYears('invalid')`、`formatCell` 三種分支
- [x] 2.5 執行 `cd frontend && npm test` 全綠

## 3. 共用 UI

- [x] 3.1 新增 `frontend/src/components/stats/ModuleFieldPicker.tsx`：兩個 shadcn `Select`（模組 → 數值欄位），props 含 `value`、`onChange`、`patient?`（可選，供統計 Dialog 過濾「有資料」的模組）、`availableModules?`（供 cohort 使用）

## 4. Feature B：單病人統計

- [x] 4.1 新增 `frontend/src/components/stats/StatsSparkline.tsx`，使用 `recharts` LineChart（320×120px，依日期升冪排序，n<2 不渲染）
- [x] 4.2 新增 `frontend/src/components/stats/StatsDialog.tsx`：shadcn Dialog，內含 `ModuleFieldPicker`、日期區間（依 `MODULE_DATE_FIELD` 決定 disable + 提示）、數值區間、統計輸出、`StatsSparkline`、n=0 時顯示「無資料符合條件」
- [x] 4.3 編輯 `frontend/src/components/PatientSummary.tsx`：刪除內部 `calcAge`（line 13），改 `import { ageInYears } from '@/utils/statsUtils'`；在右上按鈕區加「統計」按鈕開啟 `StatsDialog`
- [ ] 4.4 手動驗證：對有 ≥3 筆 enzyme record 的病人選 `enzyme / MPS1`，日期欄位應 disable 並有提示；n/mean/sd/min/max 與手算一致，sparkline 不顯示（待人工執行；無 headless UI 環境）
- [ ] 4.5 手動驗證：對 `aadc / conc` 設日期區間過濾一筆 → n 下降 1，sparkline 隨之更新（待人工執行；無 headless UI 環境）

## 5. Feature A：匯出

- [x] 5.1 新增 `frontend/src/utils/exporters/jsonExporter.ts`：`exportJson(patient, modules, filename)`，以 `JSON.stringify(subset, null, 2)` 建 Blob 並下載；未選到的模組陣列設為 `[]`
- [x] 5.2 新增 `frontend/src/utils/exporters/csvExporter.ts`：對每個選到的模組用 `papaparse.unparse`（表頭使用 `MODULE_FIELDS[moduleId]` 的 `label`）產生 CSV，動態 `import('jszip')` 打包 + 附 `manifest.json`
- [x] 5.3 新增 `frontend/src/utils/exporters/xlsxExporter.ts`：動態 `import('xlsx')`，`json_to_sheet` 逐模組建 worksheet（sheet 名截到 31 字），以 `writeFile` 下載
- [x] 5.4 新增 `frontend/src/utils/exporters/index.ts` facade：`exportPatient(patient, { format, modules, filenamePrefix })` 依 `format` 分派
- [x] 5.5 新增 `frontend/src/components/export/ExportDialog.tsx`：format radio (CSV/JSON/XLSX)、模組 checkbox（預設勾有資料的模組）、全選／全不選 toggle、檔名前綴輸入（預設 `{chartno||externalChartno||nbsId||patientId}_{yyyyMMdd}`）、確認按鈕；若未勾任何模組則 disable 確認；動態 import 失敗時 `sonner`/`toast` 錯誤訊息
- [x] 5.6 編輯 `frontend/src/components/PatientSummary.tsx`：在「統計」按鈕旁加「匯出」按鈕開啟 `ExportDialog`
- [ ] 5.7 手動驗證：JSON 匯出可用 `JSON.parse` 重新 parse，未選模組陣列為 `[]`（待人工執行；無 headless UI 環境）
- [ ] 5.8 手動驗證：CSV zip 解壓後，每個 `.csv` 的 header 使用中文 label（如 `enzyme.csv` 含 `檢體類別`、`Enzyme-MPS2`）；含逗號的文字欄位正確雙引號包覆（待人工執行；無 headless UI 環境）
- [ ] 5.9 手動驗證：XLSX 在 Excel/LibreOffice 開啟，分頁數等於選到的模組數，名稱為模組 id（截 31 字內）（待人工執行；無 headless UI 環境）
- [x] 5.10 驗證 bundle：執行 `cd frontend && npm run build`，確認 `xlsx` 與 `jszip` 位於獨立 chunk 而非 entry（build 輸出顯示 `xlsx-*.js` 與 `jszip.min-*.js` 為獨立 chunk）

## 6. Feature C：族群統計

- [x] 6.1 新增 `frontend/src/components/stats/CohortStatsPanel.tsx`：`ModuleFieldPicker`、日期區間、數值區間、cohort 人數顯示、5×3 表格（列 `0-17|18-39|40-59|60+|全部年齡` × 欄 `男|女|全部性別`），每格 `formatCell(summarize(values))`；底部註腳「年齡以該筆紀錄的日期減去病人生日為準；若該模組無紀錄日期則以今日為準」
- [x] 6.2 `CohortStatsPanel` 內以 `useMemo` 聚合：走訪 cohort 每位病人的 `patient[moduleId]` → `getRecordDate` → `asOf = recordDate ?? new Date()` → `ageInYears` → `bucketAge`；數值經 `filterByDateRange`/`filterByValueRange`/`extractNumericField`；同時推入 `{bucket,sex}`、`{bucket,全部性別}`、`{全部年齡,sex}`、`{全部年齡,全部性別}` 四桶
- [x] 6.3 編輯 `frontend/src/components/ConditionResults.tsx`：把現有 chip 列 + 結果表格包進 shadcn `Tabs`，第一分頁 `名單` 維持現況、第二分頁 `族群統計` 渲染 `CohortStatsPanel`，`matchedPatients.map(m => m.patient)` 作為輸入
- [x] 6.4 確保 `CohortStatsPanel.tsx` 沒有 `from 'recharts'`（spec 要求）
- [ ] 6.5 手動驗證：條件 `enzyme.result = Deficient` → 族群統計 → `enzyme / MPS1`；「全部年齡 × 全部性別」cell 的 n 等於 cohort 中所有病人的 enzyme MPS1 有限值總數（以 DevTools Console 手算比對）（待人工執行）
- [ ] 6.6 手動驗證：名單分頁行為與 change 前完全一致（chips、列數、點列跳詳情）（待人工執行）

## 7. 品質關卡

- [x] 7.1 `cd frontend && npm run typecheck` 全綠
- [x] 7.2 `cd frontend && npm run lint` 全綠（或新增必要的 eslint-disable 並標註原因）
- [x] 7.3 `cd frontend && npm test` 全綠（含 `statsUtils.test.ts`）
- [x] 7.4 `cd frontend && npm run format:check` 通過
- [x] 7.5 `cd frontend && npm run build` 成功；檢查 chunk 分析輸出，確認 `xlsx`、`jszip` 不在 entry bundle
- [ ] 7.6 dev server (`npm run dev`) 煙囪測試：三個 feature 各走一次，無 console error（待人工執行）

## 8. 結尾

- [x] 8.1 `openspec validate add-export-and-stats --strict` 通過
- [ ] 8.2 PR 中附上三個手動驗證畫面截圖（匯出 dialog、stats dialog、族群統計表格）（待人工執行）
- [ ] 8.3 執行 `/opsx:archive` 歸檔此 change（俟手動驗證完成後執行）
