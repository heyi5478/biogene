## Why

`npm run typecheck`(`tsc -b --noEmit`)目前在 `frontend/src/components/ui/calendar.tsx:55` 回報:

```
error TS2353: Object literal may only specify known properties, and 'IconLeft' does not exist in type 'Partial<CustomComponents>'.
```

原因是 `react-day-picker` 升級到 v9 後,`components` 介面移除 `IconLeft` / `IconRight`,改以單一 `Chevron` 元件配合 `orientation` prop 處理。目前 calendar.tsx 仍用 v8 API。

此錯誤阻擋 CI 的 `typecheck` job;必須修正後,`chore/add-pr-ci-workflow` 合併、branch protection 啟用後新 PR 才會通過。

## What Changes

- 更新 `frontend/src/components/ui/calendar.tsx` 的 `components` 設定:
  - 移除 `IconLeft` / `IconRight`
  - 改用 `Chevron: ({ orientation }) => orientation === 'left' ? <ChevronLeft .../> : <ChevronRight .../>`(或依 react-day-picker v9 文件建議寫法)
- 確認 `npm run typecheck` 通過
- 本地視覺檢查 calendar 元件的左右箭頭仍正常顯示

## Capabilities

### New Capabilities

<!-- 無新 capability -->

### Modified Capabilities

<!-- 無 spec 層級需求變動,純實作層修正 -->

## Impact

- **修改檔案**:`frontend/src/components/ui/calendar.tsx`
- **影響範圍**:所有使用 `<Calendar>` 元件的頁面(目前於 `src/components/ui/` 內的複合元件)的左右換頁箭頭
- **相依套件**:無改動(已是 react-day-picker `^9.14.0`)
- **風險**:若 v9 `Chevron` prop 介面與本方案不符,箭頭可能顯示異常 — 本機需手動驗證
