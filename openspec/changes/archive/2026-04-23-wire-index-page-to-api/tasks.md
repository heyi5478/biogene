## 1. 前置確認

- [x] 1.1 確認 `add-fastapi-microservices-skeleton` 已合入 `main`；於本機 `backend/scripts/dev.sh` 啟動四服務，`curl http://localhost:8000/patients` 正常回傳
- [x] 1.2 確認 `add-frontend-api-client-layer` 已合入；`npm run typecheck` 綠，`usePatients` / `usePatient` 已存在

## 2. Index.tsx 切換資料源

- [x] 2.1 移除 `frontend/src/pages/Index.tsx:13` 的 `import { mockPatients } from '@/data/mockData'`
- [x] 2.2 加入 `const { data: patients, isLoading, isError, error, refetch } = usePatients();`
- [x] 2.3 將所有既有使用 `mockPatients` 的地方（包含 `Index.tsx:67`、向 `ConditionResults` 傳遞 props 的位置）改為 `patients ?? []`
- [x] 2.4 加 loading UI：`isLoading && !patients` 時渲染 5 行 `<Skeleton>`
- [x] 2.5 加 error UI：`isError` 時以 `<Alert>` 顯示 `error.message`，附「重試」按鈕呼叫 `refetch()`
- [x] 2.6 保留既有「查無患者」空狀態，條件調整為 `!isLoading && !isError && patients.length === 0`

## 3. ConditionResults.tsx

- [x] 3.1 檢查 `ConditionResults` props 介面，確認已接收 `patients: Patient[]`；若未接受則調整 props
- [x] 3.2 不改 `evaluateConditions` 函式本身
- [x] 3.3 Index 呼叫 `ConditionResults` 的位置改傳 `patients ?? []`

## 4. 退役 mockData runtime 匯出

- [x] 4.1 `grep -r "from ['\"]@/data/mockData['\"]" frontend/src` 盤點所有 import
- [x] 4.2 若僅剩型別 import：移除 `frontend/src/data/mockData.ts` 的 runtime 匯出與 JSON import，保留 `export type { Patient } from '@/types/patient'`；或整檔刪除並修正少數 import 路徑
- [x] 4.3 若仍有 runtime 消費者，修改它們改用 `usePatients` / `usePatient`
- [x] 4.4 `npm run typecheck`、`npm run lint` 綠
- [x] 4.5 `npm run build` 綠，確認 bundle 已不含 `backend/mock-data/**` JSON

## 5. Playwright E2E 調整

- [x] 5.1 盤點 `frontend/tests/**` 中是否有測試直接 import `mockPatients` 或依賴「0ms 渲染完成」的時序
- [x] 5.2 若有，改為等待語意選擇器（`getByRole`、`getByText`）；**不**使用 `waitForTimeout` 硬 sleep
- [x] 5.3 依 Open Questions 擇定方案（A/B/C）實作：
  - 方案 A：於 `.github/workflows/ci.yml` e2e job 加「啟動後端四服務」步驟並 `wait-on http://localhost:8000/healthz`
  - 方案 B：於 `frontend/src/test/handlers.ts` 新增 MSW handler；E2E 以 `.env.test` 導向 `http://localhost:xxxx` by MSW
  - 方案 C：E2E 測試先 `test.skip`，另開 change 補上
- [x] 5.4 本機執行 `npm run e2e` 綠

## 6. 驗收與文件

- [x] 6.1 手動：後端啟動 → `npm run dev` → 首頁顯示患者 → 搜尋「陳志明」或「A1234567」→ 條件過濾「Biomarker 異常」，結果與合入前一致
- [x] 6.2 手動：關掉 gateway（`svc-lab` / `svc-disease` / `svc-patient` 任一皆可）→ 首頁呈現 error alert 與重試按鈕 → 重啟後端 → 點重試 → 資料恢復
- [x] 6.3 手動：在 Network tab 確認只打 gateway（`http://localhost:8000`），未直接打 8001/8002/8003
- [x] 6.4 更新 `frontend/README.md`（或 root `README.md`）：載明「本地開發需先啟動 `backend/scripts/dev.sh`」
- [x] 6.5 `openspec validate wire-index-page-to-api --strict` 通過
- [x] 6.6 CI：PR 觸發後六個 job（lint / format / typecheck / test / build / e2e）全綠

## 7. 最終清理

- [x] 7.1 移除步驟 2–3 開發過程中可能遺留的 `console.log`
- [x] 7.2 確認 `frontend/src/data/mockData.ts` 若仍存在，檔案內容僅為 `export type` re-export 與必要註解
- [x] 7.3 Commit 歷史整理為 1–3 個邏輯清楚的 commit
