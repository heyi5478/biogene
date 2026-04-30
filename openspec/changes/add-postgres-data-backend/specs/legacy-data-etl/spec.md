## ADDED Requirements

### Requirement: ETL SHALL 是 backend/etl/ 之下的一次性匯入流水線

Repo MUST 含有 `backend/etl/` 目錄收容所有匯入相關元件。流水線 MUST 可由單一 orchestrator（`run_etl.py`）執行，先載入 2.0、再載入 1.0；orchestrator 重跑 MUST 是冪等的（透過確定性 UUID upsert，重跑會收斂到同一份 row 集合）。流水線 MUST NOT 接成持續同步 — MUST 對 snapshot 來源採取「按需執行」。

`backend/etl/` MUST 至少包含：

- `pgloader_2_0.load` — 2.0 → 3.0 的 pgloader 設定。
- `extract_mdb.sh` — 用 `mdbtools` 從 1.0 `gene.mdb` 拉表到 CSV 的 wrapper。
- `extract_dbgen.py` — 1.0 `DBGEN` 的 `pyodbc`（或 pgloader MSSQL）wrapper。
- `transform.py` — 套用 1.0 欄名 → 3.0 schema 的欄位級轉換。
- `load_pg.py` — 用 `psycopg COPY FROM STDIN` 配合 `ON CONFLICT (patient_id) DO UPDATE` upsert 的批次載入器。
- `post_pgloader.sql` — 每次 pgloader 後執行的後處理 SQL。
- `verify.py` — 驗證套件（見下方 verification requirement）。
- `run_etl.py` — orchestrator，提供 `--source {2.0|1.0-mdb|1.0-dbgen|all}` 旗標。
- `expected_counts.yaml` — 宣告的 row-count parity 目標。

#### Scenario: 重跑 orchestrator 收斂到同一份 row 集合

- **WHEN** 連續對相同 snapshot 來源執行兩次 `run_etl.py --source all`
- **THEN** 第二次跑完後每張表的 row 數 MUST 等於第一次跑完後的 row 數
- **AND** 每個 `patient_id` MUST 在兩次執行中對到相同 UUID

### Requirement: 2.0 MySQL ETL SHALL 使用 pgloader 與 post_pgloader.sql

遷移 2.0 三個 MySQL 資料庫（`2.0`、`2.0外院資料庫`、`new_born_screening`）MUST 使用 `pgloader`，規則含：

- 重新命名來源 schema 至目標 schema（例如 `ALTER SCHEMA '2.0' RENAME TO 'main'`）。
- 型別轉換：`DATETIME → TIMESTAMPTZ`、`DECIMAL → NUMERIC`、`TINYINT(1) → BOOLEAN`、`DATE → DATE`，並適切處理 null。
- 盡可能保留索引名稱。

每次 pgloader 執行後 `post_pgloader.sql` MUST 執行並：

- 透過 `ALTER TABLE … ALTER COLUMN patient_id TYPE UUID USING patient_id::uuid` 把 `patient_id` 從 `CHAR(36)` 升型為原生 `UUID`。
- 建立 `postgres-data-backend` 要求的 partial index。
- 安裝呼叫 `public.set_updated_at()` 的 `BEFORE UPDATE` trigger。

#### Scenario: pgloader 把 utf8mb4 病人姓名轉換而不發生亂碼

- **WHEN** `pgloader_2_0.load` 遷移 `name` 含中文字元（例如 `陳志明`）的 row
- **THEN** 結果 `main.patient.name` 在以 UTF-8 解碼時 MUST 等於來源位元組
- **AND** PostgreSQL 中的 `length(name)` MUST 等於來源 MySQL 的 `CHAR_LENGTH(name)`

#### Scenario: post_pgloader.sql 把 patient_id 升級為 UUID

- **WHEN** 2.0 → main 的 pgloader 跑完後執行 `post_pgloader.sql`
- **THEN** `\d main.patient` MUST 顯示 `patient_id` 型別為 `uuid`
- **AND** `\d main.aa` MUST 顯示 `patient_id` 型別為 `uuid`
- **AND** 從 `main.aa.patient_id` 指向 `main.patient.patient_id` 的 FK MUST 仍然有效

