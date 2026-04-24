## Why

`統計` 與 `匯出` 兩顆按鈕目前與七顆模組跳轉按鈕（門診／MS/MS／AA／Enzyme／GAG／DNA／外送）擠在 `PatientSummary` 右上角的同一個 `flex-wrap` 容器裡（`max-w-[260px]`）。兩類按鈕的語義並不相同：`統計` / `匯出` 是對整位病人執行的全域動作，模組跳轉按鈕是導航輔助。把它們混排造成視覺擁擠，也讓使用者較難辨識主要動作。

將 `統計` / `匯出` 移到 Tab 列（`全部 / 基本資料 / 門診 / 檢驗 / 檢體 / 新生兒篩檢`）的右側，可以：

- 釋放 `PatientSummary` 的右側空間給模組跳轉按鈕使用，避免擠壓
- 將「全域動作」與「內容切換」在視覺上並置，提升資訊階層
- 維持現有樣式與行為，僅變更位置

## What Changes

- 新增元件 `frontend/src/components/PatientActions.tsx`：封裝 `統計` / `匯出` 按鈕、`statsOpen` / `exportOpen` 狀態、以及 `StatsDialog` / `ExportDialog` 的渲染
- `frontend/src/pages/Index.tsx`：在 `<Tabs>` 內把 `<TabsList>` 與新的 `<PatientActions>` 用 `flex items-center justify-between` 並排成一列
- `frontend/src/components/PatientSummary.tsx`：移除 `統計` / `匯出` 按鈕及其狀態、對話框渲染與相關 import；保留七顆模組跳轉按鈕及其現有樣式
- 視覺與互動行為不變：按鈕的 `variant`（`success` / `info`）、size、icon 與點擊後開啟 Dialog 的行為完全沿用

不包含：Dialog 內部邏輯變更、按鈕樣式變更、模組跳轉按鈕位置變更。

## Capabilities

### New Capabilities
（無）

### Modified Capabilities
- `patient-statistics`: 將「PatientSummary SHALL expose a single-patient statistics entry point」的需求放寬為由新的 `PatientActions` 元件承載入口，並更新 calcAge 去重的驗證來源
- `patient-export`: 將「PatientSummary SHALL expose an export entry point」的需求放寬為由新的 `PatientActions` 元件承載入口
- `shared-ui-buttons`: 更新「Designated action buttons SHALL use the matching semantic variant」的檔案指涉，使 `統計` / `匯出` 指向新的 `PatientActions.tsx`，其餘規則不變

## Impact

- 影響檔案：
  - 新增：`frontend/src/components/PatientActions.tsx`
  - 修改：`frontend/src/pages/Index.tsx`、`frontend/src/components/PatientSummary.tsx`
  - 參考（不改）：`frontend/src/components/stats/StatsDialog.tsx`、`frontend/src/components/export/ExportDialog.tsx`、`frontend/src/components/ui/tabs.tsx`
- 相依規格：`patient-statistics`、`patient-export`、`shared-ui-buttons`
- 無後端、API、資料或部署影響；純前端 UI 重構
- 無新相依套件
