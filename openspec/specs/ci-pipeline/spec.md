# ci-pipeline Specification

## Purpose
TBD - created by archiving change add-pr-ci-workflow. Update Purpose after archive.
## Requirements
### Requirement: PR CI 觸發條件

CI workflow SHALL 僅在 GitHub Pull Request 事件、且目標分支為 `main` 時觸發。其他事件(push 到任意分支、schedule、workflow_dispatch)MUST NOT 觸發此 workflow。

#### Scenario: PR 目標為 main
- **WHEN** 開發者開啟、更新、或 reopen 一個目標分支為 `main` 的 Pull Request
- **THEN** workflow `ci.yml` 自動執行,並在 PR 狀態欄顯示各 job 的執行結果

#### Scenario: PR 目標非 main
- **WHEN** 開發者開啟目標分支為其他分支(例如 `develop`、`release/*`)的 PR
- **THEN** workflow `ci.yml` MUST NOT 執行

#### Scenario: 直接 push 到 main
- **WHEN** 有 commit 被 push 到 `main`(例如 merge 後)
- **THEN** workflow `ci.yml` MUST NOT 執行

### Requirement: 執行環境與版本

所有 CI job SHALL 在 `ubuntu-latest` runner 上執行,並使用 Node.js 主版本 22。所有 job 的預設工作目錄 MUST 為 `./frontend`。

#### Scenario: Node 版本一致
- **WHEN** 任一 job 執行
- **THEN** `node --version` 的輸出 SHALL 以 `v22.` 開頭

#### Scenario: 工作目錄
- **WHEN** job 中執行 `npm` 或 `npx` 指令
- **THEN** 該指令 SHALL 在 `frontend/` 目錄內執行(透過 `defaults.run.working-directory` 設定)

### Requirement: 相依套件安裝與快取

每個 job SHALL 在執行檢查前先用 `actions/checkout@v4` 取得程式碼、用 `actions/setup-node@v4` 安裝 Node,並啟用 npm 快取,最後以 `npm ci` 安裝相依。

#### Scenario: 啟用 npm 快取
- **WHEN** `actions/setup-node@v4` 被呼叫
- **THEN** 其 `cache` 輸入 SHALL 為 `'npm'`,且 `cache-dependency-path` SHALL 為 `frontend/package-lock.json`

#### Scenario: 使用 npm ci 而非 npm install
- **WHEN** 安裝相依
- **THEN** 指令 SHALL 為 `npm ci`(確保 lockfile 鎖定),禁止使用 `npm install`

### Requirement: Lint 檢查

workflow SHALL 包含名為 `lint` 的 job,執行 `npm run lint`,任一 ESLint 錯誤皆 MUST 使此 job 失敗。

#### Scenario: Lint 通過
- **WHEN** 程式碼無 ESLint 錯誤
- **THEN** `lint` job 以 exit code 0 結束

#### Scenario: Lint 失敗
- **WHEN** 程式碼包含 ESLint 錯誤
- **THEN** `lint` job 以非零 exit code 結束,PR status 顯示為失敗

### Requirement: Prettier 格式檢查

workflow SHALL 包含名為 `format` 的 job,執行 `npm run format:check`,未按 Prettier 規則格式化的檔案 MUST 使此 job 失敗。

#### Scenario: 格式通過
- **WHEN** 所有檔案符合 Prettier 格式
- **THEN** `format` job 以 exit code 0 結束

#### Scenario: 格式錯誤
- **WHEN** 有檔案未按 Prettier 格式化
- **THEN** `format` job 失敗,log 顯示受影響檔案

### Requirement: TypeScript 型別檢查

workflow SHALL 包含名為 `typecheck` 的 job,執行 `npm run typecheck`(對應 `tsc -b --noEmit`),任一型別錯誤 MUST 使此 job 失敗。`frontend/package.json` SHALL 定義 `typecheck` script。

#### Scenario: 型別檢查通過
- **WHEN** 所有 TypeScript 程式碼通過 `tsc -b --noEmit`
- **THEN** `typecheck` job 以 exit code 0 結束

#### Scenario: 型別錯誤
- **WHEN** 有任何檔案包含 TypeScript 型別錯誤
- **THEN** `typecheck` job 失敗

#### Scenario: typecheck script 存在
- **WHEN** 讀取 `frontend/package.json`
- **THEN** `scripts.typecheck` 欄位 SHALL 存在,且值為 `tsc -b --noEmit`

### Requirement: 單元測試

workflow SHALL 包含名為 `test` 的 job,執行 `npm test`(對應 `vitest run` 單次執行),任一測試失敗 MUST 使此 job 失敗。

#### Scenario: 全部測試通過
- **WHEN** 所有 Vitest 測試成功
- **THEN** `test` job 以 exit code 0 結束

#### Scenario: 有測試失敗
- **WHEN** 任一 Vitest 測試失敗
- **THEN** `test` job 失敗

### Requirement: Production build

workflow SHALL 包含名為 `build` 的 job,執行 `npm run build`(對應 `vite build`),build 失敗 MUST 使此 job 失敗。

#### Scenario: Build 成功
- **WHEN** Vite production build 成功產出
- **THEN** `build` job 以 exit code 0 結束

#### Scenario: Build 失敗
- **WHEN** Vite production build 發生錯誤
- **THEN** `build` job 失敗

### Requirement: Playwright E2E 測試

workflow SHALL 包含名為 `e2e` 的 job,執行 Playwright 測試。此 job MUST 在跑測試前安裝 Chromium 瀏覽器及其系統相依,並在失敗時上傳 `playwright-report/` 作為 GitHub artifact。

#### Scenario: 安裝瀏覽器
- **WHEN** `e2e` job 執行
- **THEN** 在 `npm ci` 之後、`npx playwright test` 之前,SHALL 執行 `npx playwright install --with-deps chromium`

#### Scenario: 測試通過
- **WHEN** 所有 Playwright 測試成功
- **THEN** `e2e` job 以 exit code 0 結束,不需上傳 artifact

#### Scenario: 測試失敗時上傳 report
- **WHEN** `npx playwright test` 失敗
- **THEN** 後續步驟 SHALL 使用 `actions/upload-artifact@v4` 上傳 `frontend/playwright-report/`,步驟設定 `if: always()` 以確保即便前一步驟失敗仍會執行

### Requirement: Job 併行與獨立性

所有六個 job(`lint`、`format`、`typecheck`、`test`、`build`、`e2e`)SHALL 可獨立併行執行,彼此間 MUST NOT 存在 `needs` 依賴。

#### Scenario: 一 job 失敗不影響其他 job
- **WHEN** 任一 job(例如 `lint`)失敗
- **THEN** 其他 job 仍會完整執行至結束,個別回報結果