### Requirement: 1.0 gene.mdb ETL SHALL 透過 mdbtools 抽取，並以確定性 UUID 合併

1.0 Access 資料庫 `gene.mdb` MUST 透過 `mdbtools`（`mdb-tables`、`mdb-export`）逐表抽到 CSV。`transform.py` 接著 MUST：

- 把 1.0 舊欄名（大寫、ASCII）對應到 3.0 schema 欄名（小寫、snake_case）：例如 `AADATA.ALA → main.aa.ala`、`AADATA.LEU → main.aa.leu`。
- 為每筆 patient row 計算 `patient_id = uuid5(NAMESPACE_OID, "main:" + chartno)`（`ptinfo` 與新中文 `patient` 表都以 `chartno` 為 key，因此會碰撞到同一個 UUID 並自然合併）。
- 把 `AADATA.interpretation` 直接對映到 `main.aa.result`。
- 把 1.0 的 `sampleno` 寫進每張 sample 表的 `ntubiogene_sampleno` 欄位（追溯 1.0 的審計軌跡）。

`load_pg.py` MUST 用 `INSERT … ON CONFLICT (patient_id) DO UPDATE SET …` upsert，UPDATE 子句以新 row 的值填補目標的 NULL 欄位、但不覆蓋既有的 non-NULL 值（衝突時 2.0 資料優先；1.0 獨有欄位填入空缺）。

#### Scenario: 1.0 ptinfo 與中文 patient 表合併為單一 row

- **WHEN** `gene.mdb` 同時含有 `ptinfo` row 與中文 `patient` row 共享 `chartno = 'A1234567'`
- **THEN** ETL 結束後 `main.patient` MUST 恰存在一筆 `patient_id = uuid5(NAMESPACE_OID, "main:A1234567")` 的 row
- **AND** 該 row MUST 含有兩來源合併後的資料（例如，若中文表有 `referring_doctor`，則保留）

#### Scenario: 1.0 sample row 透過 ntubiogene_sampleno 可追溯

- **WHEN** `AADATA` 的 `sampleno = '20180312-001'` row 被遷移
- **THEN** 結果 `main.aa` row 的 `ntubiogene_sampleno` MUST 等於 `'20180312-001'`

#### Scenario: 1.0 填補 NULL 欄位但不覆蓋 2.0 值

- **WHEN** 2.0 的 `main.patient` row 為 `diagnosis = 'X'`，對應 1.0 row 為 `diagnosis = NULL` 與 `referring_doctor = 'Dr. Wang'`
- **THEN** 合併後該 row MUST 為 `diagnosis = 'X'`（保留）與 `referring_doctor = 'Dr. Wang'`（補空）

### Requirement: 1.0 BLOB 欄位 SHALL 物化到檔案系統，並由路徑欄位引用

從 `gene.mdb` 抽取期間，BLOB 欄位（`MSDATA.DATA`、`GCDATA.pic`、`MPSUDATA.pic`、`ENZYME.pic`）MUST 個別寫成檔案，置於 `/srv/gimc/blobs/<kind>/<sampleno_or_uuid>.<ext>`。對應的 3.0 row MUST 在 `raw_data_path` 欄位存其絕對路徑。路徑命名 MUST 在重跑時內容穩定，使重跑會就地覆蓋而非產生重複。

#### Scenario: BLOB 抽取在重跑下保持冪等

- **WHEN** 同一筆 1.0 `gene.mdb` ETL 對相同來源 row 跑兩次
- **THEN** 兩次跑完後 `/srv/gimc/blobs/msms/<sampleno>.bin` MUST 恰存在一份
- **AND** 其位元組 MUST 等於來源 BLOB

### Requirement: 1.0 → 3.0 ETL SHALL 為先前未建模的資料新增 schema 元件

ETL MUST 引入下列 3.0 schema 新增物，以吸收 1.0 獨有資料：

- 新 Pydantic record type `GcmsRecord`（在 `backend/shared/shared/schemas.py`）與對應 `main.gcms` 表，存 `GCDATA`（gas chromatography mass spectrometry）紀錄；並在 `svc-lab` 加上對應 route 對外暴露。
- 加寬 `main.gag` 欄位 — `od`、`urine_creatinine`、`mggag`、`twos`、`twos_cre` — 以收下完整的 `MPSUDATA` 尿液 MPS panel，不另開資料表。
- `ref` schema 由 `AAM`、`MSM`、`DNAITEM`、`ENZYMEITEM`、`COMMAND` 灌入（推遲到 MVP-2）。

