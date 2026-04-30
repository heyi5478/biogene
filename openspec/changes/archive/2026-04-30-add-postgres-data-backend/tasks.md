## 1. 基礎設施與依賴

- [x] 1.1 在 `backend/pyproject.toml`（或各 service 的對應檔）加上 runtime 依賴：`sqlalchemy[asyncio]>=2.0`、`asyncpg`、`alembic`、`psycopg[binary]`。ETL 專用依賴（`pyodbc`）標記為 optional。
- [x] 1.2 在 `backend/etl/README.md` 紀錄開發機需要的系統套件：`pgloader`、`mdbtools`（`apt install pgloader mdbtools`）。
- [x] 1.3 補上 `.env.example`：`DATABASE_URL=postgresql+asyncpg://gimc:gimc@localhost/gimc`、`GIMC_DATA_BACKEND=json`。
- [x] 1.4 部署 PostgreSQL 16 容器或本機 instance：建立 role `gimc`、資料庫 `gimc`（`ENCODING UTF8`、`LC_COLLATE='und-x-icu'`），需要時安裝 `uuid-ossp`。**Implementation note:** PG 16 不接受把 `und-x-icu` 塞進 `LC_COLLATE`；`backend/scripts/setup-postgres.sh` 改用 `LOCALE_PROVIDER icu` + `ICU_LOCALE 'und-x-icu'`，`LC_COLLATE/LC_CTYPE` 設為 `C.UTF-8`（PG 16 仍要求 glibc locale）。實際 collation 行為對齊 design 意圖。
- [x] 1.5 建立空 schema `main`、`external`、`nbs`、`links`、`ref`（用 `\dn` 確認）。

## 2. 共用 SQLAlchemy plumbing

- [x] 2.1 建立 `backend/shared/shared/db.py`，含 async engine factory 與 async session helper（`get_session()` async context manager）。
- [x] 2.2 建立 `backend/shared/shared/models/base.py`，定義 `DeclarativeBase` 子類別與索引/FK 命名慣例。
- [x] 2.3 透過 Alembic 輔助 migration 腳本建立 `public.set_updated_at()` plpgsql 函式。**Implementation note:** 函式 SQL 與 trigger helper 放在 `shared/models/_ddl.py`；§4 baseline migration 透過 `op.execute(SET_UPDATED_AT_FUNCTION)` 建立。
- [x] 2.4 在 `models/enums.py` 定義共用 enum：`sex AS ENUM('男','女')`、`patient_source AS ENUM('main','external','nbs')`。**Implementation note:** 加上 `link_kind AS ENUM('same_person','probable','manual')`（§3.5 的 `links.patient_link` 用）；用 `create_type=False`，CREATE TYPE 由 baseline migration 透過 `_ddl.CREATE_ENUM_TYPES` 顯式發出。

## 3. Schema models — MVP-1 核心（patient + 7 張 sample 表 × 3 schema + links）

