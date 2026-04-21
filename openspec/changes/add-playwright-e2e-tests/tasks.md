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

- [ ] 2.1 編輯 `frontend/playwright.config.ts`，加入 `fullyParallel: true`、`forbidOnly: !!process.env.CI`、`retries: process.env.CI ? 2 : 0`、`workers: process.env.CI ? 1 : undefined`、`timeout: 30_000`、`expect.timeout: 5_000`、`outputDir: './test-results'`
- [ ] 2.2 在 `use` 物件補上 `trace: 'on-first-retry'`、`screenshot: 'only-on-failure'`、`video: 'retain-on-failure'`、`actionTimeout: 10_000`、`navigationTimeout: 15_000`（`baseURL` 保留既值）
- [ ] 2.3 新增 `projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }]`，並 import `devices` from `@playwright/test`
- [ ] 2.4 在 `webServer` 物件補上 `timeout: 120_000`（`command`、`url`、`reuseExistingServer` 保留既值）
- [ ] 2.5 在 `frontend/` 執行 `npm run typecheck` 確認 `playwright.config.ts` 無型別錯誤；執行 `npm run lint` 與 `npm run format:check` 確認無違規
- [ ] 2.6 **Commit 2**：`git add frontend/playwright.config.ts`，訊息：`chore(e2e): upgrade playwright.config.ts with projects, trace, retries`

## 3. 新增 npm scripts

- [ ] 3.1 編輯 `frontend/package.json`，在 `scripts` 中新增 `"test:e2e": "playwright test"`、`"test:e2e:ui": "playwright test --ui"`、`"test:e2e:debug": "playwright test --debug"`、`"test:e2e:headed": "playwright test --headed"`、`"test:e2e:report": "playwright show-report"`（放在既有 `test:watch` 之後）
- [ ] 3.2 確認既有 `test`（`vitest run`）與 `test:watch`（`vitest`）未被動到
- [ ] 3.3 於 `frontend/` 執行 `npm run test:e2e` 驗證 `seed.spec.ts` 通過（Chromium 應自動安裝；若未安裝，先跑 `npx playwright install chromium`）
- [ ] 3.4 **Commit 3**：`git add frontend/package.json`，訊息：`chore(e2e): add test:e2e scripts to package.json`

## 4. 呼叫 Planner 產出測試計畫

- [ ] 4.1 依 Step 1.2 確認的 agent 呼叫方式（slash command、subagent_type 或 skill）叫起 Planner，傳入以下 prompt：
  > 為 `http://localhost:8080` 的基因醫學整合查詢中心寫 5-7 個核心 happy path 的 E2E 測試計畫，聚焦以下流程：(1) 依姓名搜尋病人並看到病人摘要 (2) 依病歷號精確查詢看到結果 Tabs (3) 搜尋不存在的字串看到空結果文案 (4) 切到條件查詢、套用條件模板、執行 AND 查詢看到結果表 (5) 從條件結果點「查看」進入病人詳情 (6) 病人查詢與條件查詢模式雙向切換。Mock data 固定病人：A1234567 陳志明、B2345678 林雅婷、C3456789 張偉翔。條件模板名稱可參考 `src/types/medical.ts` 的 `CONDITION_TEMPLATES`（如 `Biomarker 異常`、`MPS 相關異常`）。寫進 `specs/` 一份 Markdown 計畫。不要涵蓋 edge case（錯誤輸入、鍵盤導航、RWD）。
- [ ] 4.2 Planner 完成後 review `frontend/specs/` 底下產出的 `.md` 檔，確認測試數量在 5-7 之間、每個 scenario 對應到上述 6 個流程之一、沒有涵蓋被排除的 edge case
- [ ] 4.3 若 Planner 產出超量或偏離 scope，刪掉多餘計畫或補充 prompt 再跑一次
- [ ] 4.4 **Commit 4**：`git add frontend/specs/`，訊息：`docs(e2e): add Planner-generated test plans for core happy paths`

## 5. 呼叫 Generator 產出測試碼

