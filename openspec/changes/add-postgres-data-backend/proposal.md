## Why

my-project 是「基因醫學整合查詢中心」3.0 版的全新實作。1.0（ASP.NET + Access + SQL Server `DBGEN`）與 2.0（MySQL 三庫架構）今天都還跑著真實資料，並且會在 3.0 上線後退役。3.0 目前只跑 mock JSON，沒有真實資料庫後端，也尚未一次性匯入 1.0 + 2.0 累積的歷史資料 — 在這之前 3.0 沒有東西可查，切換也無法發生。本 change 就是要建好這個後端、吸收兩個舊系統的資料，讓 3.0 成為單一查詢中心。

## What Changes

- 建立單一 PostgreSQL 16 資料庫 `gimc`，內含五個 schema：`main`、`external`、`nbs`、`links`、`ref`（UTF8、ICU collation 以支援中文排序）。
- 為五個 schema 中的每張表建立 SQLAlchemy 2.0 declarative model，依 schema 各自一個 Python 模組。
- 加入 Alembic，啟用 `include_schemas=True`，`alembic_version` 表放在 `public`，由單一遷移歷史管理五個 schema。
- 新增 `postgres-data-backend` capability，定義：schema 拓撲、`patient_id` UUID v5 規則（`uuid5(NAMESPACE_OID, "{source}:{naturalKey}")`，與既有 mock-data spec 一致）、透過 `links.patient_link` 做的跨 schema 連結、NBS 子表用獨立資料表（不用 JSONB）、條件查詢熱欄位上的 partial index（`dbsLysoGb3`、`ohp17`、`leu`、`tsh` …）。
- 把 `backend/shared/shared/data_loader.py` 改成由環境變數 `GIMC_DATA_BACKEND` ∈ {`json`, `postgres`} 決定的雙後端 facade；兩種後端回傳同樣的 `dict[schema][table][rows]` 形狀，四個 FastAPI service 不需動程式碼。
- 在 `backend/etl/` 新增一條一次性 ETL 流水線：
  - **2.0 → 3.0**：用 `pgloader` 跑三次（main / external / nbs），接著 `post_pgloader.sql` 處理 UUID 型別轉換、partial index、`BEFORE UPDATE` trigger。
  - **1.0（`gene.mdb`，Access）→ 3.0**：`mdbtools` 抽取 → CSV → Pydantic 驗證 → `psycopg COPY` / `ON CONFLICT (patient_id) DO UPDATE` upsert。同樣的 `chartno` UUID seed 規則會自動讓 1.0 兩張病人表去重，並與 2.0 紀錄合併。
  - **1.0（`DBGEN`，ta-server 的 SQL Server）→ 3.0**：用 pgloader MSSQL 來源，或 `pyodbc → psycopg`（MVP-3，待確認 DBGEN 內容與網路可達性後動工）。
  - BLOB 欄位（`MSDATA.DATA`、`GCDATA.pic`、`MPSUDATA.pic`、`ENZYME.pic`）落到檔案系統 `/srv/gimc/blobs/...`；資料庫只存 `raw_data_path`。
  - 為吸收 1.0 獨有資料而新增的 schema 元件：新增 `GcmsRecord` schema 與 `main.gcms` 表存 `GCDATA`；加寬 `main.gag` 欄位（`od`、`urine_creatinine`、`mggag`、`twos`、`twos_cre`）以收下完整的 `MPSUDATA` panel。
  - 1.0 的參考表 — `AAM` / `MSM` / `DNAITEM` / `ENZYMEITEM` / `COMMAND` — 在 MVP-2 載入 `ref` schema。