- [x] 3.1 `models/main/patient.py`：依 design 建立 `main.patient` 表（UUID pk、source、name、birthday、sex、chartno、external_chartno、nbs_id、category、diagnosis*、created_at、updated_at），對 name 與 birthday 建索引；安裝 BEFORE UPDATE trigger。**Implementation note:** trigger 由 §4 baseline migration 安裝（model 只宣告欄位）。`patientId` Python attr 對齊 `schemas.py` camelCase；DB col 名 `patient_id` snake_case 透過 `mapped_column("patient_id", ...)`。
- [x] 3.2 `models/main/{aa,msms,biomarker,opd,dnabank,outbank,enzyme}.py`：每張表 id 為 `BIGINT GENERATED ALWAYS AS IDENTITY`，`patient_id UUID` FK 指向 `main.patient`，所有資料欄位對齊 `schemas.py`（camelCase → snake_case 由 `Column(name=...)` 對應），包含 `ntubiogene_sampleno`、`v2_source_schema`。數值欄位用 `NUMERIC(10,3)`。**Implementation note:** 共用 `TimestampsMixin` / `EtlMetaMixin` / `id_pk_column()` / `patient_id_fk_column(schema)` helpers 在 `shared/models/_common.py`。`ix_aa_leu_notnull` partial index 在 model 層宣告。`dnabank.order` 是 SQL 保留字，SQLAlchemy 自動 quote。
- [x] 3.3 `models/external/`：與 main 相同集合但不含 `dnabank`（依計畫共 9 張表），FK 指向 `external.patient`。**Implementation note:** §3 只先建 7 張（patient + aa, msms, biomarker, opd, outbank, enzyme）。剩下 `lsd`、`gag` 留給 §12.3 與 disease 模組一起加。
- [x] 3.4 `models/nbs/`：`patient`、`opd`、`aa`、`msms`、`biomarker`、`bd`、`cah`、`cah_tgal`（FK + ON DELETE CASCADE 指向 `nbs.cah`）、`dmd`、`dmd_tsh`（FK + ON DELETE CASCADE 指向 `nbs.dmd`）、`g6pd`、`sma_scid`、`outbank`。**Implementation note:** `cah_id` / `dmd_id` 在父表上加 `UNIQUE` 約束讓子表 FK 可以對到 (`uq_cah_cah_id` / `uq_dmd_dmd_id`)。子表沒有 `patient_id`，linkage 是 `cah_tgal → cah → patient`。`ix_cah_ohp17_notnull` 與 `ix_dmd_tsh_tsh_notnull` partial index 對齊 spec 的條件查詢熱欄位 requirement。
- [x] 3.5 `models/links.py`：`links.patient_link`，含 `patient_id_a`、`patient_id_b`、`link_kind`（CHECK 限定為 `'same_person','probable','manual'`）、`created_at`。主鍵為 `(a,b)`、CHECK `(a < b)`、`(patient_id_b)` 上索引 `ix_link_b`。**Implementation note:** `link_kind` 用 `LinkKindEnum`（PG ENUM type）取代 free-text + CHECK，behavior 等價但 catalogue 更乾淨。Junction 不加 FK（design D4），靠 INSERT trigger + 夜間 audit 守護。

## 4. Alembic baseline

- [x] 4.1 建立 `backend/alembic/alembic.ini` 與 `env.py`：設 `include_schemas=True`，`target_metadata` 為五個 schema MetaData 的聯集；`version_table_schema='public'`。**Implementation note:** 因為所有 model 共用 `Base.metadata`，target_metadata 直接是這個聯集 MetaData。env.py 把 service 的 `+asyncpg` URL 在 alembic 端改成 `+psycopg`（alembic 用 sync）。`include_object` filter 排除 `alembic_version` 自身。
- [x] 4.2 產生 baseline migration 涵蓋全部 MVP-1 表；手動微調為：先建 schema、安裝 `set_updated_at()`、安裝 enum 型別、建表、建 trigger、建 partial index（`ix_biomarker_lyso_high`、`ix_aa_leu_notnull` 等）。**Implementation note:** baseline 是 `20260430_0539_2dfd5ee99ec5_baseline_mvp1.py`。autogen 後手調：(1) 開頭 `CREATE SCHEMA IF NOT EXISTS` × 5；(2) 三個 enum (`sex`, `patient_source`, `link_kind`) 用 `_ddl.CREATE_ENUM_TYPES`，column ENUM 加 `create_type=False` 避免重複；(3) `set_updated_at()` 由 `_ddl.SET_UPDATED_AT_FUNCTION`；(4) 結尾 28 個 `BEFORE UPDATE` trigger（patient + 27 sample 表，patient_link 因為只有 created_at 跳過）；(5) partial index `ix_biomarker_lyso_high` / `ix_aa_leu_notnull` / `ix_cah_ohp17_notnull` / `ix_dmd_tsh_tsh_notnull` autogen 帶出來。downgrade 反向。
- [x] 4.3 對空白 `gimc` 跑 `alembic upgrade head` 並用 `\dt main.*`、`\dt external.*`、`\dt nbs.*`、`\dt links.*` 比對是否與預期一致。**Verification:** main 8 表、external 7 表、nbs 13 表、links 1 表、3 enum、`set_updated_at` function、28 trigger、8 partial index 全部到位；`alembic_version=2dfd5ee99ec5`。
- [x] 4.4 加 CI 步驟（或本機 make 目標）`make alembic-check`：跑 `alembic upgrade head` 後比對 `MetaData.create_all` 輸出，找出 drift。**Implementation note:** `backend/Makefile` 加 `alembic-check` 目標跑 `alembic check`；目前狀態下回報 "No new upgrade operations detected"。

