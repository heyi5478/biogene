## Context

my-project（3.0）目前完全跑在 JSON mock 資料上：`backend/shared/shared/schemas.py` 定義 17 個 Pydantic record type、`backend/mock-data/` 下三個資料庫目錄（`db_main`、`db_external`、`db_nbs`）已對齊 2.0 的三個 MySQL 資料庫、`backend/scripts/load_mock.py` 強制 FK、`data_loader.py` facade 由 4 個 FastAPI service 共用。Mock 層的設計刻意做到「換成真實 DB 時只動 `data_loader.py`」這條路。

兩個舊系統握有要吸收的真實資料：

| 版本 | 技術 | 儲存 | 狀態 |
|---|---|---|---|
| 1.0 | ASP.NET Web Forms（`ntubiogene`） | `gene.mdb`（Access） + `DBGEN`（ta-server 的 SQL Server） | 運作中、有真實資料、預定退役 |
| 2.0 | MySQL 三庫 — `2.0` / `2.0外院資料庫` / `new_born_screening` | 另一台機器的 MySQL | 運作中、有真實資料、預定退役 |

3.0 要取代兩者。Mock 資料的目錄結構已經對齊 2.0 的三庫拆分，因此大部分 schema 已被決定；缺的是資料庫本身、ETL 流水線，以及雙模 `data_loader`。本 change 依使用者要求把 MVP-1、MVP-2、MVP-3 都包成同一個 OpenSpec change — 範圍偏大，但模組之間耦合很緊（ETL 腳本依賴 schema；schema 依賴從舊系統搬進來的新欄位；`data_loader` 在 schema 沒到位前無法做有意義的後端切換）。

來自既有 spec 與程式碼的限制：
- `mock-data-layer` spec 已要求 `patient_id = uuid5(NAMESPACE_OID, "{source}:{naturalKey}")` — 這條規則原樣延伸到 DB row。
- `backend-api` spec 要求 gateway 的 `PatientBundle` 形狀穩定；換後端不能擾動傳輸格式。
- `load_mock.py` 已經編碼了 NBS 子表 FK（`SUB_TABLE_FKS` 對應 `cah_tgal → cah`、`dmd_tsh → dmd`）；同樣的關係必須以 PostgreSQL 原生跨表 FK 表達。

## Goals / Non-Goals

**Goals：**
- 單一 PostgreSQL 16 instance、單一資料庫 `gimc`、五個 schema（`main`、`external`、`nbs`、`links`、`ref`）。Schema 是唯一的 namespace；跨 schema join 仍直觀。
- 4 個 FastAPI service 不動 `data_loader.load_all()` / `validate()` 的呼叫；後端由 `GIMC_DATA_BACKEND` ∈ {`json`, `postgres`} 決定。
- 確定性 `patient_id` UUID 跨 1.0 / 2.0 一致 → 1.0 的兩張病人表（舊 `ptinfo` 與新中文 `patient`，都以 `chartno` 為 key）會自動在 `INSERT … ON CONFLICT (patient_id) DO UPDATE` 時合併。
- 一次性 ETL — 不做常態同步。切換完成後，1.0 / 2.0 設為唯讀。
- 驗證套件，證明 DB 模式對既有條件模板的回答與 JSON 模式相同（mock-parity 是回歸網）。

**Non-Goals：**
- MOH 申報表單（`G0001/G0016/G0017`）留在 1.0；3.0 這次不接申報流程。
- 不做即時 federation、雙向同步、CDC。
- 不搬：`users`、`operator`、`doctor`（3.0 自己有 auth）、`CELLDATA`、`opd_tmp`、`disease_count`（統計改成隨需計算）。
- 本 change 不做 multi-tenant 或 row-level security。
- BLOB 不放在 PostgreSQL `bytea` / large object，落到檔案系統。

## Decisions

### D1. 一個資料庫，五個 schema（vs. 多個資料庫，vs. 攤平單一 schema）

採用單一 PostgreSQL 資料庫 `gimc`，schema 為 `main`、`external`、`nbs`、`links`、`ref`。

