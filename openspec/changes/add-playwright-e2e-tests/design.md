## Context

前端 `frontend/` 的 E2E 測試基礎設施現況：

- **Playwright 1.57** 已安裝在 `frontend/package.json`，符合 Test Agents 最低版本 1.56
- **`frontend/playwright.config.ts`** 極簡：只有 `testDir`、`reporter`、`use.baseURL`、`webServer`
- **`frontend/tests/seed.spec.ts`** 存在（goto `/` + assert URL）— 這正是 Playwright Test Agents 預期的 seed 結構
- **`frontend/specs/README.md`** 存在（內容「This is a directory for test plans.」）— 也對齊 Test Agents 預期
- **`frontend/src/**`** 完全**沒有** `data-testid`
- **Mock data**：`src/data/mockData.ts` 為 5 位固定假病人（A1234567 陳志明、B2345678 林雅婷、C3456789 張偉翔），無隨機、無 `Date.now()`，斷言穩定
- **路由**：單頁 `App.tsx`（`/` 為 `Index` 頁面、`*` 為 `NotFound`）
- **UI 技術**：shadcn/ui + Radix primitives + Tailwind，所有互動文字皆為繁體中文（「搜尋」「條件查詢」「病人查詢」「執行條件查詢」「找不到符合條件的病人」等）
- **後端**：PLAN.md 指出後端（Python / FastAPI microservices）尚未建立，前端純 client-side 跑 mock data
- **CI**：`.github/workflows/ci.yml` 已有 `e2e` job（`npx playwright install --with-deps chromium` + `npx playwright test` + 上傳 `playwright-report/` artifact），由 archived 的 `ci-pipeline` capability 定義
- **現況痛點**：`tests/` 只有 `seed.spec.ts`，沒有真正的回歸覆蓋

## Goals / Non-Goals

**Goals:**
- 為 5-7 個核心使用者流程建立 E2E 回歸保護
- 讓測試產生與維運流程可重複（下次加測試不靠人工憑感覺抓選擇器）
- 維持 **production code 零侵入**（不加 `data-testid`、不動 `src/**`）
- 與現有 CI workflow 對齊，不修 `.github/workflows/ci.yml`
- 後端接上後，可在不換框架的前提下延伸測試（以 `page.route` stub API）

**Non-Goals:**
- 不建立自訂 page object / fixture 抽象層（6 個測試規模不值得）
- 不涵蓋邊界情境（錯誤輸入、鍵盤導航、RWD、視覺回歸、a11y audit）
- 不跑多瀏覽器（只 Chromium）
- 不接真實 API（後端尚未建、用 mock data 即可）
- 不處理登入 / 權限（app 目前無登入）
- 不修 CI workflow（現有 `e2e` job 已足夠）
- 不改 `ci-pipeline` spec（spec-level 行為不變）

## Decisions

### Decision 1：採用 Playwright 官方 Test Agents（Planner / Generator / Healer）而非手寫 specs + helpers

**理由：**
- Playwright 1.56+ 原生支援、由 Playwright 團隊維護 agent 定義，會跟 API 演進
- Planner 透過 Playwright MCP 實際操作瀏覽器探索 app，比人工枚舉 UI 錨點更完整也更準確
- Healer 在測試失敗時自動修選擇器與等待條件，直接解決「純文字選擇器耦合文案」造成的維護成本
- 官方文件的分層（`specs/` Markdown、`tests/` 測試碼、`seed.spec.ts` 起點）已契合此 repo 既有 skeleton

**取捨：**
- 缺點：agent 產出品質依賴 Playwright 版本、需偶爾重跑 `init-agents` 更新定義
- 缺點：Planner 可能過度生成（20+ 測試覆蓋 edge case），需要 prompt 明確寫「5-7 個 happy path」約束
- 替代方案：手寫 spec + 自建 helpers.ts。捨棄原因是維運成本高、無 Healer 的自動修復、且此 repo 有 skeleton 已等著接 Test Agents

### Decision 2：選擇器採純 `getByRole` / `getByText` / `getByPlaceholder`，不加 `data-testid`

**理由：**
- 使用者明確要求不改 production code
- Generator agent 預設就是這個策略，無須特別配置
- 此 app 為醫療系統內部工具，文案穩定度高（非行銷頁面）
- 有 Healer 補上維運韌性

**取捨：**
- 風險：未來若大改文案，多支測試同步壞掉 → 透過 Healer 自動修 + `helpers.ts`（若後續 Generator 產生）作為收斂點
- 替代方案：在關鍵節點加 `data-testid`。保留為第二階段選項，只在 Healer 反覆修不好的錨點才加

