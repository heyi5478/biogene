# postgres-data-backend Specification

## Purpose

This capability defines the gimc PostgreSQL 16 backend that hosts the integrated 3.0 query center data. It specifies the single-database / five-schema topology (`main`, `external`, `nbs`, `links`, `ref`) under UTF8 + ICU collation, the native UUID rules for `patient_id` (deterministic `uuid5(NAMESPACE_OID, "{source}:{naturalKey}")` shared with `mock-data-layer`), the standardized `links.patient_link` junction for cross-schema patient relationships, NBS sub-table modelling via real tables with cascading FKs (no JSONB), partial indexes on hot condition-template columns, the shared `BEFORE UPDATE` trigger that auto-maintains `updated_at`, the Alembic-with-`include_schemas=True` migration root, the `GIMC_DATA_BACKEND` env switch in `data_loader` that lets the four FastAPI services run unchanged against either JSON or Postgres, and the BLOB-on-filesystem contract under `/srv/gimc/blobs/` with DB rows holding only `raw_data_path`.

## Requirements

### Requirement: gimc 資料庫 SHALL 是單一 PostgreSQL 16 instance，包含五個 schema

系統 SHALL 部署唯一一個名為 `gimc` 的 PostgreSQL 16 資料庫，使用 `ENCODING UTF8` 與適合中文排序的 ICU collation（`und-x-icu` 或 `zh-x-icu`）。資料庫 MUST 包含以下且僅以下 schema，且任何應用資料 MUST NOT 存放在 `public`：

- `main` — 對應舊 2.0 的 `2.0`（台大本院檢驗）。
- `external` — 對應舊 2.0 的 `2.0外院資料庫`（外院送檢）。
- `nbs` — 對應舊 2.0 的 `new_born_screening`。
- `links` — 由 3.0 引入的跨 schema 關係 junction 表。
- `ref` — 由 1.0 帶入的參考/查詢資料（`AAM`、`MSM`、`DNAITEM`、`ENZYMEITEM`、`COMMAND`）。

跨 schema join MUST 以完整限定的引用方式表達（例如 `SELECT … FROM main.patient JOIN external.patient …`）；不得使用 foreign data wrapper 或跨資料庫查詢。

#### Scenario: 透過 catalog 可觀察到資料庫拓撲

- **WHEN** 操作員對 `gimc` 執行 `\dn`
- **THEN** 列出的 schema MUST 恰為 `main`、`external`、`nbs`、`links`、`ref`，再加上 PostgreSQL 內建 schema（`public`、`information_schema`、`pg_catalog`）
- **AND** `public` 中 MUST NOT 出現任何應用層資料表

#### Scenario: 跨 schema 查詢 join main 與 external 病人

- **WHEN** 查詢執行 `SELECT … FROM main.patient m JOIN external.patient e ON m.chartno = e.external_chartno`
- **THEN** Planner MUST 不需要 foreign data wrapper 即可解析兩個關聯
- **AND** 結果 MUST 在單一 transaction 內回傳

### Requirement: patient_id SHALL 是原生 UUID 型別欄位，且跨版本由確定性規則生成

`main`、`external`、`nbs` 中每張 `patient` 表 MUST 以原生 PostgreSQL `UUID` 型別（不可為 `CHAR(36)` 或 `TEXT`）的 `patient_id` 欄位作為主鍵。其值 MUST 等於 `uuid5(NAMESPACE_OID, f"{source}:{naturalKey}")`，其中 `source ∈ {"main", "external", "nbs"}`，`naturalKey` 為 `chartno`（main）、`external_chartno`（external）或 `nbs_id`（nbs）。Seed 規則 MUST 與 `mock-data-layer` 的規則一致，使 mock 模式與 DB 模式產生的 UUID 位元相等。

每張包含病人單筆樣本資料的非 `patient` 表 MUST 包含 `patient_id UUID NOT NULL` 欄位，並以外鍵指向同一 schema 中的 `patient(patient_id)`。

#### Scenario: Anchor chartno 對到正規 UUID

- **WHEN** 從 `main.patient` 讀出 `chartno = 'A1234567'` 的 row
- **THEN** 其 `patient_id` MUST 等於 `uuid5(NAMESPACE_OID, "main:A1234567")`（即 `4e645243-fe58-5f74-b0bf-4271b5fdc0bf`）

#### Scenario: Sample 表的 FK 拒絕未知 patient