- **為什麼選這個而不是多資料庫**：2.0 之所以分三個 MySQL 資料庫，是因為 MySQL 的「schema」就等於資料庫，沒有別的 namespace 可用。PostgreSQL 有真正的 schema，跨 schema join 是直接 `SELECT … FROM main.patient JOIN external.patient …`，不需要 FQN 體操，也不需要跨 DB FK（PostgreSQL 原生不支援）。
- **為什麼選這個而不是攤平單一 schema**：保留團隊既有心智模型（大家已經在講「main / external / nbs」），讓 `mock-data/` 目錄與 schema 一一對映，並讓 `pg_dump --schema=main` 可以切出邏輯 DB 做備份或遷移。
- `links` 與 `ref` 是新加的、不屬於原本三庫任何一個 namespace；給它們各自的 schema 既保留了原本三個 schema 的純粹，也對齊它們各自的生命週期（links 永久存在、ref 由 1.0 種子填入）。

### D2. `patient_id` 用原生 `UUID`，由 `uuid5(NAMESPACE_OID, "{source}:{naturalKey}")` 產生

- **原生 `UUID` 型別、不是 `CHAR(36)`**：儲存只佔 16 byte 而不是 36，索引可雜湊，避免字串格式漂移。
- **與 `mock-data-layer/spec.md` 共用同一條 seed 規則**：1.0 的兩張病人表（舊 `ptinfo` 與新中文 `patient`）都以 `chartno` 為 key，因此會碰撞到同一個 UUID，在 ETL upsert 時自動合併。2.0 已經存了這些 UUID，原樣搬即可。
- **考慮過的替代方案 — 用代理鍵 `BIGSERIAL` 加上獨立 `chartno` lookup**：駁回，因為這會失去跨版本身份保證；得改用人工對帳取代「seed 自動去重」。

### D3. NBS 子表用獨立資料表，不用 JSONB

`cah_tgal` 與 `dmd_tsh` 各自做成 `nbs.cah_tgal` / `nbs.dmd_tsh`，FK 指向父表。Pydantic v2 已用 nested list 表達這對關係（`schemas.py:181–212`），`load_mock.py:SUB_TABLE_FKS` 也已經編碼了父子關係；spec 測試網假設這些子列是可定址的 row、不是不透明的 JSON。

- **為什麼不用 JSONB**：查詢模式會打到單一子列（採檢日篩選、結果文字比對）；對 JSONB 做這類索引比 FK + B-tree 重。
- **代價**：要遷移的表變多。可接受 — 這種對只有兩組。

### D4. 跨 schema 病人連結用 `links.patient_link` junction 表

取代目前在 `schemas.py:32` 的 `linkedPatientIds: list[str]`，物化成 junction：

```sql
CREATE TABLE links.patient_link (
  patient_id_a UUID, patient_id_b UUID, link_kind TEXT,
  PRIMARY KEY (patient_id_a, patient_id_b),
  CHECK (patient_id_a < patient_id_b)
);
```

- 用 CHECK 強制 pair 方向歸一，每條 link 只存一份；讀取時 UNION 兩個方向再實體化回 `linkedPatientIds`。
- **junction 上不加 FK**：`patient_id_a` 可能來自 `main` / `external` / `nbs` 的任何一個，PostgreSQL FK 在跨 schema 的多型情境下沒有 conditional trigger 之外的好做法。改用週期性 audit 與 INSERT trigger 驗證。
- **考慮過的替代方案 — 三個可空 FK（一個 schema 一個）**：駁回，因為要為一個邏輯關係加上三個可空欄位與三個 FK 索引。

### D5. Service 端用 SQLAlchemy 2.0 async + asyncpg；ETL 端用 psycopg 3

- **Service path**：`SQLAlchemy 2.0` declarative + async session 跑在 `asyncpg`（連線字串 `postgresql+asyncpg://…`）。對齊 FastAPI service 已是 async 的事實。
- **ETL path**：`psycopg[binary]`（psycopg 3）— `COPY FROM STDIN` 在批次匯入時比 INSERT 快 10×+，而且一次性腳本不需要 async。
- **連線池規模**：每 service `pool_size=5, max_overflow=10`，× 4 = 60；PostgreSQL 預設 `max_connections=100` 留有餘裕給 ETL 與管理工具。