### Decision 3：只跑 Chromium，不啟用 Firefox / WebKit

**理由：**
- 使用者明確要求
- 醫療系統內部使用者，IT 通常強制 Chrome / Edge，無跨瀏覽器需求
- CI 時間與 agent 生成時間都變三分之一
- 對齊現有 `.github/workflows/ci.yml:106` 的 `--with-deps chromium` 設定

**取捨：**
- 風險：Radix UI 在不同瀏覽器的事件時序不同，只跑 Chromium 會漏偵 → 在此 app 使用情境下可接受
- 替代方案：三瀏覽器矩陣。捨棄原因是 CI 成本三倍、收益極低

### Decision 4：在 `playwright.config.ts` 明定 `projects: [{ name: 'chromium', ... }]`（即便只有一個）

**理由：**
- 預留擴充：日後若需加 Firefox 只需在陣列 push 一筆
- `devices['Desktop Chrome']` 提供穩定的 viewport、userAgent 預設
- Playwright UI mode 在有 projects 時 UX 較好

**取捨：**
- 取代方案：不設 projects，用預設 Chromium。捨棄原因是擴充時需重構

### Decision 5：`use.trace: 'on-first-retry'`、`screenshot: 'only-on-failure'`、`video: 'retain-on-failure'`

**理由：**
- 綠的 run 零額外開銷
- 抖動時全 trace 給 Healer 修；穩定失敗時 trace + screenshot + video 給人工 debug
- Healer agent 依賴 trace 才能推論選擇器該怎麼改

**取捨：**
- 替代方案：`trace: 'on'`（每 run 都錄）。捨棄原因是存儲與傳輸成本不值

### Decision 6：`retries: CI ? 2 : 0`、`workers: CI ? 1 : undefined`

**理由：**
- CI retries=2 吸收 Vite cold-boot 抖動與 Radix 動畫時序
- CI workers=1 避免 GitHub runner 資源爭用
- 本地 retries=0 讓開發者立刻看到失敗；workers 預設並行提速

**取捨：**
- 替代方案：CI retries=0。捨棄原因是初期 agent 產出尚未穩定、給兩次重試避免誤報
- 替代方案：CI workers>1。捨棄原因是 webServer 同時只能有一個 Vite 實例

### Decision 7：保留 `frontend/tests/seed.spec.ts`，不刪

**理由：**
- Test Agents 官方要求 seed test 作為探索起點
- 現有的「goto `/` + assert URL」對此 app（無登入、無全域狀態）已足夠
- 刪掉會讓 Planner / Healer 初始化失敗

**取捨：**
- 替代方案：刪除。捨棄原因是違反官方要求

### Decision 8：新增 5 個 npm scripts（`test:e2e`、`test:e2e:ui`、`test:e2e:debug`、`test:e2e:headed`、`test:e2e:report`）

**理由：**
- 對齊既有 `test` / `test:watch`（vitest）的命名風格
- CI 用 `test:e2e`、本機除錯用 `test:e2e:ui` / `test:e2e:debug`、fail 後看 report 用 `test:e2e:report`
- 不強綁 Playwright CLI 路徑，`package.json` 是單一事實來源

**取捨：**
- 替代方案：只加 `test:e2e`。捨棄原因是本機除錯流程常用的三個 mode 都值得快捷

### Decision 9：不修 `.github/workflows/ci.yml` 與 `ci-pipeline` spec

**理由：**
- 現有 `e2e` job 已定義 `npx playwright install --with-deps chromium` + `npx playwright test` + 上傳 report
- 新的 `playwright.config.ts` 對 CI 透明（`npx playwright test` 自動讀 config）
- `ci-pipeline` 的 spec-level 行為（job 名稱、觸發條件、步驟順序、artifact 路徑）皆不變

**取捨：**
- 若未來需要分 `e2e-chromium` / `e2e-firefox` matrix job，再視需要開新 change 修 `ci-pipeline`

## Risks / Trade-offs

