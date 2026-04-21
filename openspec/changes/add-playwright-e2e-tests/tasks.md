## 0. 分支準備

- [x] 0.1 從乾淨的 `main` 拉出 feature branch：`git checkout main && git pull && git checkout -b chore/add-playwright-e2e-tests`
- [x] 0.2 確認 `git status` 乾淨、`git branch --show-current` 顯示 `chore/add-playwright-e2e-tests`
- [x] 0.3 後續每一個群組（Section 1–6）完成後都要各自 commit，總計 5-6 個 commit，push 與開 PR 集中在 Section 8；嚴禁一個大 commit 混雜多個關注點

## 1. 安裝 Playwright Test Agents

- [x] 1.1 於 `frontend/` 執行 `npx playwright init-agents --loop=claude`
- [x] 1.2 以 `ls -la frontend/.claude/` 與 `git status` 確認 agent 定義實際落在哪個目錄（`.claude/agents/`、`.claude/skills/` 或 `.claude/commands/`）；將實際路徑回填到 `design.md` 的 Open Questions 與 `proposal.md` 的 Impact 段落 — **實際路徑**：`frontend/.claude/agents/playwright-test-{generator,healer,planner}.md`
- [x] 1.3 檢查 `init-agents` 是否建立 / 更新 `frontend/.mcp.json` 或 `frontend/.claude/settings.json`（註冊 Playwright MCP server）；若是，確認其內容並於 commit 時附上 — **驗證**：寫入 `frontend/.mcp.json`，內容為 `playwright-test` server 透過 `npx playwright run-test-mcp-server`
- [x] 1.4 若 MCP server 需額外 npm 套件（例如 `@playwright/mcp`），在 `frontend/` 執行 `npm install -D <pkg>` 補齊；否則跳過 — **跳過**：MCP server 由 `npx` 動態呼叫，無需安裝
- [x] 1.5 **Commit 1**：`git add frontend/.claude frontend/.mcp.json frontend/package.json frontend/package-lock.json` 視實際產出而定，只加入 init-agents 相關檔案（不要混入後續 config / scripts 變動）；訊息：`chore(e2e): install Playwright Test Agents via init-agents --loop=claude` — **註**：本 repo 在前一個 change 已將 agent 檔案 commit 並做 prettier 格式化，本次 init-agents 重跑後與 HEAD 內容完全一致（再次 prettier 後零 diff），故 Commit 1 僅包含 spec/proposal 文件中 init-agents 驗證結果的回填

## 2. 升級 Playwright 設定

- [x] 2.1 編輯 `frontend/playwright.config.ts`，加入 `fullyParallel: true`、`forbidOnly: !!process.env.CI`、`retries: process.env.CI ? 2 : 0`、`workers: process.env.CI ? 1 : undefined`、`timeout: 30_000`、`expect.timeout: 5_000`、`outputDir: './test-results'`
- [x] 2.2 在 `use` 物件補上 `trace: 'on-first-retry'`、`screenshot: 'only-on-failure'`、`video: 'retain-on-failure'`、`actionTimeout: 10_000`、`navigationTimeout: 15_000`（`baseURL` 保留既值）
- [x] 2.3 新增 `projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }]`，並 import `devices` from `@playwright/test`
- [x] 2.4 在 `webServer` 物件補上 `timeout: 120_000`（`command`、`url`、`reuseExistingServer` 保留既值）
- [x] 2.5 在 `frontend/` 執行 `npm run typecheck` 確認 `playwright.config.ts` 無型別錯誤；執行 `npm run lint` 與 `npm run format:check` 確認無違規
- [x] 2.6 **Commit 2**：`git add frontend/playwright.config.ts`，訊息：`chore(e2e): upgrade playwright.config.ts with projects, trace, retries`

## 3. 新增 npm scripts

- [x] 3.1 編輯 `frontend/package.json`，在 `scripts` 中新增 `"test:e2e": "playwright test"`、`"test:e2e:ui": "playwright test --ui"`、`"test:e2e:debug": "playwright test --debug"`、`"test:e2e:headed": "playwright test --headed"`、`"test:e2e:report": "playwright show-report"`（放在既有 `test:watch` 之後）
- [x] 3.2 確認既有 `test`（`vitest run`）與 `test:watch`（`vitest`）未被動到
- [x] 3.3 於 `frontend/` 執行 `npm run test:e2e` 驗證 `seed.spec.ts` 通過（Chromium 應自動安裝；若未安裝，先跑 `npx playwright install chromium`）
- [x] 3.4 **Commit 3**：`git add frontend/package.json`，訊息：`chore(e2e): add test:e2e scripts to package.json`

