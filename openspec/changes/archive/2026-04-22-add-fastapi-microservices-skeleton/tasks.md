## 1. Backend workspace setup

- [x] 1.1 建立目錄骨架：`backend/{shared,gateway,svc-patient,svc-lab,svc-disease}/`
- [x] 1.2 各服務建立 `pyproject.toml`（FastAPI、Uvicorn、httpx、Pydantic v2），`shared` 同樣為可 editable-install 的 package
- [x] 1.3 新增 `backend/README.md`：列出四服務 port 與啟動指令
- [x] 1.4 新增 `backend/scripts/dev.sh`（或 `Makefile`）：一鍵並行啟動四服務
- [x] 1.5 於 repo root 更新 `.gitignore`：忽略各服務的 `.venv/`、`__pycache__/`、`*.egg-info/`

## 2. Shared 模組

- [x] 2.1 `backend/shared/data_loader.py`：薄包 `backend/scripts/load_mock.py`，re-export `load_all`、`validate`
- [x] 2.2 `backend/shared/schemas.py`：定義 `Patient`、各 module Record、`PatientBundle`（欄位 camelCase，對齊 mock JSON）
- [x] 2.3 確認 `scripts/load_mock.py` 的 `load_all()` / `validate()` 簽章穩定；必要時補 type hints 與 module-level docstring
- [x] 2.4 於 `shared` 內加 `conftest.py` 或最小 smoke test 驗證 `load_all()` 回傳結構

## 3. svc-patient（port 8001）

- [x] 3.1 `backend/svc-patient/app.py`：FastAPI app，`lifespan` 內呼叫 `validate()` 與 `load_all()`，將三庫 `patient.json` 合併為記憶體快取
- [x] 3.2 實作 `GET /patients`：回傳合併後全量 `Patient[]`（含 `source` 欄位）
- [x] 3.3 實作 `GET /patients/{patientId}`：查無則 404，body `{"error": "patient_not_found", ...}`
- [x] 3.4 實作 `GET /healthz`
- [x] 3.5 手動驗證：`uvicorn svc_patient.app:app --port 8001` 啟動後 `curl` 三端點

## 4. svc-lab（port 8002）

- [x] 4.1 `backend/svc-lab/app.py`：lifespan 載入 `{aa, msms, biomarker, outbank, dnabank}` 於三庫的 JSON，建立 `patientId -> rows` 索引
- [x] 4.2 實作 `GET /labs/{patientId}`：回傳 `{"aa": [...], "msms": [...], "biomarker": [...], "outbank": [...], "dnabank": [...]}`
- [x] 4.3 實作 `GET /healthz`
- [x] 4.4 手動驗證：`curl http://localhost:8002/labs/{某 uuid}` 回傳正確陣列

## 5. svc-disease（port 8003）

- [x] 5.1 `backend/svc-disease/app.py`：lifespan 載入 `db_main/{aadc,ald,mma,mps2,lsd,enzyme,gag}` + `db_nbs/{bd,cah,cah_tgal,dmd,dmd_tsh,g6pd,sma_scid}`
- [x] 5.2 建 `patientId -> module rows` 索引；NBS 子表 `cah_tgal` 於記憶體依 `cahId` join 回 `cah`，`dmd_tsh` 依 `dmdId` join 回 `dmd`
- [x] 5.3 實作 `GET /diseases/{patientId}`：回傳物件，每 module 一 key（NBS 子表作為父 module row 內的巢狀陣列或 sibling 陣列皆可，須與 shared schema 一致）
- [x] 5.4 實作 `GET /healthz`
- [x] 5.5 手動驗證

## 6. Gateway（port 8000）

- [x] 6.1 `backend/gateway/app.py`：FastAPI app，lifespan 建立共用 `httpx.AsyncClient`（timeout=5s），呼叫 `validate()` 啟動前檢查
- [x] 6.2 註冊 `CORSMiddleware`：`allow_origins=["http://localhost:5173"]`、常用 methods、`allow_headers=["*"]`
- [x] 6.3 實作 `GET /patients`：`asyncio.gather` 並行呼叫 svc-patient `/patients` → 再針對每位患者並行 `svc-lab/labs/{id}` 與 `svc-disease/diseases/{id}`（或 bulk 端點若第 7 階段有加）；merge 為 `PatientBundle[]`
- [x] 6.4 實作 `GET /patients/{patientId}`：呼叫 svc-patient 單筆，404 直接回傳；200 時再並行取 labs/diseases 並 merge
- [x] 6.5 任一下游 5xx 或連線錯誤 → 回 502，body `{"error": "upstream_unavailable", "service": "<name>"}`；**不得**回傳 partial bundle
- [x] 6.6 實作 `GET /healthz`
- [x] 6.7 手動驗證：gateway 單獨啟動、四服務全啟動兩種情境

## 7. 效能/可選最佳化

- [x] 7.1 svc-lab 與 svc-disease 新增 bulk 端點 `POST /labs/batch`、`POST /diseases/batch`（body: `{"patientIds": [...]}`）供 gateway `/patients` 全量 aggregate 使用，避免 N 次 HTTP 呼叫
- [x] 7.2 gateway `GET /patients` 改用 bulk 端點

## 8. 整合驗證與文件

- [x] 8.1 `backend/README.md` 補完四服務啟動說明 + `curl` 範例
- [x] 8.2 `curl http://localhost:8000/patients | jq 'length'` 等於 mock 患者總數
- [x] 8.3 `curl http://localhost:8000/patients/{某個 uuid} | jq '.aa | length'` 回傳該患者的 aa 記錄數，與 `db_main/aa.json` 中同 patientId 筆數一致
- [x] 8.4 故意在 `mock-data/` 植入 FK 錯誤，確認各服務啟動 exit 非零且有日誌；驗證後還原
- [x] 8.5 關掉 svc-lab 後 `curl http://localhost:8000/patients` 回 502，body 正確標示 `service=svc-lab`
- [x] 8.6 `openspec validate add-fastapi-microservices-skeleton --strict` 通過