明確不遷移、不在範圍內的表 MUST 在 `backend/etl/README.md` 列舉：`users`、`operator`、`doctor`、`CELLDATA`、`opd_tmp`、`disease_count`、MOH 申報表 `G0001` / `G0016` / `G0017`。

#### Scenario: GCDATA 遷移到 main.gcms

- **WHEN** ETL 處理 `sampleno = 'GC-2019-007'` 的 `GCDATA` row
- **THEN** `main.gcms` MUST 有對應 row，其 `ntubiogene_sampleno = 'GC-2019-007'`
- **AND** `GcmsRecord` MUST 能用 Pydantic 驗證該 row 的內容無誤

#### Scenario: MPSUDATA panel 灌入加寬後的 gag row

- **WHEN** ETL 處理一筆有 `od`、`urine_creatinine`、`twos` 值的 `MPSUDATA` row
- **THEN** 結果 `main.gag` row 的這三個欄位 MUST 被填上
- **AND** MUST 不另建 `mpsudata` 表

### Requirement: 驗證 SHALL 證明 DB 模式與 mock 模式 parity

`backend/etl/verify.py` MUST 可端到端執行，任一檢查失敗 MUST 以非零狀態結束。MUST 涵蓋：

1. **Row-count parity**：每張表的 row 數 MUST 等於 `expected_counts.yaml` 宣告的數值（由 1.0 + 2.0 來源去重後計算）。
2. **FK 完整性**：對每張 sample 表跑 `LEFT JOIN patient ON patient_id WHERE patient.patient_id IS NULL` MUST 回傳零列；同樣的檢查 MUST 涵蓋 NBS 子表的父子關係。
3. **Patient identity round-trip**：五個 anchor chartno（`A1234567`、`B2345678`、`C3456789`、`D4567890`、`E5678901`）MUST 都存在於 `main.patient`，其 UUID MUST 由 `uuid5(NAMESPACE_OID, "main:" + chartno)` 推得。
4. **Mock-parity 回歸**：儲存型模板 `dbsLysoGb3 > 5` 在 `GIMC_DATA_BACKEND=postgres` 與 `GIMC_DATA_BACKEND=json`（以同樣 mock 資料種子）下，MUST 命中相同的 `patientId` 集合。
5. **跨 schema link 對稱性**：`links.patient_link` 中每筆 row MUST 滿足 `patient_id_a < patient_id_b` 不變式；讀取側實體化 MUST UNION 雙方向。
6. **API smoke**：`curl http://localhost:8000/api/patient-detail/<uuid>` 回傳的 JSON 形狀與鍵集 MUST 與 mock 模式一致。
7. **效能 baseline**：`SELECT * FROM main.aa WHERE leu > 200 LIMIT 100` 在單機 1 GB RAM 開發 instance、mock 等量資料下 MUST 於 < 200 ms 完成。

#### Scenario: verify.py 在 FK 懸空時非零退出

- **WHEN** 故意注入一筆懸空 FK（`main.aa` 某 row 的 `patient_id` 不在 `main.patient` 中）
- **AND** 執行 `python backend/etl/verify.py`
- **THEN** 該腳本 MUST 以非零狀態退出
- **AND** 輸出 MUST 標出冒犯的表、row、`patient_id`

#### Scenario: Mock-parity 回歸跨後端一致

- **WHEN** verify.py 透過 `seed_from_json.py` 將同樣 mock 資料種子灌進兩個後端後執行檢查 4
- **THEN** Postgres 後端命中的 `patientId` 集合 MUST 等於 JSON 後端的命中集合
- **AND** 元素數量 MUST 等於 JSON 模式上次紀錄的命中數

#### Scenario: Anchor chartno round-trip

- **WHEN** verify.py 在 `main.patient` 查詢五個 anchor chartno
- **THEN** `'A1234567'` 的 `patient_id` MUST 等於 `uuid5(NAMESPACE_OID, "main:A1234567")`
- **AND** 對五個 chartno 該等式 MUST 全部成立