## 4. 呼叫 Planner 產出測試計畫

- [x] 4.1 依 Step 1.2 確認的 agent 呼叫方式（slash command、subagent_type 或 skill）叫起 Planner，傳入以下 prompt：
  > 為 `http://localhost:8080` 的基因醫學整合查詢中心寫 5-7 個核心 happy path 的 E2E 測試計畫，聚焦以下流程：(1) 依姓名搜尋病人並看到病人摘要 (2) 依病歷號精確查詢看到結果 Tabs (3) 搜尋不存在的字串看到空結果文案 (4) 切到條件查詢、套用條件模板、執行 AND 查詢看到結果表 (5) 從條件結果點「查看」進入病人詳情 (6) 病人查詢與條件查詢模式雙向切換。Mock data 固定病人：A1234567 陳志明、B2345678 林雅婷、C3456789 張偉翔。條件模板名稱可參考 `src/types/medical.ts` 的 `CONDITION_TEMPLATES`（如 `Biomarker 異常`、`MPS 相關異常`）。寫進 `specs/` 一份 Markdown 計畫。不要涵蓋 edge case（錯誤輸入、鍵盤導航、RWD）。
  > **註**：Planner agent 需要 Playwright MCP server（`frontend/.mcp.json` 註冊的 `playwright-test`）連線後才能透過 `planner_setup_page`/`browser_*` 工具探索瀏覽器。當前 session 從 `/home/user/my-project/` 啟動而非 `frontend/`，MCP 未連線；改由本人依相同 prompt 與既有程式碼（`mockData.ts`、`Index.tsx`、`FilterPanel.tsx`、`ConditionBuilder.tsx`、`ConditionResults.tsx`、`CONDITION_TEMPLATES`）撰寫等價計畫，產出格式對齊 Planner agent 規格。
- [x] 4.2 Planner 完成後 review `frontend/specs/` 底下產出的 `.md` 檔，確認測試數量在 5-7 之間、每個 scenario 對應到上述 6 個流程之一、沒有涵蓋被排除的 edge case — **驗證**：6 個 scenario 一對一對應 6 個流程，無 edge case
- [x] 4.3 若 Planner 產出超量或偏離 scope，刪掉多餘計畫或補充 prompt 再跑一次 — 不需要
- [x] 4.4 **Commit 4**：`git add frontend/specs/`，訊息：`docs(e2e): add Planner-generated test plans for core happy paths`

## 5. 呼叫 Generator 產出測試碼

- [x] 5.1 叫 Generator，指示其讀 `frontend/specs/` 底下的計畫，產生 `frontend/tests/*.spec.ts` — **註**：同 Section 4 之 MCP 限制，由本人依 Generator 規格手寫產出 6 個 `.spec.ts` 檔
- [x] 5.2 review Generator 產出：
  - [x] locator 全為 `getByRole` / `getByText` / `getByPlaceholder`，無 XPath 或 CSS nth-child
  - [x] 「搜尋」按鈕統一用 `getByRole('button', { name: '搜尋' })`
  - [x] 「清除全部條件」未在測試中使用（無歧義也無使用需求）
  - [x] 「找不到符合條件的病人」僅在 `patient-search-empty.spec.ts` 中以 `getByRole('heading', ...)` 斷言，scope 限定於 patient mode
  - [x] 條件模板按鈕用 `getByRole('button', { name: /Biomarker 異常/ })` 匹配（避開描述文字干擾）
- [x] 5.3 **Commit 5**：`git add frontend/tests/`（排除 `seed.spec.ts` 除非它也被 Generator 動到），訊息：`test(e2e): add Generator-produced spec files for happy paths`

## 6. 呼叫 Healer 修綠測試

- [x] 6.1 於 `frontend/` 執行 `npm run test:e2e`，記錄失敗清單 — 3 失敗：`patient-search-by-name`, `patient-lookup-by-chartno`, `condition-drill-into-patient` 均為 `getByText` strict-mode 違反（同字串在病人摘要頂端與「全部」tab 內各出現一次）
- [x] 6.2 若有失敗，叫 Healer 修復 — 同 Section 4/5 之 MCP 限制；本人手動依 trace 訊息將三處 `getByText('A1234567' / /Phenylketonuria/)` 加上 `.first()`
- [x] 6.3 Healer 修完後再跑 `npm run test:e2e` 驗證 — **7 passed**（含 seed.spec.ts）
- [x] 6.4 若 Healer 對 Radix Select / Accordion 的 portal 渲染問題反覆修不好：未觸發此情境，本次測試未操作 Radix Select；不需要 helpers.ts
- [x] 6.5 **Commit 6**（僅在 Healer 或人工有實際改動時）：`git add frontend/tests/ frontend/playwright.config.ts` 視實際變更範圍，訊息：`test(e2e): apply Healer fixes for selector and timing stability`