- **WHEN** 對 `main.aa` 的 INSERT 引用了不存在於 `main.patient` 的 `patient_id`
- **THEN** PostgreSQL MUST 以 foreign-key violation 拒絕此語句
- **AND** Transaction MUST rollback

### Requirement: NBS 子表 SHALL 以原生資料表加上外鍵建模

`nbs.cah_tgal` MUST 是獨立資料表，其 `cah_id` 以 `ON DELETE CASCADE` 指向 `nbs.cah(cah_id)`。`nbs.dmd_tsh` MUST 是獨立資料表，其 `dmd_id` 以 `ON DELETE CASCADE` 指向 `nbs.dmd(dmd_id)`。子列資料 MUST NOT 以 JSONB 形式塞在父列裡。

#### Scenario: 刪除父列會 cascade 到 tgal 子列

- **WHEN** 刪除 `nbs.cah` 中的某 row
- **THEN** 在同一 transaction 中，`nbs.cah_tgal` 中所有 `cah_id` 對應的 row MUST 一併被刪除

#### Scenario: 孤兒子列 INSERT 會被拒絕

- **WHEN** 對 `nbs.dmd_tsh` 的 INSERT 引用了不存在於 `nbs.dmd` 的 `dmd_id`
- **THEN** 該語句 MUST 以 foreign-key violation 失敗

### Requirement: 跨 schema 病人連結 SHALL 以 links.patient_link 標準化 junction 儲存

`links.patient_link` 表 MUST 將病人連結編碼為 `(patient_id_a UUID, patient_id_b UUID, link_kind TEXT, created_at TIMESTAMPTZ)`，主鍵為 `(patient_id_a, patient_id_b)`，並有 `CHECK (patient_id_a < patient_id_b)` 約束以歸一 pair 方向。`link_kind` MUST 為 `same_person`、`probable`、`manual` 之一。MUST 存在 `patient_id_b` 上的次要索引以利反向查詢。回傳給 client 的 `linkedPatientIds: list[str]` 欄位 MUST 由雙向 union 查詢實體化。

#### Scenario: 每條邏輯連結只存一份

- **WHEN** 插入病人 X 與 Y 的連結
- **THEN** `links.patient_link` MUST 恰建立一筆 row，且 `patient_id_a < patient_id_b` 在字典序成立
- **AND** 試圖插入反向 `(Y, X)` 順序 MUST 因 CHECK 約束失敗

#### Scenario: 反向查詢使用 ix_link_b

- **WHEN** 讀取路徑為病人 Y 實體化 `linkedPatientIds`
- **THEN** 查詢 MUST UNION `WHERE patient_id_a = Y` 與 `WHERE patient_id_b = Y`
- **AND** 索引 `ix_link_b` MUST 可用以滿足第二個分支

### Requirement: 條件查詢熱欄位 SHALL 配置 partial index

凡是被以「數值閾值」過濾的儲存型條件模板所引用的欄位，MUST 配置 partial index，且閾值 MUST 內建在 predicate 裡。具體而言，至少必須存在以下 partial index：

- `main.biomarker (dbs_lyso_gb3) WHERE dbs_lyso_gb3 > 5`
- `nbs.cah (ohp17) WHERE ohp17 IS NOT NULL`
- `main.aa (leu) WHERE leu IS NOT NULL`
- `nbs.dmd_tsh (tsh) WHERE tsh IS NOT NULL`

當新的條件模板上線時，引入此模板的 migration MUST 同時加上對應的 partial index。

#### Scenario: 儲存型條件模板使用 partial index

- **WHEN** 儲存型模板「Biomarker 異常」執行 `SELECT * FROM main.biomarker WHERE dbs_lyso_gb3 > 5`
- **THEN** `EXPLAIN` MUST 顯示對 `ix_biomarker_lyso_high` 的 Index Scan 或 Bitmap Index Scan
- **AND** 在單機 1 GB RAM 開發 instance、mock 等量的資料下，runtime MUST < 200 ms

### Requirement: updated_at SHALL 由 BEFORE UPDATE trigger 自動維護

所有同時具有 `created_at TIMESTAMPTZ DEFAULT NOW()` 與 `updated_at TIMESTAMPTZ DEFAULT NOW()` 欄位的資料表 MUST 配置 `BEFORE UPDATE FOR EACH ROW` trigger，呼叫共用函式 `public.set_updated_at()` 將 `NEW.updated_at` 重設為 `NOW()`。應用層程式碼 MUST NOT 手動設置 `updated_at`。

