## 1. 本機準備

- [x] 1.1 在 `frontend/package.json` 的 `scripts` 中新增 `"typecheck": "tsc -b --noEmit"`(放在 `lint:fix` 之後)
- [x] 1.2 於 `frontend/` 執行 `npm run typecheck`,確認無錯誤且 exit code 0
- [x] 1.3 於 `frontend/` 依序執行 `npm run lint`、`npm run format:check`、`npm test`、`npm run build`,確認全部通過 — 首次有 113 個 lint errors 未修,由後續 PR #13 修完;其餘檢查皆通過

## 2. 建立 workflow 檔案

- [x] 2.1 在 repo 根目錄建立 `.github/workflows/` 資料夾(若不存在)
- [x] 2.2 新增 `.github/workflows/ci.yml`,定義:
  - `name: CI`
  - `on.pull_request.branches: [main]`
  - `defaults.run.working-directory: ./frontend`(在 workflow 層級或每個 job 層級)
  - 六個獨立 job:`lint`、`format`、`typecheck`、`test`、`build`、`e2e`

- [x] 2.3 為六個 job 共同撰寫前置步驟:
  - `runs-on: ubuntu-latest`
  - `actions/checkout@v4`
  - `actions/setup-node@v4` with `node-version: '22'`、`cache: 'npm'`、`cache-dependency-path: frontend/package-lock.json`
  - `run: npm ci`

- [x] 2.4 各 job 主要指令:
  - `lint`:`run: npm run lint`
  - `format`:`run: npm run format:check`
  - `typecheck`:`run: npm run typecheck`
  - `test`:`run: npm test`
  - `build`:`run: npm run build`

- [x] 2.5 `e2e` job 額外步驟:
  - 在 `npm ci` 之後新增 `run: npx playwright install --with-deps chromium`
  - 執行 `run: npx playwright test`
  - 新增 `actions/upload-artifact@v4` 步驟,`if: always()`,`name: playwright-report`,`path: frontend/playwright-report/`,`retention-days: 7`

## 3. 驗證

- [x] 3.1 用 `actionlint`(若可用)或 VS Code GitHub Actions extension 檢查 `ci.yml` 語法 — 本機無 actionlint,改用 `python3 -c "import yaml; yaml.safe_load(...)"` 驗證 YAML 合法且六個 job 齊全
- [x] 3.2 提交變更到 feature branch 並開啟 PR 目標為 `main` — PR #5 (`chore/add-pr-ci-workflow`) 及後續一連串修復 PR (#8, #9, #10, #12, #13) 均以 `main` 為目標
- [x] 3.3 確認 GitHub Actions 頁面顯示六個 job 皆執行(`lint`、`format`、`typecheck`、`test`、`build`、`e2e`)— 每個 PR run 都能看到六個 job
- [x] 3.4 確認六個 job 全部通過,PR check section 顯示綠色 — PR #13 run `24701902813` 六個 job 全綠
- [x] 3.5 刻意在一個檔案中製造 lint 錯誤 push 一次,確認 `lint` job 失敗而其他 job 不受影響 — 由 PR #9 (calendar fix) run `24700654831` 有機驗證:`Lint failure`、其餘 5 個 job 全 success,證明 job 獨立性
- [x] 3.6 刻意讓 e2e 失敗一次,確認 GitHub Actions 頁面有 `playwright-report` artifact 可下載 — `tmp/verify-e2e-artifact` run `24700905069` 的 E2E job failure、`playwright-report` artifact 成功上傳(199961 bytes);驗證完已刪除 throwaway branch

## 4. 收尾

- [x] 4.1 確認所有驗證性的暫時改動都已 revert — 無殘留;`tmp/verify-e2e-artifact` 及所有 fix branches 皆已 merge 或刪除
- [x] 4.2 更新 PR description 說明新增的 CI workflow — PR #5 description 已於建立時寫入
- [x] 4.3 告知使用者接著可在 GitHub Settings → Branches 為 `main` 啟用 required status checks(不在此 change 範圍,僅作為交接資訊)— 使用者已知悉並表示自行處理