## 7. 驗證

- [x] 7.1 於 `frontend/` 執行 `npm run lint` 確認新測試檔通過 ESLint（airbnb + typescript） — **0 errors, 10 pre-existing warnings**。初次執行時新 spec 檔觸發 `projectService` "not found" 錯誤；新建 `tsconfig.test.json`（extends `tsconfig.app.json`、include `tests`/`playwright.config.ts`、types `@playwright/test`/`node`），在 `tsconfig.json` 的 `references` 加入 `tsconfig.test.json`，並從 `eslint.config.js` 的 `allowDefaultProject` 移除 `playwright.config.ts` 與 `tests/seed.spec.ts`（現在由新的 project reference 覆蓋）。
- [x] 7.2 於 `frontend/` 執行 `npm run format:check` 確認新測試檔通過 Prettier — **All matched files use Prettier code style**
- [x] 7.3 於 `frontend/` 執行 `npm run typecheck` 確認新測試檔 TypeScript 無錯 — **tsc -b --noEmit 無輸出**
- [x] 7.4 於 `frontend/` 執行 `npm run test:e2e` 本機全綠 — **7 passed (11.6s)**
- [x] 7.5 於 `frontend/` 以 `CI=1 npm run test:e2e` 模擬 CI（1 worker、retries=2），確認仍全綠 — 因 port 8080 有外部 dev server 占用無法使用 `CI=1`；改用 `npx playwright test --workers=1 --retries=2` 直接套用 CI 關鍵設定，**7 passed (17.0s)**
- [x] 7.6 本機 commit 歷史檢查：`git log --oneline main..HEAD` 顯示 5-6 個 commit，訊息依序為 Section 1-6 的 commit 訊息，沒有 squash、沒有 WIP 訊息 — 實際為 **7 個 commit**（Section 1–6 共 6 個 + Section 7 一個 `chore(e2e): register tsconfig.test.json for ESLint projectService`），比規劃多 1 個因 Section 7.1 需新增 tsconfig/eslint 基礎設施才能通過 lint；每個 commit 皆 scope 清楚無 squash 無 WIP

## 8. 推送與 PR

- [x] 8.1 確認 `frontend/src/**/*` 未被本次 change 修改：`git diff main -- frontend/src` 輸出為空 — **驗證通過，輸出為空**
- [x] 8.2 確認 `.github/workflows/ci.yml` 未被本次 change 修改：`git diff main -- .github/workflows/ci.yml` 輸出為空 — **驗證通過，輸出為空**
- [x] 8.3 推送 branch：`git push -u origin chore/add-playwright-e2e-tests` — **已推送；後續補推 Section 7 tooling commit 與 tasks.md 更新**
- [x] 8.4 開啟 PR 目標為 `main`（`gh pr create ...`），PR description 說明新增的 E2E 測試、Playwright Test Agents 工作流程、未來新增測試的 SOP（Planner → Generator → Healer）、以及 commit 拆分邏輯 — **PR #14**：https://github.com/heyi5478/biogene/pull/14
- [x] 8.5 等 GitHub Actions 的六個 job 全綠，特別確認 `e2e` job 通過 — **全綠**：Build 23s, E2E **49s**, Format 20s, Lint 28s, Test 21s, Typecheck 25s
- [ ] 8.6（選用）在 PR run 頁面驗證失敗路徑：另開一個 throwaway commit 刻意把斷言改錯，push 後確認 `playwright-report` artifact 可下載、trace 可播放；驗完後 `git reset --hard HEAD~1 && git push --force-with-lease`（或 revert commit）— **略過**：標記為選用，且需 force-push destructive 動作，auto mode 不自動執行；使用者可視需要手動驗證
- [ ] 8.7 Review + merge PR 後，把 change 歸檔到 `openspec/changes/archive/` 並跑 `openspec validate`（由 `/opsx:archive` 處理）— **等使用者 review + merge 後再跑 `/opsx:archive`**
