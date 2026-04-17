

# 新增「條件查詢」模式 — 修改計畫

## 現狀 vs 新需求

目前頁面只有「病人查詢」模式（輸入姓名/病歷號找病人）。新規格要求在同一頁面加入第二種查詢模式：**條件查詢**，讓醫師用模組 + 子欄位 + 運算子 + 值來篩選出一批病人。

## 主要變更

### 1. 頁面頂部：模式切換

在 header 加入 segmented control / pill switch，切換「病人查詢」與「條件查詢」。標題改為「基因醫學整合查詢中心」。

### 2. 新增條件建構器元件 `ConditionBuilder.tsx`

核心 UI 元件，每一列條件包含：
- **模組** 下拉選單（從 MODULE_DEFINITIONS 取值）
- **子欄位** 下拉選單（依模組動態產生）
- **運算子** 下拉選單（依欄位型態：文字用 contains/equals，數值用 >/</between，日期用 before/after/between）
- **值** 輸入框（文字/數字/日期，依型態自動切換）
- 刪除按鈕

支援：新增條件列、AND/OR 切換、清除全部。

### 3. 新增欄位定義 `types/medical.ts`

擴充型別系統：
- 為每個模組定義子欄位清單（欄位名、顯示名、型態：text/number/date/category）
- 新增 `ConditionRow` 型別（moduleId, fieldId, operator, value）
- 新增運算子定義（依欄位型態分組）

### 4. 左側面板改造 `FilterPanel.tsx`

依查詢模式顯示不同內容：
- **病人查詢模式**：維持現有搜尋框 + 模組 checkbox + preset（不變）
- **條件查詢模式**：顯示條件建構器 + 常用條件模板按鈕（Biomarker 異常、MPS 相關、最近一年外送檢體等）

### 5. 條件查詢結果元件 `ConditionResults.tsx`

條件查詢的右側結果區，顯示：
- 條件摘要列（已套用的條件 chips）
- 病人清單表格：病歷號、姓名、性別、生日、診斷、**命中條件摘要**（如「Biomarker / DBS LysoGb3 = 2.8，超過 > 1.2」）、操作按鈕
- 點擊「查看病人」後切換到病人詳情視圖（復用現有 PatientSummary + ResultModules）

### 6. 主頁面 `Index.tsx` 改造

- 新增 `queryMode` state：`'patient' | 'condition'`
- 條件查詢模式下，用 mock 資料做前端篩選，回傳符合條件的病人清單
- 從條件結果點擊病人後，進入病人詳情（復用現有元件），並提供「返回條件結果」按鈕

### 7. Mock 資料補充

在 `mockData.ts` 中確保現有 5 位病人的數值足夠多樣，能讓條件查詢產生有意義的篩選結果。

## 不需變更的部分

- PatientSummary、ResultModules、SearchSummary 等病人詳情元件維持不變
- 模組定義（MODULE_DEFINITIONS）與 PRESETS 維持不變
- 視覺風格維持不變

## 檔案清單

| 檔案 | 動作 |
|---|---|
| `src/types/medical.ts` | 擴充：加入子欄位定義、ConditionRow 型別、運算子定義 |
| `src/components/ConditionBuilder.tsx` | 新增：條件建構器 UI |
| `src/components/ConditionResults.tsx` | 新增：條件查詢結果表格 |
| `src/components/FilterPanel.tsx` | 修改：依模式切換顯示內容 |
| `src/pages/Index.tsx` | 修改：加入模式切換、條件查詢邏輯 |
| `src/data/mockData.ts` | 微調：確保數值多樣性 |

