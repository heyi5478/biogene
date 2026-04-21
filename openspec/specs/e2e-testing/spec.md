# e2e-testing Specification

## Purpose
TBD - created by archiving change add-playwright-e2e-tests. Update Purpose after archive.
## Requirements
### Requirement: Playwright Test Agents 安裝

專案 SHALL 透過 `npx playwright init-agents --loop=claude` 安裝 Playwright 官方 Test Agents 定義到 `frontend/` 底下，提供 Planner、Generator、Healer 三個 agent 供 Claude Code 呼叫。agent 定義檔案 MUST 被 commit 進版本控制。

#### Scenario: Agent 定義檔存在於 repo
- **WHEN** 讀取 `frontend/` 底下 `init-agents` 產出的路徑（例如 `.claude/agents/`、`.claude/skills/` 或 `.claude/commands/`，以實際輸出為準）
- **THEN** Planner、Generator、Healer 三個 agent 定義檔 SHALL 存在且已 commit

#### Scenario: Playwright 版本滿足最低需求
- **WHEN** 讀取 `frontend/package.json` 的 `devDependencies`
- **THEN** `@playwright/test` 版本 SHALL >= `1.56.0`

#### Scenario: 升級 Playwright 時同步更新 agent 定義
- **WHEN** `@playwright/test` 版本在 `package.json` 中被更新
- **THEN** 同一 PR MUST 包含重跑 `npx playwright init-agents --loop=claude` 的產出

### Requirement: Playwright 設定基準

`frontend/playwright.config.ts` SHALL 定義以下欄位，以確保測試執行的穩定性、可除錯性與 CI 相容性：

- `testDir: './tests'`
- `fullyParallel: true`
- `forbidOnly: !!process.env.CI`
- `retries: process.env.CI ? 2 : 0`
- `workers: process.env.CI ? 1 : undefined`
- `timeout: 30_000`
- `expect.timeout: 5_000`
- `outputDir: './test-results'`
- `reporter` 至少包含 `html`（既有）
- `use.baseURL: 'http://localhost:8080'`
- `use.trace: 'on-first-retry'`
- `use.screenshot: 'only-on-failure'`
- `use.video: 'retain-on-failure'`
- `use.actionTimeout: 10_000`
- `use.navigationTimeout: 15_000`
- `projects` 陣列至少含一個 `{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }`
- `webServer.command: 'npm run dev'`
- `webServer.url: 'http://localhost:8080'`
- `webServer.reuseExistingServer: !process.env.CI`
- `webServer.timeout: 120_000`

#### Scenario: 本機執行不 retry、並行跑
- **WHEN** 開發者於本機以預設環境變數執行 `npx playwright test`
- **THEN** Playwright SHALL 以 `retries=0` 與預設 workers（並行）執行

#### Scenario: CI 環境執行 retry、單 worker
- **WHEN** `CI=1` 時執行 `npx playwright test`
- **THEN** Playwright SHALL 以 `retries=2` 與 `workers=1` 執行

#### Scenario: 失敗時保留 trace / screenshot / video
- **WHEN** 任一測試失敗
- **THEN** Playwright SHALL 產生該測試的 trace（在第一次 retry 時）、screenshot 與 video，輸出到 `./test-results/`

#### Scenario: 只跑 Chromium
- **WHEN** `npx playwright test` 執行
- **THEN** 唯一執行的 project SHALL 為 `chromium`

#### Scenario: webServer cold boot 有足夠時間
- **WHEN** CI 環境首次啟動 Vite dev server
- **THEN** Playwright SHALL 等待最多 `120_000` ms，確認 `http://localhost:8080` 可回應後才開始測試

### Requirement: npm scripts

`frontend/package.json` 的 `scripts` 欄位 SHALL 包含以下 5 個 E2E 相關 script，便於開發者快速呼叫不同 Playwright 模式：

- `test:e2e`: `playwright test`
- `test:e2e:ui`: `playwright test --ui`
- `test:e2e:debug`: `playwright test --debug`
- `test:e2e:headed`: `playwright test --headed`
- `test:e2e:report`: `playwright show-report`

既有的 `test`（`vitest run`）與 `test:watch`（`vitest`）SHALL 保持不變。

