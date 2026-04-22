## 0. Branch & Workflow

- [x] 0.1 從 `main` 拉新分支 `feat/restructure-mockdata-for-api`
- [x] 0.2 確認本機 Node + Python 環境可跑（`node -v`, `python3 --version`）

## 1. Backend mock data scaffold（commit: chore + feat * 5）

- [x] 1.1 建立目錄 `backend/mock-data/{db_main,db_external,db_nbs}/` 與 `backend/scripts/`，加 `.gitkeep`（commit: `chore(mock): scaffold backend/mock-data directory structure`）
- [x] 1.2 撰寫 `backend/scripts/generate_mock.py`：(a) 內嵌 main DB 5 位現有病人 + sample 資料 (b) 內嵌 external DB 3 筆 + samples (c) 內嵌 NBS DB 5 筆 + samples 含 sub-tables (d) 用 `uuid5(NAMESPACE_OID, f"{source}:{naturalKey}")` 產 `patientId` 與 sample row id (e) 寫出全部 JSON 檔（commit: `feat(mock): add deterministic UUID v5 generator script`）
- [x] 1.3 跑 `python backend/scripts/generate_mock.py` 產出 `db_main/*.json`（14 檔，含 patient 與 13 sample tables）（commit: `feat(mock): add db_main JSON seed (patient + 13 tables)`）
- [x] 1.4 跑 generator 產出 `db_external/*.json`（9 檔）（commit: `feat(mock): add db_external JSON seed`）
- [x] 1.5 跑 generator 產出 `db_nbs/*.json`（13 檔，含 cah_tgal、dmd_tsh sub-tables）（commit: `feat(mock): add db_nbs JSON seed (incl. sub-tables)`）
- [x] 1.6 撰寫 `backend/scripts/load_mock.py`：load_all() API，FK 驗證（每個 sample 的 patientId 必須在 patient.json 找得到；cah_tgal.cahId / dmd_tsh.dmdId 必須在 parent table 找得到），並印 row counts（commit: `feat(mock): add load_mock.py FK validator`）
- [x] 1.7 執行 `python backend/scripts/load_mock.py`，確認所有 FK 通過、無 dangling reference

## 2. Frontend type extensions（commit: feat * 2）

- [x] 2.1 修改 `frontend/src/types/medical.ts`：Patient 介面加 `patientId`、`source`、`externalChartno?`、`nbsId?`、`category?`、`linkedPatientIds?`；`chartno`、`diagnosis` 改 optional（commit: `feat(types): extend Patient with patientId/source/optional chartno`）
- [x] 2.2 在同檔加 5 個新 ModuleId、5 個 Sample 介面（含 TgalSubSample、TshSubSample）、5 個 MODULE_FIELDS 條目、5 個 MODULE_DEFINITIONS 條目；ModuleInfo['group'] union 加入 `'nbs'`（commit: `feat(types): add NBS module types and field defs`）
- [x] 2.3 執行 `cd frontend && npx tsc --noEmit`，確認 type check clean（此時 mockData.ts 仍是舊版，可能會 fail — 沒關係，下一節會修）

## 3. Frontend mockData loader rewrite（commit: refactor * 1）

- [x] 3.1 改寫 `frontend/src/data/mockData.ts`：用 Vite JSON import 載入 `../../../backend/mock-data/db_main/*.json`、`db_external/*.json`、`db_nbs/*.json`；以 `patientId` 為 key 把 sample 表 join 回 nested Patient 物件；`mockPatients: Patient[]` export 名稱與 shape 不變（commit: `refactor(mockdata): replace inline data with JSON join loader`）
- [x] 3.2 確認 `tsconfig.app.json` 已開 `resolveJsonModule`（多數 Vite template 預設開）；若沒開則加上
- [x] 3.3 執行 `npx tsc --noEmit && npm run build`，必須 clean

## 4. UI handle nullable chartno（commit: fix * 1）

- [x] 4.1 `frontend/src/components/PatientSummary.tsx`：所有顯示 `patient.chartno` 的位置改為 `patient.chartno ?? patient.externalChartno ?? patient.nbsId ?? '—'`
- [x] 4.2 `frontend/src/pages/Index.tsx`：(a) 搜尋 filter 在 `name`/`chartno` 之外也比對 `externalChartno`、`nbsId` (b) `results.map` 與 `displayPatient` 用 `patientId` 為 key
- [x] 4.3 `frontend/src/components/ConditionResults.tsx`：`<TableRow key={patient.chartno}>` 改為 `key={patient.patientId}`
- [x] 4.4 commit: `fix(ui): handle nullable chartno with externalChartno/nbsId fallback`

## 5. UI render NBS modules（commit: feat * 1）

- [x] 5.1 `frontend/src/components/ResultModules.tsx`：依現有 `aadc`/`ald` pattern 加 5 個新 section（bd、cah、dmd、g6pd、smaScid）
- [x] 5.2 在 `cah` section 內，對每個 cah row 渲染 `tgal?: TgalSubSample[]` 為 nested rows（length === 0 時不顯示）
- [x] 5.3 在 `dmd` section 內，對每個 dmd row 渲染 `tsh?: TshSubSample[]` 為 nested rows（length === 0 時不顯示）
- [x] 5.4 commit: `feat(ui): render NBS modules in ResultModules`

## 6. UI condition query support for NBS（commit: feat * 1）

- [x] 6.1 `frontend/src/components/ConditionResults.tsx`：在 `getModuleData()` switch 加 5 個 case（bd、cah、dmd、g6pd、smaScid）回傳對應陣列
- [x] 6.2 `frontend/src/pages/Index.tsx`：在 `tabModuleMap` 加入 `nbs: ['bd', 'cah', 'dmd', 'g6pd', 'smaScid']`，並在 Tabs UI 渲染 'nbs' tab
- [x] 6.3 commit: `feat(ui): support NBS modules in condition query`

## 7. Verification

- [x] 7.1 `cd frontend && npx tsc --noEmit` clean
- [x] 7.2 `npm run lint` clean（或維持與 main 相同的 baseline，不引入新 warning）
- [x] 7.3 `npm run build` 成功
- [x] 7.4 `npm run test` 通過（既有 vitest 測試）
- [x] 7.5 `python backend/scripts/load_mock.py` exit 0、所有 FK OK
- [ ] 7.6 `npm run dev` 啟動後手動煙霧測試：
    - [ ] 7.6.1 搜尋「陳志明」→ 出現
    - [ ] 7.6.2 搜尋 NBS 病人姓名 → 出現
    - [ ] 7.6.3 搜尋 external 病人 `externalChartno` → 出現
    - [ ] 7.6.4 condition template「Biomarker 異常」→ 命中數與 main 分支相同
    - [ ] 7.6.5 新 condition `bd / biotinidaseActivity < 5` → 命中 NBS 紀錄
    - [ ] 7.6.6 切換到 'nbs' tab → 只顯示 5 個 NBS 模組
    - [ ] 7.6.7 開啟一位有 cah+tgal 資料的病人 → tgal 渲染為 cah 下方 nested rows

## 8. Pull request

- [x] 8.1 推上分支：`git push -u origin feat/restructure-mockdata-for-api`
- [x] 8.2 用 `gh pr create` 開 PR，body 引用本 change：`See openspec/changes/restructure-mockdata-for-db-alignment/`
- [ ] 8.3 PR 通過 CI（lint、type-check、build、test、e2e、load_mock）後 merge
- [ ] 8.4 Merge 後執行 `/opsx:archive restructure-mockdata-for-db-alignment` 歸檔
