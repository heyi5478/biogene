## Why

前兩個 change 已分別在後端建好 FastAPI gateway、在前端備妥 API client / React Query hook 層。現在最後一步：把 `frontend/src/pages/Index.tsx` 與 `frontend/src/components/ConditionResults.tsx` 從「靜態 import `mockPatients`」切成「`usePatients()` 打 gateway」，補上 loading / error UI，並退役 `frontend/src/data/mockData.ts` 的 runtime 匯出。完成後前端首頁即為真正的前後端分離應用。

## What Changes

- `frontend/src/pages/Index.tsx`：
  - 移除 `import { mockPatients } from '@/data/mockData'`
  - 改用 `const { data: patients, isLoading, isError, error } = usePatients();`
  - 將原本操作 `mockPatients` 的陣列（文字搜尋、條件過濾）改為操作 `patients ?? []`
  - 新增 loading skeleton（沿用 `components/ui/skeleton.tsx`）
  - 新增 error 狀態（顯示錯誤訊息 + 重試按鈕，沿用 `components/ui/alert.tsx`）
- `frontend/src/components/ConditionResults.tsx`：
  - `evaluateConditions` 簽章不變（仍接 `Patient[]`），呼叫端改傳 `patients ?? []`
- **BREAKING**：`frontend/src/data/mockData.ts`
  - 移除 `export const mockPatients`（runtime 匯出）
  - 型別 re-export（`export type { Patient } from '@/types/patient'`）保留，以免既有 import 斷裂；若再無 runtime 消費者，整檔可視情況刪除並將型別 re-export 遷至 barrel file
  - 移除 `import` 自 `backend/mock-data/**.json`（Vite JSON import）——後端 JSON 從此只透過 HTTP 到達前端
- Playwright E2E（`frontend/tests/**`）：
  - 現有 test 若依賴「立刻顯示患者列表」的時序，改為等待 `getByRole('...', { name: /姓名/ })` 等語意選擇器或適當 `waitFor`（Playwright 預設 auto-wait 通常足夠，但須複核）
  - 若有測試從 `mockPatients` 讀取資料做斷言，改為讀取 fixture 或直接用寫入 MSW/後端的固定資料
- 更新 `frontend/README.md` 或 `backend/README.md`：明載「前端需後端 gateway 運行」，補「npm run dev 前先啟動後端」流程

## Capabilities

### New Capabilities

- `frontend-patient-data`: 明定前端患者資料來源為後端 gateway、必要 loading / error UX、以及 `Patient` 型別與 gateway response 的契約關係

### Modified Capabilities

- `mock-data-layer`: 移除「前端以 Vite JSON import 讀取 mock data」要求（被 gateway HTTP 取代），其他（JSON 檔佈局、UUID v5、FK 完整性、NBS 子表）維持不變

## Impact

- **修改檔案**：
  - `frontend/src/pages/Index.tsx`
  - `frontend/src/components/ConditionResults.tsx`（僅呼叫方式，不改 evaluateConditions 函式）
  - `frontend/src/data/mockData.ts`（移除 runtime 匯出；保留型別 re-export 或整檔移除）
  - `frontend/tests/**`（視既有選擇器是否需調整）
  - `frontend/README.md` / `backend/README.md`
- **執行時相依**：前端必須連得上 gateway（`http://localhost:8000`）才會顯示資料；關機情境由 error UI 覆蓋
- **相容性**：`Patient` 型別形狀不變，故 UI 元件邏輯完全可重用；僅資料抵達時機從「synchronous import」變成「async query」
- **E2E**：若 CI 環境尚未能啟動真實後端，須視使用者意願選擇下列之一（留待 Open Questions）：
  - A：在 CI 跑 FastAPI gateway → 真實整合 E2E
  - B：在 test build 注入 MSW handlers → 仍可跑 Playwright 但不連真後端
  - C：將 Playwright 暫標為 `skip` 並於下一 change 補
- **下游**：完成後，前端可直接受益於後端未來加上 MySQL、mutation、authn 等變更，無需再動 Index.tsx
