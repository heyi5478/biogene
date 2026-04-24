## 1. Planner → 測試計畫

- [x] 1.1 於 `frontend/` 啟動 dev server（或確保 port 8080 空閒讓 Planner 自行透過 Playwright MCP 啟動）
- [x] 1.2 呼叫 `playwright-test-planner` subagent，prompt 要點：
  - 目標 URL：`http://localhost:8080`
  - 三功能概述（匯出 / 單病人統計 / 族群統計）與對應 selector 提示
  - 三個匯出格式各一 scenario；每個 scenario 都要寫清楚 `page.waitForEvent('download')` 與 `download.suggestedFilename()` 的驗證點
  - 格式對齊 `frontend/specs/core-happy-paths.md`
  - 輸出檔名：`frontend/specs/export-and-stats.md`
  - 排除 edge case（錯誤輸入、鍵盤導航、RWD、multi-browser、visual regression）
- [x] 1.3 review 產出：5 個 scenario、對應三功能，不包含排除項

## 2. Generator → 逐支產生 spec 檔

- [x] 2.1 對 scenario 1（CSV）呼叫 `playwright-test-generator`，產出 `frontend/tests/patient-export-csv.spec.ts`
- [x] 2.2 對 scenario 2（JSON）呼叫 generator，產出 `frontend/tests/patient-export-json.spec.ts`
- [x] 2.3 對 scenario 3（XLSX）呼叫 generator，產出 `frontend/tests/patient-export-xlsx.spec.ts`
- [x] 2.4 對 scenario 4（單病人統計）呼叫 generator，產出 `frontend/tests/patient-stats-dialog.spec.ts`
- [x] 2.5 對 scenario 5（族群統計）呼叫 generator，產出 `frontend/tests/cohort-stats-tab.spec.ts`
- [x] 2.6 review 每支產出：
  - [x] locator 全為 `getByRole` / `getByText` / `getByPlaceholder` / `getByLabel`
  - [x] 進到 Dialog 後用 `page.getByRole('dialog')` scope，避免「匯出」字串與 PatientSummary 觸發鈕衝突
  - [x] Radix `Select` 選項以 `page.getByRole('option', { name: ... })` 選取（portal 渲染）
  - [x] download 測試使用 `Promise.all([page.waitForEvent('download'), ...click])` 模式
  - [x] 每個 `test()` 以 `page.goto('/')` 起頭

## 3. Healer → 修綠

- [x] 3.1 於 `frontend/` 執行 `npm run test:e2e`，記錄失敗清單
- [x] 3.2 對失敗測試呼叫 `playwright-test-healer`，每次指定一支 `.spec.ts` 與失敗訊息
- [x] 3.3 Healer 修完重跑，直到 6 原有 + 5 新測試全綠
- [x] 3.4 若某 scenario 無法穩定，允許 healer 以 `test.fixme()` 暫標並留詳盡註解

## 4. 驗證

- [x] 4.1 於 `frontend/` 執行 `npm run lint` 通過
- [x] 4.2 於 `frontend/` 執行 `npm run format:check` 通過
- [x] 4.3 於 `frontend/` 執行 `npm run typecheck` 通過
- [x] 4.4 於 `frontend/` 執行 `npm run test:e2e` 本機全綠（至少 11 passed）
- [x] 4.5 於 `frontend/` 以 `workers=1 retries=2` 模擬 CI 再跑一次
- [x] 4.6 `openspec validate add-export-and-stats-e2e-tests --strict` 無錯
- [x] 4.7 `git diff main -- frontend/src` 與 `git diff main -- .github/workflows/ci.yml` 皆為空（未動 production code 與 CI）

## 5. 提交

- [x] 5.1 依工作邏輯拆 commit：
  - `docs(e2e): add Planner-generated plan for export and stats`（Section 1）
  - `test(e2e): add patient export spec files (csv/json/xlsx)`（Section 2.1–2.3）
  - `test(e2e): add patient stats dialog spec`（Section 2.4）
  - `test(e2e): add cohort stats tab spec`（Section 2.5）
  - `test(e2e): apply Healer fixes for export and stats specs`（Section 3，如有）
- [x] 5.2 推送 branch、開 PR 目標為 `main`，等 CI 全綠
- [x] 5.3 Merge 後執行 `/opsx:archive add-export-and-stats-e2e-tests` 歸檔