#### Scenario: 應用層 UPDATE 會自動刷新 updated_at

- **WHEN** Service 執行 `UPDATE main.patient SET name = 'X' WHERE patient_id = …` 而未提及 `updated_at`
- **THEN** 該 row 的 `updated_at` MUST 推進到該 transaction 的 `NOW()`
- **AND** `created_at` MUST 不變

### Requirement: Migration SHALL 由啟用 include_schemas=True 的 Alembic 管控

Repo MUST 在 `backend/alembic/` 下保有唯一一個 Alembic root。`env.py` MUST 設定 `include_schemas=True`，並把 `target_metadata` 組成五個 schema MetaData 物件的聯集。`alembic_version` 表 MUST 位於 `public`。任何對五個 schema 的 DDL 變更 MUST 走這個 Alembic root；production 環境 MUST NOT 用 ad-hoc `psql` DDL。

#### Scenario: Migration 同時動到多個 schema 並具原子性

- **WHEN** 一次 Alembic upgrade 在同一 revision 中對 `main.patient` 與 `external.patient` 加欄位
- **THEN** 兩個 ALTER TABLE MUST 在單一 transaction 中執行
- **AND** 任一失敗 MUST 兩個一起 rollback

#### Scenario: 對空資料庫執行 alembic upgrade head

- **WHEN** 對全新空白 `gimc` 資料庫跑 Alembic
- **THEN** `alembic upgrade head` 完成後 MUST 五個 schema 都存在
- **AND** 結果 schema MUST 與 SQLAlchemy declarative metadata 比對 zero diff

### Requirement: data_loader SHALL 透過 env var 在 JSON 與 PostgreSQL 後端之間切換

`backend/shared/shared/data_loader.py` MUST 尊重環境變數 `GIMC_DATA_BACKEND`，值為 `json`（預設、現行行為）或 `postgres`。當選擇 `postgres` 時，`load_all()` MUST 回傳與 JSON 路徑同形狀的 `dict[str, dict[str, list[dict]]]`，row dict 的 key 為 camelCase 且與 JSON 路徑產生的鍵集相同。`validate()` MUST 對 PostgreSQL 後端發出 FK 驗證查詢（`LEFT JOIN … IS NULL`），失敗時拋出與 JSON 路徑相同形狀的 `ValueError`。

四個 FastAPI service（`gateway`、`svc-patient`、`svc-lab`、`svc-disease`）MUST NOT 為了支援後端切換而改 Python 程式碼 — `data_loader` 是唯一接縫。

#### Scenario: 切換後端時 service 程式碼不變

- **WHEN** 一次 service 跑在 `GIMC_DATA_BACKEND=json`、另一次跑在 `GIMC_DATA_BACKEND=postgres`
- **THEN** 兩次之間 service 的 Python 原始檔 MUST 位元相等
- **AND** 同一 `patientId` 的 API 回應 MUST 具有相同的 JSON 形狀與鍵集

#### Scenario: dbsLysoGb3 模板的 mock-parity 回歸

- **WHEN** 儲存型條件模板 `dbsLysoGb3 > 5` 在 `GIMC_DATA_BACKEND=postgres` 下執行
- **THEN** 命中的 `patientId` 集合 MUST 等於 JSON 後端在同樣 mock 資料種子下的命中集合

### Requirement: BLOB SHALL 落到檔案系統，DB 只存路徑

由 1.0 帶入的二進位 BLOB 欄位 — `MSDATA.DATA`（原始質譜）、`GCDATA.pic`、`MPSUDATA.pic`、`ENZYME.pic`（影像附件）— MUST NOT 以 PostgreSQL `bytea` 或 large object 儲存。其內容 MUST 寫入檔案系統 `/srv/gimc/blobs/{msms,gcms,mpsu,enzyme}/<sample_or_uuid>.<ext>`，DB row MUST 改存 `raw_data_path TEXT` 欄位指向該路徑。

#### Scenario: ETL 期間將 BLOB 物化到檔案系統

- **WHEN** 一筆 `MSDATA` row 含有非 null `DATA` blob 被遷移
- **THEN** 位元組 MUST 寫到 `/srv/gimc/blobs/msms/<sampleno>.bin`
- **AND** 對應 `main.msms` row 的 `raw_data_path` MUST 等於該路徑字串
- **AND** MUST 沒有 `bytea` 欄位含有原始位元組
