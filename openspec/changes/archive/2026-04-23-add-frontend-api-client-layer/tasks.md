## 1. 環境變數與型別

- [x] 1.1 新增 `frontend/.env.development`：`VITE_API_BASE_URL=http://localhost:8000`
- [x] 1.2 新增 `frontend/.env.example`：同上，附註說明
- [x] 1.3 `frontend/.gitignore` 確認忽略 `.env.local`、`.env.*.local`，但保留 `.env.development`、`.env.example` 版控
- [x] 1.4 `frontend/src/vite-env.d.ts` 擴充 `ImportMetaEnv`，加入 `readonly VITE_API_BASE_URL: string`

## 2. 型別搬家

- [x] 2.1 新增 `frontend/src/types/patient.ts`，將 `Patient` 及其 sample/record 子型別（`PatientSource`、`OpdRecord`、`AaSample`、`MsmsSample`、`BiomarkerSample`、`AadcSample`、`AldSample`、`MmaSample`、`Mps2Sample`、`LsdSample`、`EnzymeSample`、`GagSample`、`DnabankRecord`、`OutbankRecord`、`BdSample`、`TgalSubSample`、`CahSample`、`TshSubSample`、`DmdSample`、`G6pdSample`、`SmaScidSample`）從 `frontend/src/types/medical.ts` 搬過去
- [x] 2.2 於 `frontend/src/types/medical.ts` 用 `export type { Patient, ... } from '@/types/patient'` re-export 所有搬出去的型別，保持既有 7 處元件 import 不動
- [x] 2.3 `npm run typecheck` 綠

## 3. HTTP client（src/lib/api.ts）

- [x] 3.1 實作 `ApiError` class：`status`、`code?`、`body`、`message`
- [x] 3.2 實作 `apiGet<T>`：base URL 組合、JSON parse、非 2xx 丟 `ApiError`、network error 丟 `ApiError(status=0)`
- [x] 3.3 首次呼叫時檢查 `import.meta.env.VITE_API_BASE_URL` 存在，否則 throw 可診斷訊息
- [x] 3.4 單元測試 `src/lib/api.test.ts`：成功 200、4xx error shape、network error（用 MSW 或 `vi.fn()` 依決策）

## 4. Service 層（src/services/patients.ts）

- [x] 4.1 實作 `fetchPatients(): Promise<Patient[]>`
- [x] 4.2 實作 `fetchPatient(patientId: string): Promise<Patient>`
- [x] 4.3 單元測試：mock gateway `/patients`、`/patients/{id}`，驗證回傳型別與 404 錯誤傳遞

## 5. Query key helper（src/hooks/queries/keys.ts）

- [x] 5.1 匯出 `queryKeys.patients.all = ['patients'] as const`
- [x] 5.2 匯出 `queryKeys.patients.detail(id: string) = ['patients', id] as const`
- [x] 5.3 匯出 `queryKeys.patients.subResource(id, name) = ['patients', id, name] as const`

## 6. React Query hooks

- [x] 6.1 `src/hooks/queries/usePatients.ts`：使用 `queryKeys.patients.all` 與 `fetchPatients`
- [x] 6.2 `src/hooks/queries/usePatient.ts`：`enabled: Boolean(patientId)`、key `queryKeys.patients.detail(id!)`
- [x] 6.3 單元測試 `usePatients.test.tsx`：用 `@testing-library/react` + `QueryClientProvider` 驗證 loading → success 流，以及 queryKey 正確
- [x] 6.4 單元測試：`usePatient(undefined)` 不觸發 fetch

## 7. QueryClient 預設

- [x] 7.1 在 `frontend/src/App.tsx` 將 `new QueryClient()` 改為 `new QueryClient({ defaultOptions: { queries: { staleTime: 60_000, retry: 1, refetchOnWindowFocus: false } } })`
- [ ] 7.2 手動驗證：Index 頁面仍顯示 mockPatients（本 change 不改 UI）— 需本機開 dev server 驗證，未在此環境執行

## 8. 測試工具（視決策）

- [x] 8.1 如決策採 MSW，`npm i -D msw`，加 `src/test/handlers.ts` 與 `src/test/setup.ts`（若現有 vitest config 需調整）
- [x] 8.2 `npm run test` 綠

## 9. 文件與驗證

- [x] 9.1 於 `frontend/README.md`（若無則新增）寫明：後端必須於 `VITE_API_BASE_URL` 可達；如何啟動前後端
- [ ] 9.2 手動測試：後端四服務啟動後，暫時在某元件加 `const { data } = usePatients(); console.log(data);`，確認瀏覽器拿到 gateway 資料；驗證後移除 — 需 live backend+瀏覽器，未在此環境執行
- [x] 9.3 `npm run typecheck`、`npm run lint`、`npm run test`、`npm run build` 全綠
- [x] 9.4 `openspec validate add-frontend-api-client-layer --strict` 通過