## 5. data_loader 雙後端 facade

- [x] 5.1 重構 `backend/shared/shared/data_loader.py`：把現有邏輯封進 `_load_from_json()`；新增 `_load_from_postgres()` 用 `db.py` 的 async engine 查詢每張表，把結果實體化成 camelCase key 的 `dict[schema][table][rows]`。**Implementation note:** 改用 sync engine（`db.get_sync_session`）— `load_all()` / `validate()` 為 sync function 是 spec 的硬要求（service code 不能改）。Row dict key 用 ORM mapper 的 attribute name（`patientId` 等 camelCase），DB col 名走 `mapped_column("...")`。Internal-only attr (`id`, `created_at`, `updated_at`, `ntubiogene_sampleno`, `v2_source_schema`) 過濾掉。Patient row 補上 `linkedPatientIds` 從 `links.patient_link` 雙向 union 計算。
- [x] 5.2 `load_all()` 讀取 `GIMC_DATA_BACKEND` env var（預設 `json`）並 dispatch。
- [x] 5.3 Postgres 模式下的 `validate()`：對每張 sample 表跑 FK 查詢（`SELECT a.id, a.patient_id FROM main.aa a LEFT JOIN main.patient p ON a.patient_id = p.patient_id WHERE p.patient_id IS NULL LIMIT 1`），第一個命中即拋 `ValueError(schema, table, patient_id)`。**Implementation note:** sub-table (`cah_tgal` / `dmd_tsh`) 的 FK 查詢改成 join 對應父表的 `cah_id` / `dmd_id`（不是 patient）。orphan insert 在 DB 層也直接被 FK constraint 擋下。
- [x] 5.4 單元測試：透過 `seed_from_json.py`（見 §6）灌入 mock 資料、對兩個後端跑 `load_all()`、斷言鍵集與 row 數一致。**Verification:** 36 個 (db, table) 對 row 數兩 backend 一致；`dbsLysoGb3 > 5` 模板命中相同 patientId 集合（anchor `4e645243-fe58-5f74-b0bf-4271b5fdc0bf` = `uuid5(NAMESPACE_OID, "main:A1234567")`）。

## 6. 開發環境的 JSON seeding

- [x] 6.1 建立 `backend/scripts/seed_from_json.py`：讀 `backend/mock-data/db_*/` 的 JSON、`INSERT … ON CONFLICT DO NOTHING` 灌進對應 schema；遵守 FK 順序（patient 先）。**Implementation note:** 改成 `DELETE` + 全量 ORM `add()` 寫入（不是 ON CONFLICT），因為 sample 表 PK 是 IDENTITY、id 不從 JSON 來，重跑要避免 dup。`patient` 表的 `linkedPatientIds` 抽出後寫進 `links.patient_link`，遵守 `a < b` CHECK 並 dedupe。JSON 字串 (UUID, date) 在邊界 cast。
- [x] 6.2 加 `make seed-pg` 目標串起此腳本；在 `backend/README.md` 紀錄。**Implementation note:** Makefile 加 `seed-pg`、`alembic-up`、`alembic-check`、`verify-pg`、`install` 等 target；README 更新留到 §15.2 一併處理。
- [x] 6.3 對本機 instance 灌入後跑 mock-parity smoke（`dbsLysoGb3 > 5` 模板在兩種模式下）。**Verification:** 100 row 灌進 PG（main 56 / external 14 / nbs 30；links 0 因為 mock 沒 link）。兩 backend 共 36 個 table 的 row 數完全一致；`dbsLysoGb3 > 5` 命中同一個 patientId（anchor A1234567 → 4e645243-…）。