- **Risk**：`npx playwright init-agents --loop=claude` 實際安裝路徑未完全文件化 → Mitigation：Step 1 跑完立刻 `ls .claude/` 與 `git status` 確認；若 MCP server 需額外安裝，在叫 Planner 前補齊
- **Risk**：Playwright MCP server 第一次被 Claude Code 呼叫時可能跳權限詢問（瀏覽器自動化屬敏感操作）→ Mitigation：使用者核准即可；若反覆中斷，在 `.claude/settings.json` 加入 allowlist
- **Risk**：Planner 過度生成 → Mitigation：prompt 明確寫「5-7 個」「happy path」「不涵蓋 edge case」
- **Risk**：Generator 產生的選擇器踩文字歧義（「搜尋」、「清除全部條件」、「找不到符合條件的病人」在多處出現） → Mitigation：審 code 時特別檢查、必要時請 Generator 改用 `getByRole('button', { name: '搜尋' })` 或加 scope
- **Risk**：Healer 無法修 Radix Select / Accordion 的 portal 渲染問題 → Mitigation：退回人工加 `disableAnimations(page)` 或改用 `getByRole('option', ...)` 搜尋 portal
- **Risk**：升級 `@playwright/test` 版本時 agent 定義可能過期 → Mitigation：package.json 升版時同步重跑 `init-agents --loop=claude`
- **Trade-off**：Auto-generated spec / test 碼需人工 review 一輪才能合入，不能 100% 無人化

## Migration Plan

### Branch 策略

所有變更在 feature branch `chore/add-playwright-e2e-tests` 進行（從乾淨的 `main` 拉出）。`main` 受 PR-only 更新（`ci-pipeline` capability 已定義）；合入前必須所有 CI job 綠燈。

### Commit 拆分策略

以「關注點單一」為原則，拆成 5-6 個 commit，對應 tasks.md 的 Section 1–6。每個 commit 都應可獨立 review、可獨立 revert：

| # | Scope | 訊息 | 產出檔案 |
|---|---|---|---|
| 1 | Agents 骨架 | `chore(e2e): install Playwright Test Agents via init-agents --loop=claude` | `frontend/.claude/**`（init-agents 產出）、`frontend/.mcp.json`（若有）、`frontend/package.json` + `package-lock.json`（若有新增 MCP 套件） |
| 2 | Config | `chore(e2e): upgrade playwright.config.ts with projects, trace, retries` | `frontend/playwright.config.ts` |
| 3 | Scripts | `chore(e2e): add test:e2e scripts to package.json` | `frontend/package.json` |
| 4 | Test 計畫 | `docs(e2e): add Planner-generated test plans for core happy paths` | `frontend/specs/*.md` |
| 5 | Test 程式 | `test(e2e): add Generator-produced spec files for happy paths` | `frontend/tests/*.spec.ts`（不含 `seed.spec.ts`） |
| 6 | Healer 修正 | `test(e2e): apply Healer fixes for selector and timing stability` | 視實際範圍而定；若 commit 5 後跑測試即全綠，跳過此 commit |

訊息格式對齊 repo 慣例（conventional commits：`<type>(scope): description`，近期 commit 皆採此形式）。

### 實作步驟（流程層面）

1. Section 0：開 branch
2. Section 1：跑 `init-agents` → Commit 1
3. Section 2：升級 config → Commit 2
4. Section 3：加 scripts → Commit 3（此步後 `seed.spec.ts` 應可透過 `npm run test:e2e` 通過，作為後續 agent 的 baseline）
5. Section 4：Planner → Commit 4
6. Section 5：Generator → Commit 5
7. Section 6：Healer → Commit 6（可選）
8. Section 7：本機驗證 + 模擬 CI + commit 歷史檢查
9. Section 8：push、開 PR、等 CI 綠、archive

**Rollback：**
- 若 Test Agents 產出品質無法接受：
  - 整支 PR 退回：`main` 未受影響，丟棄 branch 即可
  - 只退 agent 相關 commit：`git revert` commit 4、5、6（保留 config 與 scripts 升級）；改以人工撰寫 specs
- 若只有某個測試抖動：以 `.skip` 暫時關掉並開新 issue，不必整個 revert

## Open Questions

1. `npx playwright init-agents --loop=claude` 在 `frontend/` 底下會建立到 `.claude/agents/`、`.claude/skills/`、還是 `.claude/commands/`？需在 Step 1 跑完後確認，並在 tasks.md 中填入實際路徑
2. Playwright MCP server 是否需要 `npm install @playwright/mcp`，或由 `init-agents` 設定用 `npx` 動態呼叫？需檢查 `init-agents` 是否動了 `.mcp.json` 或 `.claude/settings.json`
3. Planner 會把 specs 寫在 `frontend/specs/` 還是 `frontend/tests/specs/`？需依 agent 產出實際位置決定 `frontend/specs/README.md` 是否保留 / 更新
4. 未來後端接上後，stub 策略（`page.route` vs fixture）：留在後續 change 處理，不在此 change 範圍
