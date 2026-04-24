## Why

已封存的 change `2026-04-23-add-export-and-stats` 為前端新增三個使用者面向功能：單病人匯出（CSV zip / JSON / XLSX）、單病人統計（StatsDialog）、族群統計（CohortStatsPanel tab）。目前 `frontend/tests/` 僅有 6 支由前一個 change 產生的核心 happy-path 測試，這三個新功能完全沒有 e2e 覆蓋，也沒有任何檔案下載驗證先例。

`frontend/.claude/agents/` 已安裝 Playwright Test Agents（Planner / Generator / Healer）與 `frontend/.mcp.json` 的 `playwright-test` MCP server，可直接沿用。本次 change 的責任是按照既有 SOP「Planner → Generator → Healer」產出並合入這三個新功能的 e2e 測試，同時建立本 repo 首批 download 測試的範例，讓後續任何匯出/下載類功能都有可照抄的樣板。

## What Changes

- 以 Planner agent 產出 `frontend/specs/export-and-stats.md`：涵蓋 5 個 scenario，分別對應三個匯出格式、單病人 StatsDialog、族群統計 tab
- 以 Generator agent 產出 5 支 `frontend/tests/*.spec.ts`：
  - `patient-export-csv.spec.ts`：CSV 匯出，驗證 `.zip` 下載 + `{chartno}_{yyyyMMdd}` 檔名前綴
  - `patient-export-json.spec.ts`：JSON 匯出，驗證 `.json` 下載
  - `patient-export-xlsx.spec.ts`：XLSX 匯出，驗證 `.xlsx` 下載
  - `patient-stats-dialog.spec.ts`：PatientSummary「統計」按鈕 → StatsDialog 模組/欄位選擇、無日期模組的 disabled 行為、n/mean/sd/min/max 顯示
  - `cohort-stats-tab.spec.ts`：條件查詢套用「酵素活性低下」模板 → 切「族群統計」tab → 選模組+欄位 → 5×3 年齡桶×性別交叉表
- 以 Healer agent 修補任何因選擇器、portal、animation timing 造成的失敗，直到 `npm run test:e2e` 全綠
- 建立 `page.waitForEvent('download')` 的實作樣板，供未來匯出類測試參考
- **不** 新增 `data-testid`，延續既有「禁用 testid、只用語意選擇器」的 repo 規範
- **不** 修改 `frontend/playwright.config.ts`、`frontend/package.json` 或 CI workflow

## Capabilities

### Modified Capabilities

- `e2e-testing`：在既有 8 項 Requirement 之外，新增「匯出功能 e2e 覆蓋」、「統計功能 e2e 覆蓋」、「下載事件斷言策略」三條 Requirement，擴充核心使用者流程矩陣並納入 download 驗證規範

## Impact

- **新增檔案**：
  - `frontend/specs/export-and-stats.md`（由 Planner 產生的測試計畫）
  - `frontend/tests/patient-export-csv.spec.ts`
  - `frontend/tests/patient-export-json.spec.ts`
  - `frontend/tests/patient-export-xlsx.spec.ts`
  - `frontend/tests/patient-stats-dialog.spec.ts`
  - `frontend/tests/cohort-stats-tab.spec.ts`
- **修改檔案**：無（不動 playwright.config.ts、package.json、CI workflow、任何 production code）
- **相依套件**：不新增 npm 套件
- **對 CI 成本**：e2e job 新增 5 支測試，預估 +20-40 秒（CI 下 `workers: 1`、`retries: 2`）；仍遠低於 build 與 npm ci 的時間
- **對開發者**：本 change 同時建立 download 斷言樣板（`page.waitForEvent('download')` + `download.suggestedFilename()`），日後任何匯出類功能 SOP 可直接照抄三支匯出 spec