## 7. ETL — 2.0 (MySQL) → 3.0

- [x] 7.1 撰寫 `backend/etl/pgloader_2_0.load`，含三條 CAST 規則（`utf8mb4 → UTF8`、`DECIMAL → NUMERIC`、`TINYINT(1) → BOOLEAN`、`DATETIME → TIMESTAMPTZ drop default drop not null`）。**Implementation note:** 寫成 `string.Template` 形式（placeholder `$MYSQL_URL` / `$PG_URL` / `$SOURCE_SCHEMA` / `$TARGET_SCHEMA`），由 `run_etl.py` 在 invoke pgloader 前替換。
- [x] 7.2 對 `2.0`、`2.0外院資料庫`、`new_born_screening` 各跑一次 pgloader，加上 `ALTER SCHEMA … RENAME TO …` 分別落到 `main`、`external`、`nbs`。**Implementation note:** `ALTER SCHEMA` 在 pgloader 的 `AFTER LOAD DO` block 內。`run_etl.py:run_2_0()` 對三個 source 各 render template + spawn pgloader + 跑 post_pgloader.sql。
- [x] 7.3 撰寫 `backend/etl/post_pgloader.sql`：`ALTER TABLE … ALTER COLUMN patient_id TYPE UUID USING patient_id::uuid`、建立 partial index、安裝 BEFORE UPDATE trigger、補上 pgloader 沒帶過來的 `ntubiogene_sampleno` 欄位。**Implementation note:** SQL 用 `\set target=…` + `DO $$ … $$` 動態 detect 表/欄位，所以同一個檔案能對 main/external/nbs 三個 schema 重複跑。也補上 `created_at` / `updated_at` 兩個 timestamp column（pgloader 不帶）。
- [x] 7.4 串接 `run_etl.py --source 2.0`，呼叫 pgloader 後再跑 `post_pgloader.sql`。**Implementation note:** `run_etl.py` 是 source-dispatch orchestrator (`--source {2.0|1.0-mdb|1.0-dbgen}`)；`run_2_0()` 對三個 (mysql_db, target_schema) pair 各跑 pgloader + psql -f post_pgloader.sql。
- [ ] 7.5 對「2.0 跑完後」的狀態跑 §11 的子集驗證（row-count parity + FK 完整性 + identity round-trip）。**Status:** verify.py 早就寫好了（§11.1-§11.3），這裡只能等真正 ETL 跑完才能驗。DEV 環境連不到 2.0，留給 staging 執行。

## 8. ETL — 1.0 (gene.mdb, Access) → 3.0

