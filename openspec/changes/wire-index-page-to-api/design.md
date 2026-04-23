## Context

`Index.tsx`（13、67 行）與 `ConditionResults.tsx`（267 行 `evaluateConditions`）是目前唯二消費 `mockPatients` 的元件。前者做列表渲染與姓名 / 病歷號文字搜尋，後者對患者陣列跑條件判斷（例如 `dbsLysoGb3 > 5`）。兩者皆為純函式化操作，無 client-side mutation。

`add-frontend-api-client-layer` 合入後，前端已擁有：
- `usePatients()`：`useQuery({ queryKey: ['patients'], queryFn: fetchPatients })`
- `@/types/patient` 是 `Patient` 的單一事實來源

本 change 的設計重點：**以最小 diff 完成切換、把風險鎖在 UI 層；不讓 `Patient` 型別或 `evaluateConditions` 邏輯改動**。

## Goals / Non-Goals

**Goals**
- Index 頁面完全改由 API 資料驅動
- 補完 loading 與 error UX（非空白頁）
- 刪除 `mockPatients` runtime 匯出，避免後續 code 又「退回」靜態資料
- 保留既有文字搜尋、條件過濾行為 100% 相容（無使用者感知回歸）

**Non-Goals**
- 不改 `evaluateConditions` 本身（函式簽章與實作不變）
- 不做伺服器端分頁/搜尋（規模小、沿用客戶端過濾）
- 不引入全站 error boundary（局部 error UI 足夠）
- 不改 Playwright test agent / CI 結構（若 E2E 需調整僅限測試檔本身）

## Decisions

### 決策 1：loading / error UX 樣式

**選擇：**
- loading：沿用 `components/ui/skeleton.tsx`，渲染 5 行 placeholder 佔位，維持列表高度穩定
- error：沿用 `components/ui/alert.tsx` 顯示錯誤標題與 `error.message`，附「重試」按鈕呼叫 React Query 的 `refetch`

理由：已存在的 shadcn/ui 元件，風格與站內一致；無需額外設計決策。

### 決策 2：空資料 vs. 載入失敗區分

- `isLoading && !data` → skeleton
- `isError` → 錯誤 alert + 重試
- `data?.length === 0` → 沿用現行「查無患者」的空狀態

確保三態互斥且每一狀態有對應 UI。

### 決策 3：ConditionResults 的資料來源

**選擇：由 `Index.tsx` 仍以 prop 傳入 `patients`**，`ConditionResults` 保持「接受 `Patient[]`」介面。

理由：
- `evaluateConditions` 為純函式、已在 267 行，不該知道資料來源
- 若改成 `ConditionResults` 內自呼 `usePatients()`，會造成兩份 query 快取與重複渲染（React Query 會 dedupe，但 prop 介面更明確）

### 決策 4：`mockData.ts` 的命運

**選擇：階段式退役**

Step A（本 change）：
- 移除 `export const mockPatients`
- 移除從 `backend/mock-data/` 的 Vite JSON import（整個陣列組裝程式碼）
- 保留 `export type { Patient } from '@/types/patient'`（若 re-export 已在 `add-frontend-api-client-layer` 遷完，則此檔可能只剩型別 re-export，可整檔移除並把 re-export 改至 `src/types/patient.ts` 直接供 import）

Step B（不在本 change）：若所有既有 `@/data/mockData` import 皆已遷移，後續可整檔刪除；本 change 不強制完成此步，以降低 PR 變動面。

實作時先 `grep -r "from '@/data/mockData'"` 核對全站 import，判斷能否整檔刪除。

### 決策 5：Playwright E2E 的應對

開發環境在 CI 能否啟動 FastAPI 是關鍵決策。暫定方案（供 Open Questions 與使用者確認）：

- **方案 A（建議）**：在 `.github/workflows/ci.yml` 的 e2e job 前啟動 `backend/scripts/dev.sh` 並 `wait-on http://localhost:8000/healthz`，讓 E2E 打真後端（對齊 `mock-data` 固定資料）
- 方案 B：以 MSW handler 注入 `/patients` 回應（`.env.test` 指向 `http://localhost`），避免 CI 跑 Python
- 方案 C：暫標 Playwright 既有 test `skip`，於下一 change 補整合 E2E

本 change 預設走方案 A；若 CI 上 Python 環境準備成本過高再回退至 B。

### 決策 6：E2E 資料穩定性

後端讀取 `backend/mock-data/*.json`，其 UUID v5 deterministic、5 個 main DB 患者 chartno/姓名固定（參見 `mock-data-layer` spec），故 E2E 斷言「搜尋 A1234567 → 出現 陳志明」不需改動。

## Risks / Trade-offs

- **風險：後端未啟動時前端永久 loading / error 看不到資料**→ **緩解**：明確 error UI + 重試；文件清楚寫「需先啟後端」
- **風險：async 時序導致既有 Playwright test flaky**→ **緩解**：Playwright 預設 auto-wait；斷言用 `getByRole`/`getByText`，避免 `waitForTimeout` 硬 sleep
- **風險：後端 CORS 或 network 設定問題在合併後才發現**→ **緩解**：合併前的手動驗收清單（README 寫啟動步驟 + 典型 curl + 瀏覽器 Network tab 驗證）
- **風險：`Patient` 型別後端回傳時差一個欄位大小寫**→ **緩解**：後端 Pydantic config 已 `populate_by_name=True`；發現漂移時應於 `backend/shared/schemas.py` 修，而非前端 workaround
- **Trade-off**：不做伺服器端搜尋短期簡單，日後患者數量大增會成為效能問題；到時再新增 change

## Migration Plan

1. 開發環境：本機啟後端四服務 → `npm run dev` → 驗證首頁、搜尋、條件過濾
2. 關掉後端 → 驗證 error UI + 重試
3. 更新 E2E（若需要）並在本機跑過
4. CI：若採方案 A，調整 `.github/workflows/ci.yml` 於 e2e job 啟動 Python 後端
5. PR 合入

Rollback：revert PR 即可；`Patient` 型別與 `mockData.ts` 的 git 歷史仍保留，可快速還原靜態 import。

## Open Questions

- E2E 方案 A/B/C 擇哪一？建議 A；若 CI 運行時間成為問題可改 B
- `mockData.ts` 在本 change 內整檔刪除或僅移除 runtime 匯出？建議視 grep 結果當下判斷，二者皆在本 change 範圍內可接受
