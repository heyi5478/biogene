## Why

目前 repo 沒有任何 GitHub Actions workflow(`.github/workflows/` 不存在),PR 合入 `main` 前沒有任何自動化把關。Lint、型別錯誤、格式違規、測試失敗、build 壞掉都必須靠開發者本機記得跑,容易漏掉且無法在 PR review 時客觀呈現結果。

為了建立最低限度的品質基準,需要在每次 PR 目標為 `main` 時自動執行完整檢查,並讓結果顯示在 PR 上。

## What Changes

- 新增 GitHub Actions workflow `.github/workflows/ci.yml`,於 `pull_request` 目標為 `main` 時觸發
- 在單一 workflow 中併行執行六個 job:
  - `lint`:`npm run lint`(ESLint)
  - `format`:`npm run format:check`(Prettier)
  - `typecheck`:`npm run typecheck`(TypeScript,新 script)
  - `test`:`npm test`(Vitest)
  - `build`:`npm run build`(Vite production build)
  - `e2e`:Playwright end-to-end 測試(含瀏覽器安裝、失敗時上傳 report)
- 為 `frontend/package.json` 新增 `typecheck` script:`tsc -b --noEmit`(因 tsconfig 使用 project references)
- 所有 job 使用 Node 22、`actions/checkout@v4`、`actions/setup-node@v4` 並啟用 npm cache
- 所有 job 的 working-directory 設為 `./frontend`
- 不處理 branch protection / required status checks(由 repo 擁有者在 GitHub UI 自行設定)

## Capabilities

### New Capabilities

- `ci-pipeline`:定義 PR 回 `main` 時的自動化檢查流程、觸發條件、執行環境、各檢查步驟的成功準則,以及 artifact 產出方式

### Modified Capabilities

<!-- 無既有 spec,全部為新增 -->

## Impact

- **新增檔案**:`.github/workflows/ci.yml`
- **修改檔案**:`frontend/package.json`(新增 `typecheck` script)
- **不變動**:任何應用程式程式碼、測試程式碼、ESLint / Prettier / tsconfig / Playwright 設定皆不異動
- **對開發者**:之後 PR 會自動觸發 CI,失敗的檢查會阻擋 merge(若 repo 擁有者啟用 branch protection)
- **對 CI 成本**:每次 PR 會在 GitHub-hosted runner 跑六個 job(其中 e2e 最慢,需下載 Chromium)
- **相依套件**:不新增任何 npm 套件;`@playwright/test` 1.57 已存在
