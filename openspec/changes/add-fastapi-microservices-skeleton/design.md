## Context

`backend/` 目前只有 mock-data JSON 檔與純標準庫腳本（`scripts/load_mock.py`、`scripts/generate_mock.py`），尚無任何 HTTP 服務。前端 `frontend/src/data/mockData.ts` 直接以相對路徑 `import` 後端 JSON（Vite JSON import），跳過了網路層。

`backend/PLAN.md` 已定義目標架構：四個 FastAPI 微服務，部署於單機，總記憶體預算 1 GB，對應三個邏輯資料庫（未來由 SQLAlchemy 連到外部 MySQL）。當前階段資料尚未進 MySQL，且 mock-data 的 schema 已對齊目標 DB（參見已存檔的 `restructure-mockdata-for-db-alignment`）。

關鍵限制：
- 不可改動 `mock-data/*.json` 與 `scripts/generate_mock.py`（schema 已鎖定）
- `scripts/load_mock.py` 現為 CLI + 純函式雙用；本 change 需讓它提供穩定 Python API 供 FastAPI `startup` 呼叫
- 前端 `Patient` 型別（`frontend/src/data/mockData.ts`）定義了 API response 的實質契約，回應形狀需與其相容

## Goals / Non-Goals

**Goals**
- 四個 FastAPI 服務可獨立以 `uvicorn` 啟動
- Gateway 暴露 `GET /patients` 與 `GET /patients/{patientId}` aggregate 端點，回傳形狀與前端 `Patient` 型別相容
- Gateway 啟動時呼叫 `load_mock.validate()`，FK 失敗即退出
- CORS 放行 Vite dev origin
- 建立 `shared` 模組供三 svc-* 重用 Pydantic schemas 與 data loader
- 每服務 single worker 記憶體 ≤ 100 MB

**Non-Goals**
- 不連 MySQL、不引入 SQLAlchemy（留待後續 change）
- 不做寫入端點（POST/PUT/DELETE）；前端目前也無此需求
- 不做驗證/授權（內網開發用）
- 不做前端接線（屬 `add-frontend-api-client-layer` 與 `wire-index-page-to-api`）
- 不做 Docker / 部署自動化
- 不做生產級錯誤回報、rate limit、metrics

## Decisions

### 決策 1：四服務 vs. 單 FastAPI app

**選擇：四服務微架構**（使用者明確指定）。

理由：直接貼合 `PLAN.md` 最終形狀，避免未來拆分成本；每服務職責單純，日後各自接不同 MySQL database 時邊界已切好。

代價：初期 boilerplate 較多（4 個 `pyproject.toml`、4 個 `uvicorn` process），開發啟動較麻煩。以 `backend/scripts/dev.sh`（或 `Makefile`）一鍵啟動緩解。

### 決策 2：Gateway aggregate 放哪裡

**選擇：Gateway 端 aggregate**（非前端 fan-out）。

Gateway 收到 `GET /patients` 後，用 `httpx.AsyncClient` 並行呼叫 svc-patient / svc-lab / svc-disease，於 gateway 端合併成 `Patient[]` bundle。

理由：
- 前端只需打一個端點，後續換 MySQL 時前端無感
- 並行 I/O 在 gateway 容易控制 timeout / 錯誤邊界
- 未來可在 gateway 加快取層

代價：gateway 成為聚合熱點，需注意記憶體（全量載入時）。目前 5 位患者資料極小，無虞。

### 決策 3：資料來源層

**選擇：以 `backend/scripts/load_mock.py` 為唯一入口**，於 `backend/shared/data_loader.py` 薄包 `load_all()`、`validate()`。

各 svc-* 於 `FastAPI.lifespan` 讀一次 JSON 放記憶體快取（dict[str, list[dict]]），用 Pydantic 模型驗證後回應。

理由：避免重複實作 JSON I/O；未來替換成 SQLAlchemy 時只改 `shared/data_loader.py` 與各服務的 query 層。

### 決策 4：服務切分原則

