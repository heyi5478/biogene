## Why

前端目前透過相對路徑 `import` 後端 mock-data JSON 檔作為資料來源，無任何 HTTP API 可供整合。依 `backend/PLAN.md`，目標架構為四個 FastAPI 微服務（gateway + svc-patient + svc-lab + svc-disease），本次變更建立這個骨架並以既有 mock-data JSON 作為第一階段資料來源，讓後續「前端改打 HTTP」與「日後接 MySQL」兩條路都有落腳點。

## What Changes

- 於 `backend/` 建立四個 FastAPI 服務，各以獨立 process 啟動：
  - `gateway` @ port 8000：對前端暴露的唯一入口，負責 CORS、aggregate、將請求 fan-out 至下游 svc-*
  - `svc-patient` @ port 8001：患者基本資料（讀 `db_main/patient.json` + `db_external/patient.json` + `db_nbs/patient.json`）
  - `svc-lab` @ port 8002：一般檢驗資料（aa / msms / biomarker）
  - `svc-disease` @ port 8003：疾病模組資料（aadc、ald、mma、mps2、lsd、enzyme、gag、bd、cah(+tgal)、dmd(+tsh)、g6pd、sma_scid）
- 共用 `backend/shared/` 模組收納：
  - `schemas.py`：Pydantic 模型，欄位對齊前端 `Patient` 型別
  - `data_loader.py`：薄包 `backend/scripts/load_mock.py` 提供的 `load_all()` 與 `validate()`，啟動時執行 FK 驗證
- Gateway 端點（第一波）：
  - `GET /healthz`
  - `GET /patients`：aggregate 所有患者 bundle（含 labs + diseases 子陣列），回傳結構與前端現行 `Patient[]` 相容
  - `GET /patients/{patientId}`：單筆 aggregate
- 各 svc-* 端點（內部，不對前端公開）：
  - svc-patient：`GET /patients`、`GET /patients/{id}`
  - svc-lab：`GET /labs/{patientId}`
  - svc-disease：`GET /diseases/{patientId}`
- CORS 放行 Vite dev origin（`http://localhost:5173`）於 gateway
- 每服務獨立 `pyproject.toml`，以 FastAPI + Uvicorn + httpx 為基礎；共用模組安裝為 editable local package
- `backend/README.md` 新增啟動說明（四個 terminal / 或 `uvicorn` 並行腳本）

## Capabilities

### New Capabilities

- `backend-api`: 對外公開的 HTTP API 入口（gateway）與四微服務拓樸，規範服務切分、aggregate 策略、資料來源（JSON → 未來 MySQL）、CORS、健康檢查、錯誤模型

### Modified Capabilities

- `mock-data-layer`: 新增「`load_mock.py` 須提供 `load_all()` 與 `validate()` 穩定介面，供 FastAPI 服務啟動時呼叫」之要求；原 CLI 行為不變

## Impact

- **新增程式碼**：`backend/gateway/`、`backend/svc-patient/`、`backend/svc-lab/`、`backend/svc-disease/`、`backend/shared/`、各自 `pyproject.toml`、`backend/README.md`
- **相依性**：新增 FastAPI、Uvicorn、httpx、Pydantic v2；本地 editable install `backend/shared`
- **不動**：前端程式碼完全不變（本 change 範圍內）；`backend/scripts/load_mock.py`、`generate_mock.py`、`mock-data/*.json` 只讀不改
- **下游 change**：解鎖 `add-frontend-api-client-layer`（前端 API client 層）與 `wire-index-page-to-api`（前端實際切換）
- **風險**：四服務並行 port 衝突、JSON 檔啟動 I/O 成本；記憶體預算 1 GB（PLAN.md）下需確認每服務 single worker 約 60–70 MB
