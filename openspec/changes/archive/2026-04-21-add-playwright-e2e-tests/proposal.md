## Why

前端 `frontend/` 雖已安裝 Playwright 1.57、CI workflow 的 `e2e` job 也已就位，但目前 `tests/` 目錄只有一支 `seed.spec.ts`（goto `/` + assert URL），等於沒有真正的回歸保護。此刻後端尚未建立，前端以 `src/data/mockData.ts` 的 5 位固定假病人驅動，**所有邏輯都在 client、資料確定**，是寫 E2E 最穩定的時機。

同時，Playwright 1.56 起官方推出 Test Agents（Planner / Generator / Healer），可透過 `npx playwright init-agents --loop=claude` 安裝，讓 Claude Code 自動探索 app、產生 specs 與測試、並在失敗時自動修復選擇器。採用官方方案可大幅降低人工維護選擇器的成本，也讓後端上線後的測試演進更平順。

## What Changes

- 執行 `npx playwright init-agents --loop=claude`，在 `frontend/` 安裝 Playwright 官方 Test Agents 定義（Planner、Generator、Healer）與 Playwright MCP 設定
- 升級 `frontend/playwright.config.ts`：補上 `projects`（明定 chromium）、`trace: 'on-first-retry'`、`screenshot: 'only-on-failure'`、`video: 'retain-on-failure'`、`retries`（CI=2、local=0）、`workers`（CI=1）、`timeout`、`expect.timeout`、`actionTimeout`、`navigationTimeout`、`outputDir: './test-results'`、`webServer.timeout: 120_000`、`forbidOnly`、`fullyParallel`
- 為 `frontend/package.json` 新增 5 個 scripts：`test:e2e`、`test:e2e:ui`、`test:e2e:debug`、`test:e2e:headed`、`test:e2e:report`
- 保留 `frontend/tests/seed.spec.ts`（Test Agents 要求的互動起點）
- 使用 Planner 產生 `frontend/specs/*.md` 的 Markdown 測試計畫（5-7 個核心 happy path）
- 使用 Generator 產生 `frontend/tests/*.spec.ts` 的 Playwright 測試程式
- 使用 Healer 執行並修復測試直到全綠
- 不新增任何 `data-testid`；選擇器採純 `getByRole` / `getByText` / `getByPlaceholder`
- 只跑 Chromium（不啟用 Firefox、WebKit）

## Capabilities

### New Capabilities

- `e2e-testing`：定義 E2E 測試的產生與維運流程（採用 Playwright Test Agents）、Playwright 設定基準、可執行的 npm scripts、涵蓋的核心使用者流程（5-7 個 happy path）、以及 mock data 穩定性的要求

### Modified Capabilities

<!-- 無。現有 `ci-pipeline` 的 Playwright E2E 測試 requirement 已涵蓋 CI 層行為（`npx playwright install --with-deps chromium`、`npx playwright test`、失敗時上傳 report）。本次 change 不改動 CI workflow 或 `ci-pipeline` 的 spec-level 行為。 -->

## Impact

- **新增檔案**：
  - `frontend/.claude/agents/playwright-test-{generator,healer,planner}.md`（已驗證為 init-agents 實際輸出路徑）
  - `frontend/specs/*.md`（由 Planner 產生）
  - `frontend/tests/*.spec.ts`（由 Generator 產生；除保留的 `seed.spec.ts`）
  - `frontend/.mcp.json`（已驗證：init-agents 註冊 `playwright-test` MCP server，使用 `npx playwright run-test-mcp-server`）
- **修改檔案**：
  - `frontend/playwright.config.ts`（擴充設定）
  - `frontend/package.json`（新增 5 個 scripts）
- **不變動**：
  - 應用程式 source code（`frontend/src/**/*`）— 不加 `data-testid`
  - `.github/workflows/ci.yml` — 現有 `e2e` job 與 `ci-pipeline` spec 已符合需求
  - `.gitignore` — `frontend/.gitignore:16-19` 已含 `test-results/`、`playwright-report/`、`blob-report/`、`playwright/.cache/`
  - vitest 設定（`vitest.config.ts`、`src/test/setup.ts`、`src/test/example.test.ts`）— 與 Playwright 互不干涉
- **相依套件**：不新增 npm 套件；`@playwright/test` 1.57 已存在。已驗證 Playwright MCP server 由 `init-agents` 設定為 `npx playwright run-test-mcp-server` 動態呼叫，不需 `npm install @playwright/mcp`
- **對 CI 成本**：現有 `e2e` job 執行時間會因測試數量由 1 支增至 5-7 支而略增（預估 +30-60 秒），仍遠低於 build 與 npm ci 的時間
- **對開發者**：日後新增 E2E 測試的 SOP 為「更新或新增 `specs/*.md` → 叫 Generator → 叫 Healer 修綠」，而非手寫 spec 檔