### D6. ETL：2.0 / DBGEN 用 pgloader；`gene.mdb` 用 mdbtools + 自製 Python

- **2.0（MySQL）→ 3.0**：pgloader 一次處理 `utf8mb4 → UTF8`、`DECIMAL → NUMERIC`、`TINYINT(1) → BOOLEAN`、`DATETIME → TIMESTAMPTZ`。跑三次（一個 schema 一次）。隨後跑 `post_pgloader.sql` 處理 `CHAR(36) → UUID`（pgloader 不會自動升型）、partial index、`updated_at` 用的 `BEFORE UPDATE` trigger。
- **1.0 `gene.mdb`（Access）→ 3.0**：`mdbtools` 是 Linux 端唯一的 Access 讀取工具。輸出 CSV → Python（`psycopg COPY`）載入。1.0 的差異（英文舊欄名、BLOB、MOH 申報表）需要轉換，因此自製 `transform.py` 是合理的。
- **1.0 `DBGEN`（MSSQL）→ 3.0**：pgloader 也支援 MSSQL；推到 MVP-3，因為要先確認 DBGEN 內容與 ta-server 可達性才能設計切點。

### D7. BLOB 落到 `/srv/gimc/blobs/` 檔案系統，DB 只存 `raw_data_path`

`MSDATA.DATA`（原始質譜）、`GCDATA.pic`、`MPSUDATA.pic`、`ENZYME.pic` 是不會出現在 WHERE 子句的大 BLOB。塞進 PostgreSQL `bytea` 會把 heap 撐大、拖慢 vacuum；用 large object 沒有相對的好處。慣例：`/srv/gimc/blobs/{msms,gcms,enzyme,mpsu}/{sampleno_or_uuid}.{bin,jpg}`。備份依靠檔案系統層級 snapshot（與 PG 備份視窗一致）。

### D8. Alembic 啟用 `include_schemas=True`，`alembic_version` 放 `public`

- 整個專案一個 alembic root。`target_metadata` 是 `main`、`external`、`nbs`、`links`、`ref` 五份 MetaData 的聯集。
- `alembic_version` 在 `public`、追蹤統一的 migration 歷史 — 把 migration 包進 PostgreSQL 的 transactional DDL，可以保證跨五個 schema 的 schema 變更原子性。
- **考慮過的替代方案 — 一個 schema 一個 alembic root**：駁回，因為這會切割 migration 歷史，使跨 schema 的協同變更（例如同一次給 `main.patient` 與 `external.patient` 加同名欄位）很難寫。

### D9. `data_loader` 由 env var 選擇後端、回傳形狀完全相同

`backend/shared/shared/data_loader.py` 變成 facade：

```python
def load_all() -> dict[str, dict[str, list[dict]]]:
    if os.getenv("GIMC_DATA_BACKEND", "json") == "postgres":
        return _load_from_pg()
    return _load_from_json()
```

兩個後端回傳同樣的 `{schema: {table: [rows]}}`，row 是純 dict，key 為 camelCase（與 `schemas.py` 一致）。Postgres 路徑用我們已有的 model 走 SQLAlchemy 查詢、把 `Row._mapping` 轉成 dict 在邊界輸出。**Service 不需要改。** 這就是 mock 世界與真實世界的唯一接縫。

## Risks / Trade-offs

