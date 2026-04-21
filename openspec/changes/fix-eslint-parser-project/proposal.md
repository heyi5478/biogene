## Why

`npm run lint` 目前產生 75 個錯誤,其中多數是:

```
Parsing error: "parserOptions.project" has been provided for @typescript-eslint/parser.
The file was not found in any of the provided project(s): <path>
```

受影響的檔案至少包含:
- `src/test/setup.ts`、`src/test/**/*.test.ts`
- `src/types/medical.ts`
- `src/vite-env.d.ts`
- `tailwind.config.ts`、`vite.config.ts`、`vitest.config.ts`
- `tests/seed.spec.ts`

根本原因:`frontend/eslint.config.js` 第 41 行設定 `parserOptions.project: './tsconfig.json'`,但 `tsconfig.json` 是 composite root(`"files": []`),實際檔案由 `tsconfig.app.json`(`include: ["src"]`)與 `tsconfig.node.json` 涵蓋;而測試檔、`src/types/`、設定檔、Playwright 測試都不在這兩個 include 範圍內。ESLint 因此無法為這些檔案建立 TypeScript 程式分析上下文,整個檔案的 parse 都失敗。

此問題阻擋 CI 的 `lint` job,需在啟用 branch protection 前修好。

## What Changes

預計評估下列三種方案,選一實作:

- **方案 A**(優先評估):改用 `parserOptions.projectService: true`(typescript-eslint 8 新 API,自動發現最相關的 tsconfig)
- **方案 B**:改為 `parserOptions.project: true`(舊版 auto-project,可能會慢)
- **方案 C**:新增 `frontend/tsconfig.lint.json` 明確 include 所有需要 lint 的檔案(`src/**`、`tests/**`、`*.config.ts` 等),並將 `parserOptions.project` 指向它

選定方案後:
- 修改 `frontend/eslint.config.js`(或新增 `tsconfig.lint.json`)
- 確認 `npm run lint` 所有 75 個 parse 錯誤消失
- 確認既有通過的規則未被弱化(例如仍能抓出 `@typescript-eslint/no-floating-promises` 等需型別資訊的規則)

## Capabilities

### New Capabilities

<!-- 無新 capability -->

### Modified Capabilities

<!-- 無 spec 層級需求變動,純設定調整 -->

## Impact

- **修改檔案**:至少 `frontend/eslint.config.js`;方案 C 另增 `frontend/tsconfig.lint.json`
- **不變動**:現有 lint 規則條目、`tsconfig.app.json`、`tsconfig.node.json`
- **風險**:
  - 方案 A/B 可能拖慢 ESLint(需要全專案 type-check 啟動)
  - 方案 C 維護負擔多一個 tsconfig
  - 任一方案若設定錯誤,可能讓原本能抓到的錯誤被靜悄悄略過
- **相依套件**:無新增(`typescript-eslint` 已是 `^8.38.0`,支援 `projectService`)