#### Scenario: scripts 存在且指令正確
- **WHEN** 讀取 `frontend/package.json` 的 `scripts`
- **THEN** 上述 5 個 key SHALL 存在，且對應 value 與規格一致

#### Scenario: vitest scripts 未被覆蓋
- **WHEN** 讀取 `scripts.test` 與 `scripts.test:watch`
- **THEN** 其 value SHALL 分別為 `vitest run` 與 `vitest`

### Requirement: Seed 測試保留

`frontend/tests/seed.spec.ts` SHALL 保留作為 Playwright Test Agents 的互動起點。其內容 MUST 至少包含一次 `page.goto('/')` 與一個對 baseURL 的斷言。

#### Scenario: Seed 檔存在
- **WHEN** 讀取 `frontend/tests/seed.spec.ts`
- **THEN** 檔案 SHALL 存在

#### Scenario: Seed 測試可執行且通過
- **WHEN** 以 `npx playwright test tests/seed.spec.ts` 執行
- **THEN** 該測試 SHALL 在 Chromium 上通過

### Requirement: 測試產生與維運流程

新增或修改 E2E 測試 SHALL 遵循「Planner → Generator → Healer」的 agent 驅動流程，而非直接手寫 `.spec.ts` 檔。此流程的產出 MUST 經人工 review 後才合入 main。

#### Scenario: Planner 產生 Markdown 計畫
- **WHEN** 需要新增一組 E2E 測試
- **THEN** SHALL 先呼叫 Planner agent 產生 `frontend/specs/` 底下的 Markdown 測試計畫（或 agent 產出的等效路徑）

#### Scenario: Generator 把計畫轉成測試碼
- **WHEN** `specs/` 底下的 Markdown 計畫已 review 完成
- **THEN** SHALL 呼叫 Generator agent 把該計畫轉成 `frontend/tests/` 底下的 `.spec.ts` 檔

#### Scenario: Healer 修復失敗測試
- **WHEN** `npm run test:e2e` 出現失敗且原因為選擇器、等待條件、動畫時序等可自動修復的問題
- **THEN** SHALL 優先呼叫 Healer agent 嘗試修復，而非直接人工改碼

#### Scenario: Agent 產出需人工 review
- **WHEN** Planner、Generator 或 Healer 產出新檔案或修改既有檔案
- **THEN** 在 commit 前 MUST 由人工 review，確認沒有踩文字歧義、portal 陷阱或過度生成

### Requirement: 選擇器策略

Generator 產出的測試 SHALL 優先使用 `getByRole` / `getByText` / `getByPlaceholder` 等語意選擇器。`frontend/src/**/*` 的 production code MUST NOT 因測試需求加入 `data-testid` 屬性。

#### Scenario: 不加入 data-testid
- **WHEN** 在 `frontend/src/` 底下搜尋 `data-testid`
- **THEN** 搜尋結果 SHALL 為 0 筆

#### Scenario: 優先用語意選擇器
- **WHEN** 審查 Generator 產出的 `.spec.ts`
- **THEN** 其中的 locator 呼叫 SHOULD 以 `page.getByRole(...)`、`page.getByText(...)`、`page.getByPlaceholder(...)`、`page.getByLabel(...)` 為主，避免 XPath 或 CSS nth-child 類的脆弱選擇器

#### Scenario: 文字歧義處理
- **WHEN** 某個文字（例如「搜尋」、「清除全部條件」）在 DOM 中出現超過一個 element
- **THEN** 測試 SHALL 以 `getByRole('button', { name: '...' })` 或對父容器 scoping 的方式避開 strict mode violation

### Requirement: 瀏覽器矩陣

E2E 測試 SHALL 僅在 Chromium 執行。不啟用 Firefox、WebKit 或 Mobile viewport。

#### Scenario: 唯一的 project
- **WHEN** 讀取 `playwright.config.ts` 的 `projects` 陣列
- **THEN** 陣列長度 SHALL 為 1，且唯一元素的 `name` SHALL 為 `chromium`

#### Scenario: CI 只裝 chromium
- **WHEN** CI workflow `.github/workflows/ci.yml` 的 `e2e` job 執行
- **THEN** 瀏覽器安裝步驟 SHALL 為 `npx playwright install --with-deps chromium`，不安裝其他瀏覽器