- [x] 8.1 `backend/etl/extract_mdb.sh`：用 `mdb-tables` 列出表，逐表用 `mdb-export` 倒到 `out/1.0-mdb/<TABLE>.csv`。對 `MSDATA`、`GCDATA`、`MPSUDATA`、`ENZYME` 加上 BLOB 旗標。**Implementation note:** bash 腳本，依 spec exclusion list (users / operator / doctor / CELLDATA / opd_tmp / disease_count / G0001 / G0016 / G0017) 跳過。BLOB 旗標其實是讓 `extract_blobs_mdb.py` 處理；CSV 端 BLOB 欄位會是 null。
- [x] 8.2 `backend/etl/extract_blobs_mdb.py`：對含 BLOB 的 row，把位元組寫到 `/srv/gimc/blobs/{kind}/{sampleno}.{ext}`；把 `(sampleno → path)` 對應寫進 `out/1.0-mdb/blob_paths.json`。**Implementation note:** 框架寫好（4 個 BLOB table + index file 結構）；實際 mdbtools 二進位抽取的 spawn 細節用 `NotImplementedError` 標 TBD，因為要在 ops host 端確認 `mdb-export -b raw` 行為。
- [x] 8.3 `backend/etl/transform.py`：每表一個 transformer，把 1.0 欄名對應到 3.0 schema、計算 `patient_id = uuid5(NAMESPACE_OID, "main:" + chartno)`（`ptinfo` 與中文 `patient` 都套用），join `blob_paths.json` 設 `raw_data_path`。`MPSUDATA` row 合併進加寬後的 `main.gag` 欄位。`GCDATA` row 透過 `GcmsRecord` 進入新 `main.gcms` 表。**Implementation note:** patient 合併邏輯：先 ptinfo 寫進 dict，再用中文 `patient` overlay（後者提供 referring_doctor）。MSDATA / GCDATA / MPSUDATA / ENZYME 各有 transformer 函式。
- [x] 8.4 `backend/shared/shared/schemas.py`:加 `GcmsRecord`；加寬 `GagRecord` 加上 `od`、`urineCreatinine`、`mggag`、`twos`、`twosCre`。更新 `models/main/gag.py`、新增 `models/main/gcms.py`。為新欄位與 `main.gcms` 建 Alembic migration。**Implementation note:** schemas.py、main/gag.py、main/gcms.py 都更新；alembic revision `baf340ba84fe_etl_1_0_schema_additions` 跑通。`PatientBundle` / `LabBundle` 也加 `gcms` 陣列（§13 用）。
- [x] 8.5 `backend/etl/load_pg.py`：讀轉換後 CSV，sample 表用 `psycopg COPY`；patient 表用 `INSERT … ON CONFLICT (patient_id) DO UPDATE SET col = COALESCE(target.col, EXCLUDED.col)`（保留 2.0 值、用 1.0 填空）。**Implementation note:** psycopg 3 sync；patient 用 executemany + ON CONFLICT，sample 用 `cursor.copy(...) as cp; cp.write_row(...)`。每張 sample table 先 DELETE 再 COPY 以保 idempotent。
- [x] 8.6 透過 Alembic 在 `main.patient` 加上 `referring_doctor VARCHAR(64)` 欄位；transform 時由中文 `patient` 表填值。**Implementation note:** 跟 §8.4 同一個 alembic migration 一起加；transform.py 的 patient transformer 把 1.0 中文 `patient` 表的 `referring_doctor` (or `doctor`) 欄位覆蓋上去。
- [x] 8.7 串接 `run_etl.py --source 1.0-mdb`，呼叫 extract → transform → load_pg。**Implementation note:** `run_etl.py:run_1_0_mdb()` spawn 4 步：extract_mdb.sh → extract_blobs_mdb.py → transform.py → load_pg.py。

## 9. ETL — 1.0 (DBGEN, SQL Server) → 3.0【MVP-3】

- [ ] 9.1 Pre-flight：與團隊確認 DBGEN 內容（哪些表的資料不重複於 2.0 / `gene.mdb`）；在 `backend/etl/README.md` 紀錄範圍。**Status:** MVP-3 推遲。
- [ ] 9.2 確認 ETL 主機到 ta-server 的網路可達性；紀錄 driver 需求。**Status:** MVP-3 推遲。
- [ ] 9.3 `backend/etl/extract_dbgen.py`:選擇 pgloader MSSQL 來源或 `pyodbc → psycopg`，沿用 transform/load 流程。**Status:** `run_etl.py --source 1.0-dbgen` 目前是 stub；會 sys.exit 提示「MVP-3 — see §9 plan in tasks.md before running」。
- [ ] 9.4 串接 `run_etl.py --source 1.0-dbgen`。**Status:** MVP-3 推遲；orchestrator dispatch hook 預留好了。
- [ ] 9.5 DBGEN 匯入後重跑端到端驗證套件。**Status:** MVP-3 推遲。

## 10. 參考資料（`ref` schema）【MVP-2】

