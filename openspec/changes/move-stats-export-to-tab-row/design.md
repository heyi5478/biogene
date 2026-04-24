## Context

[PatientSummary.tsx](frontend/src/components/PatientSummary.tsx) 目前在右上角用一個 `flex max-w-[260px] flex-wrap justify-end gap-1` 的容器放了 9 顆小按鈕：

- `統計`（variant=success）、`匯出`（variant=info） — 對整位病人執行的全域動作
- 7 顆模組跳轉鈕 `門診 / MS/MS / AA / Enzyme / GAG / DNA / 外送`（variant=outline） — 切換下方 Tab 與顯示模組

下方 [Index.tsx](frontend/src/pages/Index.tsx) 緊接著渲染 `<Tabs>`，其 `<TabsList className="h-8">` 包含 6 個 `<TabsTrigger>`（全部 / 基本資料 / 門診 / 檢驗 / 檢體 / 新生兒篩檢）。`TabsList` 右側有大片空白。

`StatsDialog` 與 `ExportDialog` 的開關狀態（`statsOpen`、`exportOpen`）目前由 `PatientSummary` 以 `useState` 持有，兩個 Dialog 也在 `PatientSummary` 內部渲染。

相關規格：

- `patient-statistics` 規定 `PatientSummary` 必須暴露統計入口
- `patient-export` 規定 `PatientSummary` 必須暴露匯出入口
- `shared-ui-buttons` 規定「統計」與「匯出」按鈕分別用 `variant="success"` 與 `variant="info"`，並指涉檔案 `PatientSummary.tsx`

## Goals / Non-Goals

**Goals:**

- 把 `統計` 與 `匯出` 按鈕移到 Tab 列右側，與 `TabsList` 並排成同一列
- 保留按鈕的 variant、size、icon 與互動行為
- 保留模組跳轉按鈕在 `PatientSummary` 內
- 保持 Radix Tabs 的行為不變（active tab state、keyboard navigation 等）
- 更新相關規格以反映按鈕新位置

**Non-Goals:**

- 不改 `StatsDialog` / `ExportDialog` 內部邏輯或 API
- 不動 `shared-ui-buttons` 中 variant 的顏色或語義規則
- 不調整 Tab 的數量、順序、樣式
- 不調整模組跳轉按鈕
- 不引入新相依套件
- 不做響應式重新設計（窄螢幕行為僅需「不破版」即可）

## Decisions

### 決策 1：以新元件 `PatientActions` 封裝，而非把狀態升到 `Index.tsx`

**選項：**

- A. 將 `statsOpen` / `exportOpen` 狀態、`StatsDialog` / `ExportDialog` 渲染全部搬到 [Index.tsx](frontend/src/pages/Index.tsx)
- B. 新增元件 `PatientActions.tsx`，封裝兩顆按鈕、兩個 Dialog、兩個狀態，並在 Tab 列渲染 `<PatientActions patient={displayPatient} />`

**選 B。** 理由：

- `Index.tsx` 已 376 行、管理 10+ 個 state，再塞兩個 modal state 會繼續膨脹
- `StatsDialog` / `ExportDialog` 的 lifecycle 與其觸發按鈕天然耦合，封裝在一起讓測試與重用更容易
- `PatientActions` 介面極簡（`{ patient: Patient }`），未來若要加第三顆全域動作按鈕（例如「列印」）只需改 `PatientActions`

### 決策 2：用 `<div className="flex items-center justify-between gap-2">` 包住 `TabsList` 與 `PatientActions`

**選項：**

- A. 把按鈕塞進 `<TabsList>` 內，模擬「非 TabsTrigger 的子節點」
- B. 在 `<Tabs>` 內、`<TabsList>` 外，包一個 flex 容器，讓 `TabsList` 與 `PatientActions` 成為同層兄弟

**選 B。** 理由：

- `TabsList` 的 `inline-flex bg-muted rounded-md p-1` 是為 Tab 觸發器設計的容器，放入非 Trigger 元素會破壞樣式與 Radix 行為
- Radix Tabs 不要求 `TabsList` 必須是 `Tabs` 的直接子節點，中間夾一個 `<div>` 不影響 context 傳遞
- `justify-between` 讓左側 `TabsList` 與右側 `PatientActions` 自然分靠兩端；`items-center` 讓不同高度（`h-8` vs `h-6`）的元素垂直對齊

### 決策 3：`PatientActions` 外層加 `shrink-0`，`TabsList` 允許被壓縮

窄螢幕下 6 個 TabsTrigger + 2 顆按鈕總寬度可能溢位。將 `PatientActions` 用 `shrink-0` 鎖住尺寸，讓 `TabsList` 先被壓縮（Radix 的 TabsList 本身會撐開內部；若實際測試出現溢位，可再加 `min-w-0 overflow-x-auto` 到 `TabsList`）。本次不預先加 `overflow-x-auto`，避免無必要的樣式噪音。

### 決策 4：按鈕視覺保持完全一致

按鈕的 JSX 從 `PatientSummary` 搬到 `PatientActions` 時，`variant`、`size`、`className`、icon 完全照搬，不微調。理由：`shared-ui-buttons` 規格仍要求 `variant="success"` / `variant="info"`；使用者也習慣目前外觀。

## Risks / Trade-offs

- **風險：Radix `Tabs` 若依賴 `TabsList` 是直接子節點** → 緩解：已查 `tabs.tsx` 封裝僅透過 `TabsPrimitive`，而 Radix 官方 API 透過 React Context 傳遞，不要求 DOM 直接子節點；實作後要在瀏覽器驗證 active tab state、hover、keyboard focus 皆正常
- **風險：窄螢幕溢位** → 緩解：`PatientActions` 加 `shrink-0`，TabsList 可自然壓縮；驗證階段在 768px / 1024px / 1280px 各測一次
- **風險：改動規格文字但漏掉舊規格的其他間接引用** → 緩解：archive 前跑 `openspec validate`，並全文搜尋 `PatientSummary.tsx` 在 specs 中的出現位置，逐一審閱
- **Trade-off：新增一個元件檔會稍增導覽成本** → 值得，因為減少 `Index.tsx` 的狀態，且 `PatientActions` 語義清晰（「這個病人可做的全域動作」）

## Migration Plan

- 本變更為純前端 UI 搬移，無資料遷移、無 API 變動、無向後相容考量
- 部署後使用者立即看到新位置；Dialog 行為不變
- 回滾：單純 git revert 即可，無額外清理

## Open Questions

無。所有設計決策已在決策 1-4 敲定。