### Requirement: 核心使用者流程覆蓋

E2E 測試套件 SHALL 涵蓋以下 5-7 個核心 happy path 情境。每個情境 MUST 至少有一個對應的 Playwright `test()` 與至少一個可見度或文字斷言。

涵蓋的流程：

1. 依病人姓名搜尋，顯示病人摘要
2. 依病歷號搜尋，顯示結果 Tabs
3. 搜尋不存在的病人，顯示空結果文案
4. 切換到條件查詢模式，套用條件模板並執行 AND 邏輯查詢，顯示結果表
5. 從條件查詢結果點「查看」進入病人詳情
6. 病人查詢與條件查詢模式雙向切換

#### Scenario: 病人姓名查詢有結果
- **WHEN** 使用者在首頁輸入 `陳志明` 並按下「搜尋」
- **THEN** 頁面 SHALL 顯示病歷號 `A1234567` 與相關的病人摘要

#### Scenario: 病歷號精確查詢
- **WHEN** 使用者輸入 `B2345678` 並按下「搜尋」
- **THEN** 頁面 SHALL 顯示病人 `林雅婷` 與結果 Tabs（包含「全部」、「基本資料」、「門診」、「檢驗」、「檢體」）

#### Scenario: 空結果文案
- **WHEN** 使用者搜尋一個不存在於 mock data 的字串（例如 `ZZZ`）
- **THEN** 頁面 SHALL 顯示文字「找不到符合條件的病人」

#### Scenario: 條件查詢 AND 邏輯
- **WHEN** 使用者切到「條件查詢」、套用任一條件模板（例如 `Biomarker 異常`）、確認邏輯為 `AND（全部符合）`、按下「執行條件查詢」
- **THEN** 結果表 SHALL 可見，且至少存在一個「查看」按鈕

#### Scenario: 查看按鈕導向病人詳情
- **WHEN** 承上情境，使用者點第一列的「查看」按鈕
- **THEN** 頁面 SHALL 顯示該病人的 `PatientSummary` 與一個可用的返回 / 返回條件查詢結果按鈕

#### Scenario: 模式雙向切換
- **WHEN** 使用者在「病人查詢」與「條件查詢」之間來回切換
- **THEN** 每個模式的核心 UI 元素（病人查詢的搜尋輸入、條件查詢的「執行條件查詢」按鈕）SHALL 正確顯示，不殘留對方模式的狀態

### Requirement: Mock data 穩定性

E2E 測試 SHALL 使用 `frontend/src/data/mockData.ts` 的固定 mock data 作為斷言依據。mock data MUST NOT 包含隨機值或時間相依欄位（例如 `Date.now()`、`Math.random()`），以確保測試可重現。

#### Scenario: 固定病人可被斷言
- **WHEN** 測試引用病歷號 `A1234567`、`B2345678`、`C3456789`
- **THEN** 對應的姓名 `陳志明`、`林雅婷`、`張偉翔` SHALL 可在頁面上被斷言

#### Scenario: mock data 無隨機/時間相依
- **WHEN** 靜態分析 `frontend/src/data/mockData.ts`
- **THEN** 該檔案 SHALL NOT 直接呼叫 `Date.now()`、`new Date()`（不帶參數）、或 `Math.random()`

### Requirement: CI 整合

E2E 測試 SHALL 透過既有 `.github/workflows/ci.yml` 的 `e2e` job 在 PR 回 `main` 時自動執行。本次 change MUST NOT 修改 workflow 檔案，也 MUST NOT 改動 `ci-pipeline` capability 的 spec-level 行為。

#### Scenario: PR 觸發 e2e
- **WHEN** 開發者開啟 / 更新目標為 `main` 的 PR
- **THEN** `e2e` job SHALL 執行 `npx playwright test` 並在所有測試通過後以 exit code 0 結束

#### Scenario: 失敗時上傳 report
- **WHEN** `e2e` job 的 `npx playwright test` 失敗
- **THEN** `actions/upload-artifact@v4` SHALL 上傳 `frontend/playwright-report/`，使 reviewer 可下載 debug

#### Scenario: workflow 檔案未被修改
- **WHEN** 比對本次 change 的 git diff
- **THEN** `.github/workflows/ci.yml` SHALL NOT 在 diff 中出現
