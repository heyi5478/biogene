## Context

前端現況（2026-04-22）：
- `@tanstack/react-query@5.83.0` 已安裝，`App.tsx` 已包 `QueryClientProvider`，但**無任何 useQuery 實作**
- 無 `.env` 檔、無 `VITE_API_BASE_URL`、無 `src/lib/api` 或 `src/services` 目錄
- `Patient` 型別定義在 `frontend/src/types/medical.ts`（與 module/condition 等 ~800 行其他型別混居），被 7 處元件共用；`data/mockData.ts` 僅 import 不 export
- 下一 change (`wire-index-page-to-api`) 會實際切掉 `mockPatients` 靜態 import

本 change 的設計重點是：**把基礎設施做得扎實，讓下一 change 的 UI 切換單純到「改一行 import + 加 loading/error」**。

並行前提：`add-fastapi-microservices-skeleton` 已合入、gateway 於 `http://localhost:8000` 可提供 `GET /patients`。

## Goals / Non-Goals

**Goals**
- 前端有穩定、可單測的 API 存取層，不依賴具體 UI
- Base URL 由 env 驅動，dev/prod/test 可切換
- `queryKey` 規則統一，方便日後新增快取失效與 mutation
- `Patient` 型別與後端 gateway response 對齊（同 camelCase，欄位名不變）
- 錯誤模型一致：HTTP 非 2xx 統一丟 `ApiError`，React Query 可辨識

**Non-Goals**
- 不改任何現有頁面/元件
- 不寫 mutation hooks（目前無寫入需求）
- 不引入 OpenAPI/Zod schema codegen（規模尚小，先手寫型別對齊）
- 不引入 axios（以內建 `fetch` 為主，薄包 100 行內搞定）
- 不做全站 error boundary（留待下一 change 視情況加）

## Decisions

### 決策 1：fetch 薄包 vs. axios

**選擇：fetch 薄包**。

理由：
- 已無其他 axios 使用者；新增依賴不划算
- `fetch` 於現代瀏覽器與 Vite 測試環境（happy-dom）皆完備
- 薄包維持 100 行內即可：base URL 組合、JSON parse、錯誤包裝、timeout via `AbortController`

```ts
// src/lib/api.ts（概念）
export class ApiError extends Error {
  constructor(public status: number, public body: unknown, msg: string) { super(msg); }
}
export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> { ... }
```

### 決策 2：queryKey 規則

**選擇：以資源名為第一層，以 id / sub-resource 為後續層**。

```
['patients']                          // list
['patients', patientId]               // detail
['patients', patientId, 'labs']       // 預留
```

同一 queryKey 的 `staleTime` 在 service 層封裝時固定（透過 hook 內建），UI 無需關心。

### 決策 3：Patient 型別搬家（以 domain aggregate 為單位拆檔）

**選擇：新增 `frontend/src/types/patient.ts`，將 `Patient` 及其 sample/record 子型別（`PatientSource`、`OpdRecord`、`AaSample`、`MsmsSample`、`BiomarkerSample`、`AadcSample`、`AldSample`、`MmaSample`、`Mps2Sample`、`LsdSample`、`EnzymeSample`、`GagSample`、`DnabankRecord`、`OutbankRecord`、`BdSample`、`TgalSubSample`、`CahSample`、`TshSubSample`、`DmdSample`、`G6pdSample`、`SmaScidSample`）從 `types/medical.ts` 搬出；`types/medical.ts` 以 `export type` re-export 保持向後相容**。

理由：
- 現況：`types/medical.ts` 已經 800+ 行，混雜了三個關注點（Patient 實體、module 設定 `MODULE_DEFINITIONS`/`PRESETS`、filter/condition `MODULE_FIELDS`/`CONDITION_TEMPLATES`）
- 按 domain aggregate root 拆檔是中大型 TS 專案的產業慣例（DDD 影響）；本 change 只拆出 Patient aggregate，module/condition 相關型別留待未來 change 再拆
- 搬家後 `services/`、`hooks/queries/` 等新程式碼 MUST `import type { Patient } from '@/types/patient'`；既有 7 處元件透過 `types/medical.ts` 的 re-export 無痛運作，本 change 內不強制改既有 import
- `data/mockData.ts` 目前只 import 不 export，無需新增 re-export

### 決策 4：是否引入 MSW

**選擇：引入 `msw` 作為 dev dependency 供單元測試與 Storybook-like 開發**。

理由：
- 測 hooks 需要 mock fetch；MSW 與 React Query 生態相容最好
- CI pipeline 已跑 `npm test`，本 change 新增測試可立即被把關
- 開發者可隨時用 MSW handlers 覆蓋後端真實回應做 UI 探索（後續 change 用得上）

代價：多一個 dev dep；若使用者偏好更輕量，改用 `vi.mock('global.fetch')` 亦可（可在 Open Questions 確認）。

### 決策 5：QueryClient 預設值

- `staleTime: 60_000`（patients 資料變動少，一分鐘夠）
- `retry: 1`（後端若短暫抖動給一次機會）
- `refetchOnWindowFocus: false`（內網醫療系統，不需要）
- `gcTime: 5 * 60_000`（預設即可）

可於個別 hook 以 `useQuery({ ..., staleTime })` override。

### 決策 6：env 變數與型別擴充

`frontend/.env.development` 設 `VITE_API_BASE_URL=http://localhost:8000`。`vite-env.d.ts`：

```ts
/// <reference types="vite/client" />
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
}
interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

`api.ts` 啟動時讀一次 `import.meta.env.VITE_API_BASE_URL`；若未設，throw 一目了然的錯誤訊息（dev 時立即暴露設定缺失）。

## Risks / Trade-offs

- **風險：env 變數未設 → 執行時 throw**→ **緩解**：提供 `.env.example` + `.env.development` 含預設值；CI 測試注入 `VITE_API_BASE_URL=http://localhost:8000`
- **風險：Patient 型別與後端 Pydantic schema 漂移**→ **緩解**：於 `types/patient.ts` 註明「field names and camelCase MUST match backend.shared.schemas」；後續考慮加 contract test 或 schema codegen
- **風險：MSW 引入拖慢 CI**→ **緩解**：MSW 僅作 dev dep，production bundle 不受影響；CI 測試量目前極小
- **Trade-off**：不做 OpenAPI codegen，短期簡單，長期若 API 變多可能需重新評估

## Migration Plan

本 change 純新增。對既有程式無破壞性。驗收僅需：
1. `npm run typecheck` 綠
2. `npm run test` 綠（新增的 `api.test.ts`、`usePatients.test.tsx`）
3. `npm run dev` 啟動後首頁仍顯示與 mockPatients 相同內容（因尚未接線）
4. 在 React Query Devtools 或暫時加一個 `console.log(usePatients().data)` 的隱藏 div 驗證 hook 能拿到 gateway 資料（驗證完移除）

Rollback：revert PR 即可。

## Open Questions

- 是否引入 MSW 測試？或改用更輕量的 `vi.fn()` mock？— 預設採 MSW，若使用者偏好精簡可討論
- `ApiError` 是否加 `code` 欄位對應後端 `{"error": "patient_not_found"}`？— 建議加（Pydantic 後端已固定 error body 形狀）