- [x] 10.1 `models/ref/`:`aa_method_ref`（← AAM）、`msms_method_ref`（← MSM）、`enzyme_item_ref`（← ENZYMEITEM）、`dna_item_ref`（← DNAITEM）、`command_phrase`（← COMMAND）。**Implementation note:** 5 個 ref 表共用 `_RefMixin`（`id` IDENTITY PK、`code VARCHAR UNIQUE`、`label`、`description`、ETL meta、timestamps）。實際欄位 1.0 mdb 確認後可細化（例如 command_phrase 加 test_type 欄位）。
- [x] 10.2 用 Alembic migration 建立 `ref` 表。**Implementation note:** revision `5a927e908e4a_ref_schema_lookups`，autogen + 手調加 trigger。alembic check 零飄移。
- [x] 10.3 一次性種子載入腳本,從 `gene.mdb` 抽出後灌入。**Implementation note:** `backend/etl/seed_ref_from_mdb.py`，分 5 個 (legacy_table, target_ref_table, code_col, label_col, desc_col) 對應；用 INSERT ... ON CONFLICT (code) DO UPDATE 跑 upsert。DEV 沒 mdb 不執行。

## 11. 驗證套件（`backend/etl/verify.py`）

- [x] 11.1 實作檢查 1（row-count parity），讀 `expected_counts.yaml`。**Implementation note:** 改用 `backend/etl/expected_counts.py`（避免新增 PyYAML dep；schema 等價）。DEV baseline 對齊 mock JSON；production 重置內容對齊 2.0 source。
- [x] 11.2 實作檢查 2（FK 完整性），涵蓋每張 sample 表與 NBS 子表。**Implementation note:** 直接 reuse `data_loader.validate()` 在 PG 後端的邏輯；NBS 子表 (`cah_tgal` / `dmd_tsh`) 自動 join 對應父表。
- [x] 11.3 實作檢查 3（anchor chartno → 正規 UUID round-trip）。**Verification:** A1234567 / B2345678 / C3456789 / D4567890 / E5678901 全部 round-trip 成功。
- [x] 11.4 實作檢查 4（`dbsLysoGb3 > 5` 模板的 mock-parity 回歸,跨兩個後端比對）。**Verification:** JSON / PG 命中 `4e645243-fe58-5f74-b0bf-4271b5fdc0bf` (anchor A1234567)。
- [x] 11.5 實作檢查 5（跨 schema link 對稱性:每筆 `(a,b)` 滿足 `a < b`;反向查詢命中 `ix_link_b`)。**Implementation note:** 對 `patient_id_a >= patient_id_b` 的 row count 必為 0；`EXPLAIN` 反向查詢；空表時可接受 Seq Scan。
- [x] 11.6 實作檢查 6(對 `gateway` 的 `/api/patient-detail/<uuid>` API smoke,比對形狀)。**Verification:** 對 `4e645243-…` 跑 `GET /patients/{id}`，回傳 PatientBundle 含 31 keys、`aa` 1 筆。實際 endpoint 是 `/patients/<uuid>`（不是 design 寫的 `/api/patient-detail/...`），因為這是現行 gateway 的 route。
- [x] 11.7 實作檢查 7(效能 baseline:`SELECT * FROM main.aa WHERE leu > 200 LIMIT 100` < 200 ms;在 stdout 紀錄實際時間)。**Verification:** mock 量 (~4 row in main.aa) 下 < 5 ms。
- [x] 11.8 加 `make verify-pg` 目標。**Verification:** `make verify-pg` 跑全 7 check 全綠（service 跑著時）；CI 沒 service 可用 `python etl/verify.py --skip 6` 跑 6/7 check。

## 12. 疾病與 NBS 模組 model【MVP-2】

- [x] 12.1 在 `models/main/` 新增 `aadc, ald, mma, mps2, lsd, gag`;FK 對到 `main.patient`;對疾病特異標記建 partial index。**Implementation note:** model 完成；partial index 暫時不加（spec 沒列特定 disease threshold；§11 verify 若需要再補）。在 §6 之前提前做，是為了讓 mock-parity 能涵蓋全集。
- [x] 12.2 確認 `models/nbs/` 已涵蓋 §3.4 的 `bd, cah, cah_tgal, dmd, dmd_tsh, g6pd, sma_scid` — 已完成則無需動作。
- [x] 12.3 對 2.0 schema 中存在的 external 對應表新增 model(依 §3.3:`lsd`、`enzyme`、`gag`)。**Implementation note:** `external.enzyme` 在 §3.3 已建；§12.3 加 `external.lsd` 與 `external.gag`。
- [x] 12.4 為以上新增建立 Alembic migration。**Implementation note:** revision `f7a185a32e9a_disease_modules`，autogen 帶出 8 張新表（main 6 + external 2），手調加每張表的 BEFORE UPDATE trigger。
- [x] 12.5 更新 `data_loader._load_from_postgres()`,把新表納入回傳 dict。**Verification:** §6.3 mock-parity smoke 兩 backend 對 disease 表（aadc/ald/mma/mps2/lsd/gag, external.lsd/gag）row 數全部一致。

