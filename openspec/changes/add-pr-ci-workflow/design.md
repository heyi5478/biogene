## Context

此 repo 為單一前端 Vite 專案(`frontend/`),使用 React 19、TypeScript 5.8、Vitest、Playwright 1.57。目前沒有任何 GitHub Actions workflow。本機 Node 版本為 `v22.22.2`。套件管理為 npm,`frontend/package-lock.json` 存在。

`frontend/tsconfig.json` 採用 project references(composite)架構,refs 到 `tsconfig.app.json` 與 `tsconfig.node.json`,因此 typecheck 必須走 `tsc -b` 而非單檔 `tsc --noEmit`。

`frontend/playwright.config.ts` 已定義 `webServer: npm run dev`(port 8080),且 `reuseExistingServer: !process.env.CI` — GitHub Actions 預設會設定 `CI=true`,因此 Playwright 會自動啟動 server 並在測試結束時關閉。

## Goals / Non-Goals

**Goals:**
- PR 目標為 `main` 時自動觸發完整 CI
- 六項檢查結果分別顯示在 PR status(而非合併成單一 job),方便 reviewer 快速看出哪項失敗
- CI 腳本呼叫已存在於 `package.json` 的 script,避免在 workflow 內直接硬寫 `eslint .`、`vitest run` 等,保持單一事實來源
- E2E 測試失敗時可下載 Playwright HTML report 做 debug

**Non-Goals:**
- 不處理 push 到 `main` 後的 CI(此 change 只關心 PR 閘門)
- 不處理 branch protection / required status checks 設定(使用者明確表示在 GitHub UI 自行處理)
- 不導入 coverage 上傳、SonarQube、bundle size 檢查等延伸功能
- 不改動任何應用程式碼、測試碼、lint 規則
- 不加入 matrix(多 Node 版本、多 OS)
- 不新增 pre-commit hook(husky/lint-staged 不在此 change 範圍)

## Decisions

### Decision 1:單一 workflow、六個併行 job(而非單一 job 依序跑)

把六項檢查拆成獨立 job 而非在同一 job 內序列執行。

**理由:**
- 併行執行總時間約等於最慢 job(預期為 `build` 或 `e2e`),比序列快很多
- PR status 頁面會分別顯示六個 check,reviewer 一眼看出失敗項
- 單一 job 失敗不影響其他 job 繼續跑,開發者一次看到所有失敗項

**取捨:**
- 缺點是每個 job 都要各自 `checkout` + `setup-node` + `npm ci`。透過 `actions/setup-node@v4` 的 `cache: 'npm'` 緩解 `npm ci` 成本
- 替代方案:單一 job + 多步驟。捨棄原因是失敗時只能看到第一個失敗點,且無法平行

### Decision 2:新增 `typecheck` script 到 `package.json`,而非在 workflow 內硬寫 `npx tsc`

**理由:**
- workflow 只呼叫 `npm run <script>` 維持單一事實來源
- 開發者本機可以 `npm run typecheck` 複現 CI 結果
- 日後若改 typecheck 命令(加 flag、切工具)只需改一處

**命令選擇:`tsc -b --noEmit`**
- `tsconfig.json` 為 composite build 架構,必須用 `-b`(build mode)
- `tsconfig.app.json` 已有 `noEmit: true`,顯式加 `--noEmit` 讓意圖更清楚,並與之後若 references 新增不含 noEmit 的子 config 時一致

### Decision 3:Node 22、固定主版號

workflow 使用 `node-version: '22'`(不鎖小版號)。

**理由:**
- 本機開發用 Node 22,CI 與本機對齊,避免 Node 版本差異造成 CI 過 / 本機掛(或反之)
- 不鎖小版號讓 GitHub 自動取最新 22 patch,收安全更新
- 不做 matrix(20 + 22):此專案只部署一個環境,跑兩版浪費 CI 時間

### Decision 4:Playwright 只安裝 Chromium、`--with-deps`

E2E job 執行 `npx playwright install --with-deps chromium`。

**理由:**
- 目前 `playwright.config.ts` 沒定義 `projects`,預設用 Chromium,裝其他瀏覽器無意義
- `--with-deps` 連同系統相依(Debian 套件)一起裝,在 Ubuntu runner 是必要的
- 若日後擴充多瀏覽器測試,再來修這一步

### Decision 5:E2E 失敗時上傳 `playwright-report/` artifact

使用 `actions/upload-artifact@v4` + `if: always()`。

**理由:**
- Playwright 失敗時的 HTML report 是主要 debug 手段;沒有上傳就只能從 log 猜
- `if: always()` 確保失敗流程也會執行上傳(預設只在前面步驟成功才跑)

### Decision 6:npm 快取以 `frontend/package-lock.json` 為 key

`actions/setup-node@v4` 的 `cache-dependency-path: frontend/package-lock.json`(repo 根目錄沒有 lockfile)。

## Risks / Trade-offs

- **Risk**:Playwright 瀏覽器下載偶爾慢或失敗 → Mitigation:`actions/setup-node@v4` cache 對 npm 有效但不包 Playwright browsers。目前只裝一個 Chromium,影響有限。日後若要加速,再考慮 `~/.cache/ms-playwright` 快取(需小心 cache key)
- **Risk**:`tsc -b --noEmit` 會讀 `tsconfig.node.json` 的範圍,若該 config 含 Vite plugin 等相依且版本錯亂可能 fail → Mitigation:本機先跑過驗證
- **Risk**:`npm run dev`(Vite dev mode)在 Playwright CI 內啟動,跟 production build 行為可能有差 → 此 change 不處理,若日後 e2e 需要跑 production build,改 `playwright.config.ts` 的 `webServer.command` 為 `npm run preview`
- **Trade-off**:每個 job 獨立 `npm ci` 約 10–30 秒成本 × 6。作為第一版 CI 可接受;之後可用 reusable workflow 或 composite action 抽掉重複
