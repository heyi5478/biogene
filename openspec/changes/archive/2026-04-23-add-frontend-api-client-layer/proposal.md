## Why

前端目前沒有任何 HTTP client、API service 層或 React Query hooks，資料全靠 `frontend/src/data/mockData.ts` 直接 `import` 後端 JSON。要把首頁與後續頁面切換到打後端 gateway，必須先建一套可重用、型別安全的 API 基礎設施，獨立於 UI 變更之外，以降低下一 change（`wire-index-page-to-api`）的風險面與 PR 大小。

## What Changes

- 新增環境變數設定：
  - `frontend/.env.development`：`VITE_API_BASE_URL=http://localhost:8000`
  - `frontend/.env.example`：供共筆者參考
  - `frontend/src/vite-env.d.ts` 擴充 `ImportMetaEnv` 型別
- 新增 HTTP client 薄包：
  - `frontend/src/lib/api.ts`：`apiGet<T>(path)` 等函式，集中 base URL、JSON parse、錯誤轉換（HTTP 非 2xx → typed `ApiError`）
- 新增 service 函式層（純函式、無 React 相依）：
  - `frontend/src/services/patients.ts`：`fetchPatients()`、`fetchPatient(id)`
  - 回傳型別沿用現有 `Patient` interface（將 `Patient` 及其 sample/record 子型別從 `types/medical.ts` 搬至 `types/patient.ts`，`types/medical.ts` re-export 以保持既有 7 處元件 import 不動）
- 新增 React Query hook 層：
  - `frontend/src/hooks/queries/usePatients.ts`：`usePatients()`
  - `frontend/src/hooks/queries/usePatient.ts`：`usePatient(patientId)`
  - 定義統一 `queryKey` 規則（`['patients']`、`['patients', id]`）於 `src/hooks/queries/keys.ts`
- `frontend/src/App.tsx` 設定 `QueryClient` 預設 options：`staleTime=60_000`、`retry=1`、`refetchOnWindowFocus=false`（開發用合理值）
- **不動**：`frontend/src/data/mockData.ts`、`frontend/src/pages/Index.tsx`、`frontend/src/components/**` — UI 行為完全不變
- 加 smoke 單元測試：以 MSW 或簡單 fetch mock 驗證 `apiGet` 錯誤處理與 `usePatients` queryKey

## Capabilities

### New Capabilities

- `frontend-api-client`: 前端對後端的 HTTP 存取層，定義 base URL 來源、錯誤模型、service 函式命名慣例、React Query hook 命名與 queryKey 規則

### Modified Capabilities

（無——本 change 純新增基礎設施，不改既有行為；`mock-data-layer` 規定的 Vite JSON import 行為在本 change 仍然保留）

## Impact

- **新增程式碼**：`frontend/src/lib/api.ts`、`frontend/src/services/*`、`frontend/src/hooks/queries/*`、`frontend/src/types/patient.ts`、`.env.development`、`.env.example`
- **修改**：`frontend/src/App.tsx`（QueryClient options）、`frontend/src/vite-env.d.ts`（env 型別）、`frontend/src/types/medical.ts`（將 Patient aggregate 搬出並 re-export）
- **相依性**：無新套件（`@tanstack/react-query` 已存在，fetch 用內建 Web API）；測試若採 MSW 則新增 `msw` dev dep
- **下游 change**：解鎖 `wire-index-page-to-api`
- **風險低**：此 change 不改任何現有元件行為；最壞情況是新增檔案未被使用，可直接 revert