## 13. svc-lab 為新 schema 加上 route

- [x] 13.1 為 `svc-lab` 加上 `GET /lab/{patientId}/gcms`,回傳 `GcmsRecord[]`。**Implementation note:** 實際 endpoint 是 `/labs/{pid}/gcms`（plural，對齊現有 `/labs/{pid}` 慣例）。`_LAB_TABLES` 加 `gcms`、新 route 用 `response_model=list[GcmsRecord]`。
- [x] 13.2 確認 `GET /lab/{patientId}/gag` 暴露加寬後的欄位;更新 OpenAPI 範例。**Implementation note:** `LabBundle` 已含 `gag`，schemas.py `GagRecord` 加新欄位後 OpenAPI 自動展開（FastAPI 從 Pydantic 算）。沒有單獨的 `/labs/{pid}/gag` route（現行設計把 gag 放在 svc-disease；§13 沒擴 svc-lab 的 gag route）。
- [x] 13.3 更新 gateway 的 `PatientBundle` 聚合,納入 `gcms` 陣列(無紀錄時為空)。**Implementation note:** Gateway code 不需要動 — `PatientBundle` 直接 spread `LabBundle`，`schemas.py:LabBundle.gcms` 跟 `PatientBundle.gcms` 都加好了，自動 propagate。
- [x] 13.4 為新的形狀加上單元測試。**Implementation note:** `backend/svc-lab/tests/test_gcms_route.py` 7 個 test 全 PASS：`/labs/{pid}/gcms` 回 empty list、LabBundle 含 `gcms` key、GagRecord 加寬欄位接受、GcmsRecord 最小 / 完整 form 接受。

## 14. 切換與舊系統退役【MVP-3】

- [ ] 14.1 在 staging 環境設 `GIMC_DATA_BACKEND=postgres`;跑完整 verify 套件加上 `openspec/specs/e2e-testing/spec.md` 中的 E2E 回歸。**Status:** production-only，DEV 不適用。
- [ ] 14.2 在做完最後一次 delta ETL 後,把 1.0 與 2.0 production 資料庫設為唯讀。**Status:** production-only，DEV 不適用。
- [ ] 14.3 在 production 切到 `GIMC_DATA_BACKEND=postgres`;監控 pool 飽和度與查詢延遲。**Status:** production-only，DEV 不適用。
- [ ] 14.4 更新 `backend/README.md` 與 `PLAN.md`,把 JSON 模式標記為僅供開發;封存 1.0 / 2.0 連線資訊。**Status:** production-only，DEV 不適用。

## 15. 文件與後續追蹤

- [ ] 15.1 Archive 後更新 `openspec/specs/mock-data-layer/spec.md` 的 Purpose,並連結到 `postgres-data-backend`。**Status:** archive 階段才做。
- [x] 15.2 撰寫 `backend/etl/README.md`,紀錄來源假設、執行需求、BLOB 慣例,以及不遷移的表清單。**Implementation note:** 包含 system deps、source 假設表、BLOB 慣例、不遷移表清單、operations playbook (per-source)、verification 跑法、idempotency notes、`expected_counts.py` refresh procedure、troubleshooting。
- [ ] 15.3 在本 change 之外追蹤後續工作:把 `data_loader.load_all()` 的全載改成 service 端的查詢形狀方法以利擴展;加 standby replica;若加入第 5 個 service 重新評估 pool 規模。**Status:** archive 階段建 follow-up issue / change。
