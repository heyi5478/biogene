## Context

目前 mock data 是 [frontend/src/data/mockData.ts](../../../frontend/src/data/mockData.ts) 中的單一扁平 `Patient[]`，5 位假病人，所有檢驗結果都 nested 在 patient 物件下。後端 [PLAN.md](../../../PLAN.md) 規劃用 4 個 FastAPI microservices 連 3 個外部 MySQL 資料庫（`2.0`、`2.0 外院資料庫`、`new_born_screening`），多 table 名稱重疊但語意各自獨立。後端開發初期不接真實 DB，會先讀 mock；同時前端 UI 要持續可用、未來換成真 API 時 `Patient` shape 不變、無痛切換。

**現況約束：**
- 5 位假病人邏輯仍要保留，避免破壞現有 condition templates 與 e2e 測試。
- React Query 已安裝但未使用 — 切換到 API 是後續 change 的事，本次 mock data 仍由 frontend bundle 載入。
- 1 GB RAM VM 限制 — Python load_mock 必須輕量（標準庫即可，不引入 Pandas）。
- 本次不動 `vite.config.ts`、不動 `evaluateConditions` 演算法本體。

**關鍵實作脈絡：**
- [Patient](../../../frontend/src/types/medical.ts#L26-L47) 是核心型別；變動會擴散到所有讀 `patient.<moduleId>` 的元件。
- [evaluateConditions](../../../frontend/src/components/ConditionResults.tsx) 用 switch + `getModuleData()` 讀 sample 陣列；新增模組需在此加 case。
- [MODULE_FIELDS](../../../frontend/src/types/medical.ts#L387-L546) 與 [MODULE_DEFINITIONS](../../../frontend/src/types/medical.ts#L171-L284) 是 ConditionBuilder UI 的 metadata 來源。

## Goals / Non-Goals

**Goals:**
- Mock data 對齊真實 3-DB schema，**一個 table 一個 JSON**，後端可逐表載入。
- 引入 `patientId` (UUID v5, deterministic) 為主鍵；所有 sample 表用 `patientId` FK。
- 補齊 NBS 5 個專屬模組（含 sub-tables）的型別、UI、條件查詢支援。
- 既有 5 位 main DB 病人保留 chartno、保留現有 sample 內容 → 既有條件查詢命中數**不應**變動。
- 前端 `mockPatients: Patient[]` export 名稱與 shape 不變 → 元件 import 不需改（除型別擴充以外）。
- 後端 Python 用標準庫即可載入並驗證 FK。

**Non-Goals:**
- ❌ 不實作 FastAPI 服務本身（屬於 [PLAN.md](../../../PLAN.md) Step 5–6 的後續 change）。
- ❌ 不實作 Vite proxy / `src/lib/api.ts` / React Query hooks（後續 change）。
- ❌ 不實作跨 DB patient linkage / MPI（保留 `linkedPatientIds: string[]` 欄位但本次不填）。
- ❌ 不重構 `evaluateConditions` 為後端化（Phase 3 的事）。
- ❌ 不為 sub-tables (`tgal`, `tsh`) 加 ConditionBuilder 欄位（UI 只當 sub-rows 顯示）。
- ❌ 不對外院 / NBS 5 位以外的 mock data 做大量編造，每個 DB 約 3–5 筆代表性資料即可。

## Decisions

### D1. JSON 拆檔粒度：一個 table 一個 JSON
- **選擇**：`backend/mock-data/{db_main,db_external,db_nbs}/<table>.json`，每檔是該 table 的 JSON array。
- **理由**：對齊真實 schema、microservice 可選擇性載入、單檔 diff 友善、新增模組門檻低。
- **替代**：每個 DB 一個 JSON 把所有 table 包進去 → 載入時要 parse 整包、所有 service 都吃同一份；棄。

### D2. `patientId` 用 deterministic UUID v5
- **選擇**：`uuid5(NAMESPACE_OID, f"{source}:{naturalKey}")`，naturalKey 為 `chartno` / `externalChartno` / `nbsId`。
- **理由**：mock 重新產生時 ID 不變，FK 不會斷；不需要 DB sequence；script 可離線執行。
- **替代**：(a) UUID v4 隨機 → 每次重產 FK 都會碎；(b) 直接用 chartno → 外院/NBS 沒有；棄。

### D3. FK 由 `patientId` 維繫，不再用 `chartno`
- **選擇**：所有 sample table row 帶 `patientId` 欄位；`patient.json` 也帶 `patientId`。
- **理由**：chartno 在外院/NBS 為 null，無法當 FK；統一用 UUID 簡化 join 邏輯。
- **替代**：每個 DB 用各自的「主鍵」（chartno / externalChartno / nbsId）→ join 邏輯要寫三套；棄。

### D4. 跨 DB patient 暫不連結
- **選擇**：同一人在 `db_main` 與 `db_nbs` 視為兩個獨立 patient（不同 patientId）。`Patient` 預留 `linkedPatientIds: string[]`，本次預設 `[]`。
- **理由**：真實連結需要 MPI 或機率比對，超出 mock 範圍；先以 forward-compat 欄位保留接口。
- **替代**：硬連結（手工指定）→ 假資料無意義且誤導；棄。

### D5. 保留 `Patient` 為 nested arrays（不 flatten）
- **選擇**：JSON 是扁平的（每 table 一檔），但 frontend `mockData.ts` 在 load 階段 join 回 nested `Patient` 物件，沿用既有 shape。
- **理由**：`evaluateConditions`、`PatientSummary`、`ResultModules` 都靠 `patient.<moduleId>` 取陣列；flatten 會擴散修改到 4 個檔案無對應收益。
- **替代**：直接 export flat tables，重構所有消費者 → 大幅增加 change 範圍與風險；棄。

### D6. NBS sub-tables（tgal、tsh）只顯示，不查詢
- **選擇**：`tgal`、`tsh` 在型別中以 `cah.tgal?: TgalSubSample[]` / `dmd.tsh?: TshSubSample[]` 表達；ResultModules 渲染為 nested rows；**不**進入 `MODULE_FIELDS` / `MODULE_DEFINITIONS` / ConditionBuilder。
- **理由**：sub-table 是「同一筆檢驗的後續加驗」，UI 語意應跟父表綁定；條件查詢場景目前無需求。
- **替代**：列為獨立 ModuleId → ConditionBuilder 多兩個欄位但臨床語意混亂；棄。

### D7. NBS 模組欄位以最小可行 schema 起步
- **選擇**：每個 NBS 模組只放 1–2 個關鍵 analyte（bd: biotinidaseActivity / cah: ohp17 / dmd: ck / g6pd: g6pdActivity / sma_scid: smn1Copies + trec），加上 `sampleId`、`collectDate`、`result`。
- **理由**：mock 階段不需要全參考區間；之後接真 DB 時用真 schema 取代。
- **替代**：照公開 NBS panel 完整 reference 補齊 → 過早投資且資料容易誤導；棄。

### D8. JSON 載入策略：Vite import + 啟動時 join
- **選擇**：`mockData.ts` 用 Vite 的 JSON import (`import x from '...../*.json'`) 載入所有 36 個 JSON，然後在 module top-level 做一次 `patientId` join，輸出 `mockPatients`。
- **理由**：Vite 原生支援 JSON import、type-safe（搭配 `resolveJsonModule`）、無 runtime fetch 成本。
- **替代**：runtime fetch JSON → 增加 async 處理、與後續 React Query 切換時程衝突；棄。

### D9. 後端 load_mock 用標準庫 + dataclass
- **選擇**：`backend/scripts/load_mock.py` 用 `json` + `pathlib` + `dataclasses` 實作；提供 `load_all() -> dict[str, dict[str, list[dict]]]` API。
- **理由**：1 GB RAM 約束下避免引入 Pandas；FastAPI service 之後可在 startup 直接 import 此模組。
- **替代**：用 Pydantic v2 model 直接驗證 → 等到 svc-* 真正建立時再做（屬下個 change）。

### D10. Generator 從現有 mockData.ts 取種子
- **選擇**：`generate_mock.py` 不從 TS 動態解析；改為**手動將現有 5 位病人資料整理為 Python dict literal** 寫在腳本中，配上 NBS / external 範例資料，跑一次產出所有 JSON。
- **理由**：避免引入 ts 解析器；mock data 變動少，手動維護成本低。
- **替代**：寫 ts → json 編譯流程 → overkill。

## Risks / Trade-offs

- **R1**: JSON join 邏輯錯誤（漏 patientId 對應、欄位 typo）→ 既有條件查詢結果與既有 5 位病人不一致 → **Mitigation**: tasks.md 中的驗證步驟「跑既有 condition templates 比對命中數」必須與當前 main 一致；`load_mock.py` 在 CI 中也跑一次 FK 驗證。
- **R2**: `Patient` 型別變動讓未列入修改清單的元件 type-check fail → **Mitigation**: `npx tsc --noEmit` 強制 clean；發現非預期受影響檔案則更新 tasks.md。
- **R3**: NBS sub-table 資料量稀少時 UI 出現空 section → **Mitigation**: ResultModules 對 `cah.tgal` / `dmd.tsh` 加 `length === 0` guard，不顯示空表頭。
- **R4**: 外院 / NBS 病人沒 chartno 時，原本以 chartno 為 React key 會出現 collision → **Mitigation**: 全面改用 `patientId` 為 key（D3 已涵蓋）；tasks.md 列為獨立 commit。
- **R5**: Generator 與 JSON 不同步（手動編輯 JSON 後 generator 規格沒跟著動）→ **Mitigation**: Generator 設計為「重跑必須完全覆蓋現有 JSON」；變更 mock 資料一律改 generator 而非 JSON。
- **R6**: Vite JSON import 對 36 檔的 cold-start 開銷 → 實測前不確定。**Mitigation**: 若 dev server 啟動明顯變慢（> 3s），改為 `import.meta.glob` 動態載入。

## Migration Plan

mock data 是 internal seed，無線上資料，**不需要回滾策略**。實作順序：

1. 在新分支 `feat/restructure-mockdata-for-api` 上開發。
2. 依 tasks.md 的 commit 拆分順序執行（每個 commit 都應 build pass）。
3. PR 開出後 review；merge 進 main 後，PLAN.md Step 5–6 的後續 change 即可消費此 mock。
4. 若實作中發現 type 變動波及未列入清單的檔案 → 暫停、更新 tasks.md、補 commit。

回滾路徑：mock data 與型別變動皆封閉在前端 + `backend/mock-data/`，PR revert 即可完整回到變動前狀態。

## Open Questions

- **Q1**: NBS `category`（nbs / self_pay / opd_case）在 UI 上是否需要 filter？本次先存欄位但不在 FilterPanel 上顯示，待 product 確認。
- **Q2**: 外院病人的 `name` 是否要去識別化？mock 資料先用「外院001」之類的代號，避免與 main DB 真實名稱混淆。
- **Q3**: `MODULE_DEFINITIONS` 的 `'nbs'` group 的 icon 與顯示順序？暫沿用既有 `'lab'` 風格，待設計確認。
