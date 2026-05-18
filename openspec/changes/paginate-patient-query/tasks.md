## 1. Shared schemas（backend/shared）

- [x] 1.1 `backend/shared/shared/schemas.py` 新增 `PatientPage`（`items: list[Patient] = []`、`total: int = 0`、`limit: int = 50`、`offset: int = 0`）
- [x] 1.2 新增 `PatientListPage`（同上，`items: list[PatientListItem] = []`）
- [x] 1.3 `__all__` 補上 `PatientPage`、`PatientListPage`

## 2. svc-patient

- [x] 2.1 `GET /patients` 改為分頁：從 `fastapi` 匯入 `Query`，加 `limit: int = Query(50, ge=1, le=200)`、`offset: int = Query(0, ge=0)`，`response_model=PatientPage`
- [x] 2.2 `list_patients` 內把 `q` 篩選結果存成具名變數 `filtered`，`total = len(filtered)`，回傳 `{"items": filtered[offset:offset+limit], "total": total, "limit": limit, "offset": offset}`（保留原本 name 大小寫敏感、chartno/externalChartno/nbsId 大小寫不敏感的子字串語意）
- [x] 2.3 新增 `POST /patients/batch`：重用既有 `_BatchRequest`，`response_model=dict[str, Patient]`，回傳 `{pid: _patients_by_id[pid] for pid in req.patientIds if pid in _patients_by_id}`

## 3. gateway

- [x] 3.1 `GET /patients` 加 `limit`/`offset` 參數（同 svc-patient 的 `Query` 約束），`response_model=PatientListPage`；下游固定帶 `limit`/`offset`、`q` 僅在非空時帶
- [x] 3.2 對 svc-patient 回傳信封的 `page["items"]`（≤50 筆）呼叫既有 `_fetch_list_items_for_patients`，回傳 `{"items": ..., "total": page["total"], "limit": page["limit"], "offset": page["offset"]}`
- [x] 3.3 `condition-query`：把抓整表的 `GET /patients` 換成 `POST /patients/batch`（帶 `{"patientIds": list(combined)}`），`selected` 由回傳 dict 解析；移除原 `is None` 404 防呆

## 4. 後端測試

- [x] 4.1 `svc-patient/tests/test_search_and_condition.py` 的 `ListPatientsQTest` 各方法改讀 `r.json()["items"]`，並加上 `total`/`limit`/`offset` 斷言
- [x] 4.2 新增 `ListPatientsPagingTest`：`limit`/`offset` 生效、跨頁 `total` 一致、offset 超界回 `[]`、非法參數（`limit=0`/`limit=999`/`offset=-1`）回 422
- [x] 4.3 新增 `backend/svc-patient/tests/test_batch_patients.py`：已知 id → dict、未知 id → 省略、空 `patientIds` → `{}`
- [x] 4.4 `gateway/tests/test_list_patients.py` 各測試改讀 `["items"]`（slim 形狀斷言保留），並加一個 gateway 分頁測試
- [x] 4.5 重跑 `gateway/tests/test_condition_query.py` 確認條件查詢回應形狀不變、5xx→502 仍成立
- [x] 4.6 `cd backend && pytest` 全數通過

## 5. 前端型別與資料層

- [x] 5.1 `frontend/src/types/patient.ts` 新增 `Page<T>`（`items`/`total`/`limit`/`offset`）與 `PatientListPage = Page<PatientListItem>`；`types/medical.ts` re-export 兩者
- [x] 5.2 `frontend/src/services/patients.ts`：新增 `PATIENT_PAGE_SIZE = 50`，`fetchPatients(q: string, page: number)` 帶 `limit`/`offset`（`q` 非空才帶）、回傳 `PatientListPage`
- [x] 5.3 `frontend/src/hooks/queries/keys.ts`：`list(q?, page?)` → `['patients','list', q ?? '', page ?? 1]`
- [x] 5.4 `frontend/src/hooks/queries/usePatients.ts`：`usePatients(q, page)`，`enabled: q !== ''`，`placeholderData: keepPreviousData`，queryKey 用 `list(q, page)`

## 6. 前端 UI

- [x] 6.1 新增 `frontend/src/components/PatientListPager.tsx`：包裝 `components/ui/pagination.tsx`，Prev/Next + 數字頁碼 + 省略號（兩端固定 1 頁、當前頁左右各 1 頁），首尾頁停用 Prev/Next
- [x] 6.2 `frontend/src/pages/Index.tsx`：新增 `page` state；`results = data.items`、`total`、`pageCount`；`handleSearch`/`handleClearAll` 重設 `page=1`；自動選取條件改 `total === 1`；`SearchSummary` 的 `patientCount` 傳 `total`；多頁時於 `PatientList` 下方渲染 `<PatientListPager>`
- [x] 6.3 `frontend/src/components/PatientList.tsx`：新增選用 `total?: number` prop，「找到 N 位病人」顯示 `total ?? patients.length`

## 7. 前端測試

- [x] 7.1 `frontend/src/test/handlers.ts`：預設 `/patients` handler 改回信封 `{ items: [], total: 0, limit: 50, offset: 0 }`
- [x] 7.2 `frontend/src/services/patients.test.ts`：`fetchPatients` 測試改帶 `(q, page)`，斷言 URL 的 `limit`/`offset`、預期信封回傳
- [x] 7.3 `frontend/src/hooks/queries/usePatients.test.tsx`：改以 `usePatients('q', 1)` 測試並讀 `data.items`；新增 `usePatients('', 1)` 維持 `idle`、handler 不被呼叫
- [x] 7.4 新增 `frontend/src/components/PatientListPager.test.tsx`：頁碼/省略號正確、點擊觸發 `onPageChange`、首尾頁停用 Prev/Next
- [x] 7.5 新增 E2E `frontend/tests/patient-search-pagination.spec.ts`（先確認 `frontend/tests/seed.spec.ts` 種子資料是否有 >50 筆命中；不足則加專屬種子或改為驗證小結果集時 pager 不出現）
- [x] 7.6 `cd frontend && npx vitest run` 與 `npx playwright test` 全數通過

## 8. 驗收

- [x] 8.1 `curl 'http://localhost:8001/patients?limit=5&offset=0'` → 回信封、`items` 5 筆、`total` 正確
- [x] 8.2 `curl 'http://localhost:8001/patients?offset=999999999'` → `items: []`、`total` 正確、HTTP 200
- [x] 8.3 `curl -X POST http://localhost:8001/patients/batch -H 'content-type: application/json' -d '{"patientIds":["<已知id>","missing"]}'` → 只含已知 id
- [x] 8.4 `curl 'http://localhost:8000/patients?q=王&limit=50&offset=0'` → slim 信封、回應遠低於 5 秒（502 消失）
- [x] 8.5 瀏覽器：搜尋前 Network 無 `GET /patients`；搜尋寬鬆字 → ≤50 筆 + pager；「命中 N 位病人」為總數；翻頁、唯一姓名自動進詳情、新搜尋重設第 1 頁皆正常
- [ ] 8.6 （部署到 stage 後）用 chrome-devtools MCP 在 http://10.19.209.19/ 重現模糊搜尋「王」，確認 502 已解除
- [x] 8.7 `openspec validate paginate-patient-query --strict` 通過