- **[pgloader 在型別轉換的邊界 case]** → 緩解：`post_pgloader.sql` 重新指定特定欄位的型別（`patient_id` 透過 `USING patient_id::uuid` → UUID），verify §3（patient identity round-trip）會立刻抓到誤轉的 UUID。
- **[1.0 BLOB 透過 mdbtools 抽取在極大紀錄上可能失敗]** → 緩解：先跑 pre-flight 腳本統計 BLOB 欄位的數量與大小；若有紀錄超過 Access 的怪癖，退回原 ASP.NET 應用程式的匯出途徑。BLOB 無論如何都落在檔案系統。
- **[跨 schema link 沒有 FK 強制]** → 緩解：INSERT trigger 驗證 `patient_id_a/b` 至少存在於某個 patient 表；夜間 audit 查詢回報 orphan。
- **[一個跨三個 MVP 的大 change 比三個小 change 難 review / revert]** → 緩解：`tasks.md` 依 MVP 分割；每個 MVP 結尾是一個可驗證的檢查點（MVP-1 = 真實資料可查；MVP-2 = 模組覆蓋齊全；MVP-3 = 舊系統退役）。Reviewer 可以先看 MVP-1 並依此分段審。
- **[`data_loader.load_all()` 目前回傳整份資料；對大 PG 表全載很浪費]** → 緩解：JSON 開發模式下保留這個 API（mock 資料量有限）；Postgres 後端只在跑 spec 測試網時才會全載。Production 的 gateway / service 已經查特定端點；它們之後會改用查詢形狀化的方法（不在本 change 範圍內，但已列入後續追蹤）。
- **[單一 DB 故障會帶走五個 schema]** → 可接受：當年舊系統分多個 DB 是為了解 MySQL 的 namespace 問題，不是可用性問題；3.0 用單一 PG instance 是最簡單的運維模型。Standby replica 列入後續。
- **[asyncpg（service）與 psycopg（ETL）的 driver 版本飄移]** → 可接受：ETL 是一次性腳本，跑在固定版本的環境；service 自己有 pinning。Runtime 兩者沒有共享狀態。

## Migration Plan

1. 部署 PostgreSQL 16 instance；建立 `gimc` DB（`ENCODING UTF8`、ICU collation）；建立五個 schema。
2. 套用 Alembic baseline（MVP-1 model 集合：`patient` + 7 張核心 sample 表 × 3 個 schema + `links`）。
3. 跑 `pgloader` 2.0 → 3.0（三次）；套用 `post_pgloader.sql`。執行 verify §1、§2、§3。
4. 在 staging 環境設 `GIMC_DATA_BACKEND=postgres`；跑 mock-parity 回歸（`dbsLysoGb3 > 5` 模板）與 API smoke（`/api/patient-detail/<uuid>`）。
5. 推進到 MVP-2：加上疾病模組與 NBS 模組、跑 1.0 `gene.mdb` ETL 並 upsert 合併、灌入 `ref` schema、上線 `GcmsRecord` + `main.gcms` + svc-lab route、加寬 `gag` 欄位。
6. 推進到 MVP-3：在確認 DBGEN 內容與網路後跑其 ETL；補完 `MPSUDATA` 整個 panel 進 `gag`；把 1.0 / 2.0 切換到唯讀；正式把 3.0 流量導到 Postgres 後端。

**Rollback**：每個 MVP 階段是一組獨立的 migration。`data_loader` 隨時可以回到 `GIMC_DATA_BACKEND=json`（service 照樣運作）。Schema 層級的 rollback 用 `alembic downgrade <rev>`。ETL 是一次性 — 重跑是冪等的（`ON CONFLICT (patient_id) DO UPDATE`），失敗的匯入修好後可重跑、不需要人工清理。檔案系統 BLOB 寫入以 sample id 內容定位，重跑會 overwrite 同樣的路徑。

## Open Questions

- DBGEN 的內容範圍：哪些表的資料不在 2.0 或 `gene.mdb` 裡？需要在 MVP-3 ETL 設計前釐清。
- Collation 選擇 — `und-x-icu` 與 `zh-x-icu` 哪個對既有 patient-search UI 的排序更好？需用真實 chartno + 姓名語料 benchmark。
- `COMMAND`（判讀片語）的參考表語意：是 per-test 還是全域？影響 `command_phrase` 該放在 `ref` 還是各 sample 表旁。
- Gateway 連線池規模：目前 5/10 是以 4 個 service 估的；MVP-3 若加第 5 個 service 要重新評估。