- 新增 `backend/etl/verify.py`，涵蓋：row-count parity、FK 完整性（跨 schema `LEFT JOIN ... IS NULL`）、五個 anchor chartno（`A1234567` ~ `E5678901`）的 patient identity round-trip、`dbsLysoGb3 > 5` 模板的 mock-parity 回歸、跨 schema link 對稱性、效能 baseline（`SELECT * FROM aa WHERE leu > 200 LIMIT 100` < 200 ms）。
- 明確不在範圍內：MOH 申報表單 `G0001/G0016/G0017` 留在 1.0；不做即時 federation 或雙向同步；`users` / `operator` / `doctor` / `CELLDATA` / `opd_tmp` / `disease_count` 不搬。
- **BREAKING**（僅在部署層）：把 `GIMC_DATA_BACKEND` 設成 `postgres` 需要先把資料庫灌好；JSON 模式仍是開發/測試的預設。Service 的 Python 程式碼不變。

## Capabilities

### New Capabilities
- `postgres-data-backend`：PostgreSQL `gimc` 資料庫 — schema 拓撲（`main` / `external` / `nbs` / `links` / `ref`）、與既有 Pydantic record types 對齊的資料表契約、套用到 DB row 的 `patient_id` UUID 規則、跨 schema 連結、條件查詢用的 partial index，以及證明 DB 模式答案與 JSON 模式答案一致的驗證契約。
- `legacy-data-etl`：一次性匯入 2.0（MySQL）與 1.0（Access `gene.mdb` + SQL Server `DBGEN`）到 `gimc` 的流水線；用確定性 UUID 去重病人、把 BLOB 落到檔案系統、產出 verify 報告。生命週期到 MVP-3 切換完成後結束。

### Modified Capabilities
- `mock-data-layer`：`backend/shared/shared/data_loader.py` 多了一個後端切換器（`GIMC_DATA_BACKEND` env var）。既有 JSON 相關 requirement 完全不變；新增一條 requirement，要求當 env var 為 `postgres` 時，`load_all()` 與 `validate()` 必須能正確對 PostgreSQL 運作，且回傳形狀位元等價。

## Impact

- **新增程式碼**：`backend/shared/shared/db.py`、`backend/shared/shared/models/{main,external,nbs,links,ref}/`、`backend/alembic/`、`backend/etl/`（pgloader 設定、mdbtools wrapper、transform/load/verify 腳本）、`backend/scripts/seed_from_json.py`。
- **修改程式碼**：`backend/shared/shared/data_loader.py`（加 PG 後端）、`backend/shared/shared/schemas.py`（加 `GcmsRecord`、加寬 `GagRecord`）。
- **不動的程式碼**：`gateway`、`svc-patient`、`svc-lab`、`svc-disease` — 都消費 `data_loader` facade，與後端無關。`backend/scripts/load_mock.py` 在 JSON 開發模式下繼續使用，其 FK 驗證邏輯被移植到 `etl/verify.py`。
- **新增 runtime 依賴**：PostgreSQL 16 server、`asyncpg`、`sqlalchemy[asyncio]`、`alembic`、`psycopg[binary]`、`pgloader`（建置/ETL 機器）、`mdbtools`（建置/ETL 機器）；MVP-3 再選擇加上 `pyodbc` + MSSQL ODBC driver。
- **基礎設施**：一台 PostgreSQL instance（一個 DB、五個 schema）；檔案系統 `/srv/gimc/blobs/{msms,gcms,enzyme,mpsu}/` 存 BLOB；`.env` 加上 `DATABASE_URL=postgresql+asyncpg://...` 與 `GIMC_DATA_BACKEND`。
- **運維**：每個 service 的連線 pool 設 5 + 10 overflow（4 service × 15 = 60，仍小於 PostgreSQL 預設 `max_connections=100`）；備份用 `pg_dump --schema=...` 切片。
- **風險**：pgloader 在 `utf8mb4 → UTF8`、`DECIMAL → NUMERIC`、`TINYINT(1) → BOOLEAN`、`CHAR(36) → UUID` 的邊界情況；由 `post_pgloader.sql` 與 verify §1–§3 緩解。