| 服務 | 負責的 mock-data 檔 |
|---|---|
| svc-patient | `{db_main,db_external,db_nbs}/patient.json` |
| svc-lab | `{db_main,db_external,db_nbs}/{aa,msms,biomarker,outbank,dnabank}.json`（共通檢驗） |
| svc-disease | `db_main/{aadc,ald,mma,mps2,lsd,enzyme,gag}.json` + `db_nbs/{bd,cah,cah_tgal,dmd,dmd_tsh,g6pd,sma_scid}.json`（疾病/NBS 模組） |
| gateway | 不擁有資料，只 aggregate |

注意 `opd.json` 存在於三庫但尚無前端消費者，暫由 svc-patient 持有（屬患者就診記錄）。

### 決策 5：Port 與啟動

- gateway 8000、svc-patient 8001、svc-lab 8002、svc-disease 8003（照 PLAN.md）
- 前端 `.env.development` 只需設 `VITE_API_BASE_URL=http://localhost:8000`
- 各服務 `host=127.0.0.1`（內網）；僅 gateway 建議可放 `0.0.0.0` 以便容器化過渡

### 決策 6：Response schema

Pydantic v2；於 `shared/schemas.py` 定義：
- `Patient`（對齊前端同名 type）
- 各 module 子型別（`AaRecord`、`MsmsRecord`、`BiomarkerRecord`、`AadcRecord`、`AldRecord`、`MmaRecord`、`Mps2Record`、`LsdRecord`、`EnzymeRecord`、`GagRecord`、`OutbankRecord`、`DnabankRecord`、`BdRecord`、`CahRecord`、`CahTgalRecord`、`DmdRecord`、`DmdTshRecord`、`G6pdRecord`、`SmaScidRecord`）
- `PatientBundle = Patient` with 上述陣列欄位（gateway aggregate 結果）

欄位命名沿用 mock JSON 的 camelCase（如 `patientId`、`dbsLysoGb3`），以 `model_config = ConfigDict(populate_by_name=True)` 支援；避免 snake_case 轉換造成前端改動。

## Risks / Trade-offs

- **風險：啟動 JSON I/O 重複**（四服務都讀部分 JSON）→ **緩解**：目前檔案極小（KB 級），無需最佳化；日後換 MySQL 此問題消失
- **風險：gateway 並行呼叫下游出錯時 partial response**→ **緩解**：首版採 fail-fast（任一下游錯誤即 502），不做部分降級
- **風險：Pydantic schema 與前端 TS 型別漂移**→ **緩解**：欄位命名完全照抄 mock JSON（亦即前端當前所見形狀）；後續可加 schema contract test
- **風險：httpx 連線池設定不當造成 gateway 延遲**→ **緩解**：用單一 `AsyncClient` lifespan-scoped，timeout=5s
- **風險：CORS 設定過寬**→ **緩解**：僅放行 `http://localhost:5173`（開發）；production origin 待後續 change 補
- **Trade-off**：四服務 boilerplate 多但換 port 8001/8002/8003 各自重啟不影響 gateway；若改為單服務，後續拆分要搬 code，目前接受此 upfront 成本

## Migration Plan

此為新增，無既有服務遷移。

1. 建立目錄、`pyproject.toml`、`shared` 套件
2. svc-patient 先實作並可 curl 通過 → 建立模式
3. svc-lab、svc-disease 依樣建立
4. Gateway aggregate 最後串接
5. `backend/README.md` 寫啟動指令 + `scripts/dev.sh` 並行啟動腳本
6. PR 合入後，`add-frontend-api-client-layer` 可開工

Rollback：整個 `backend/{gateway,svc-*,shared}` 為新目錄，revert PR 即可，不影響 `mock-data/`、`scripts/` 既有檔案。

## Open Questions

- `pyproject.toml` 採 workspace（單一 root）還是 per-service？— 建議 per-service 獨立，shared 以 editable install (`pip install -e ../shared`) 引入，最貼近 PLAN.md 的未來容器化拆分。
- 是否引入 `ruff` / `pytest` 基礎設施？— 建議引入最小 `pytest` 作 smoke test，但不在本 change 強制要求（可由獨立 `add-backend-lint-test-setup` change 處理）。