- [ ] 5.1 叫 Generator，指示其讀 `frontend/specs/` 底下的計畫，產生 `frontend/tests/*.spec.ts`
- [ ] 5.2 review Generator 產出：
  - locator 應為 `getByRole` / `getByText` / `getByPlaceholder` / `getByLabel`，禁用 XPath 與 CSS nth-child
  - 「搜尋」按鈕 locator 應以 `getByRole('button', { name: '搜尋' })` 表達以避開 placeholder 與其他地方的「搜尋」字樣
  - 「清除全部條件」locator 僅出現在 ConditionBuilder，無歧義但需確認只用一次
  - 「找不到符合條件的病人」出現在多 scope，確認測試文件分檔後不會跨 scope 斷言
  - Radix Select 的 portal option 以 `page.getByRole('option', { name: ... })` 取得，不用 parent scoping
- [ ] 5.3 **Commit 5**：`git add frontend/tests/`（排除 `seed.spec.ts` 除非它也被 Generator 動到），訊息：`test(e2e): add Generator-produced spec files for happy paths`

## 6. 呼叫 Healer 修綠測試

- [ ] 6.1 於 `frontend/` 執行 `npm run test:e2e`，記錄失敗清單
- [ ] 6.2 若有失敗，叫 Healer 修復；Healer 會讀 trace + screenshot + video 推論選擇器或等待條件的修正
- [ ] 6.3 Healer 修完後再跑 `npm run test:e2e` 驗證
- [ ] 6.4 若 Healer 對 Radix Select / Accordion 的 portal 渲染問題反覆修不好：
  - 在 `tests/helpers.ts`（若 Generator 已產生）加入 `disableAnimations(page)` 透過 `page.addStyleTag` 注入 `*,*::before,*::after{animation:none!important;transition:none!important}`
  - 或改用 `page.getByRole('option', ...)` 明確尋找 portal 內的選項
- [ ] 6.5 **Commit 6**（僅在 Healer 或人工有實際改動時）：`git add frontend/tests/ frontend/playwright.config.ts` 視實際變更範圍，訊息：`test(e2e): apply Healer fixes for selector and timing stability`；若 Step 6.1 已全綠、完全沒改東西，跳過此 commit

## 7. 驗證

- [ ] 7.1 於 `frontend/` 執行 `npm run lint` 確認新測試檔通過 ESLint（airbnb + typescript）
- [ ] 7.2 於 `frontend/` 執行 `npm run format:check` 確認新測試檔通過 Prettier
- [ ] 7.3 於 `frontend/` 執行 `npm run typecheck` 確認新測試檔 TypeScript 無錯
- [ ] 7.4 於 `frontend/` 執行 `npm run test:e2e` 本機全綠
- [ ] 7.5 於 `frontend/` 以 `CI=1 npm run test:e2e` 模擬 CI（1 worker、retries=2），確認仍全綠
- [ ] 7.6 本機 commit 歷史檢查：`git log --oneline main..HEAD` 顯示 5-6 個 commit，訊息依序為 Section 1-6 的 commit 訊息，沒有 squash、沒有 WIP 訊息

## 8. 推送與 PR

- [ ] 8.1 確認 `frontend/src/**/*` 未被本次 change 修改：`git diff main -- frontend/src` 輸出為空
- [ ] 8.2 確認 `.github/workflows/ci.yml` 未被本次 change 修改：`git diff main -- .github/workflows/ci.yml` 輸出為空
- [ ] 8.3 推送 branch：`git push -u origin chore/add-playwright-e2e-tests`
- [ ] 8.4 開啟 PR 目標為 `main`（`gh pr create ...`），PR description 說明新增的 E2E 測試、Playwright Test Agents 工作流程、未來新增測試的 SOP（Planner → Generator → Healer）、以及 commit 拆分邏輯
- [ ] 8.5 等 GitHub Actions 的六個 job 全綠，特別確認 `e2e` job 通過
- [ ] 8.6（選用）在 PR run 頁面驗證失敗路徑：另開一個 throwaway commit 刻意把斷言改錯，push 後確認 `playwright-report` artifact 可下載、trace 可播放；驗完後 `git reset --hard HEAD~1 && git push --force-with-lease`（或 revert commit）
- [ ] 8.7 Review + merge PR 後，把 change 歸檔到 `openspec/changes/archive/` 並跑 `openspec validate`（由 `/opsx:archive` 處理）
