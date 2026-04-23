## Why

前端 `Patient` TypeScript 型別要求 `opd: OpdRecord[]`，但後端骨架（`add-fastapi-microservices-skeleton`）漏掉 opd：

- `svc-patient` 只載 `patient.json`，未處理 `opd.json`
- `svc-lab` / `svc-disease` 不 own opd
- `shared.schemas.PatientBundle` 沒有 `opd` 欄位
- `gateway` 也沒 fan-out 至任何 opd 端點

結果：`GET /patients` 的每筆回應都缺 `opd` key，前端 `PatientSummary.tsx:59` 讀 `patient.opd.length` 執行期 TypeError，導致 `wire-index-page-to-api` 合入後病人搜尋畫面空白。

依 `wire-index-page-to-api` 的 design doc：「發現漂移時應於 `backend/shared/schemas.py` 修，而非前端 workaround」，此 change 於後端補齊。

## What Changes

- `backend/shared/shared/schemas.py`：
  - 新增 `OpdRecord`（對齊前端 `OpdRecord` type：`visitDate` / `sex` / `birthday` / `diagCode` / `diagName` / optional `subDiag1` / optional `subDiag2`，加上 `patientId`）
  - 新增 `OpdBundle { opd: list[OpdRecord] = [] }`，與 `LabBundle` / `DiseaseBundle` 形狀對稱
  - `PatientBundle` 加 `opd: list[OpdRecord] = []`
- `backend/svc-patient/svc_patient/app.py`：
  - 啟動時額外載入 `db_{main,external,nbs}/opd.json`，建 `_opd_by_id` 索引
  - 新增 `GET /opd/{patient_id} → OpdBundle`
  - 新增 `POST /opd/batch { patientIds: [...] } → dict[str, OpdBundle]`（與 svc-lab / svc-disease batch 對稱）
- `backend/gateway/gateway/app.py`：
  - `GET /patients`：於 `asyncio.gather` 併發多加一路 `svc-patient /opd/batch`
  - `GET /patients/{id}`：於 `asyncio.gather` 併發多加一路 `svc-patient /opd/{id}`
  - `_merge_bundle` 簽章多吃 `opd: dict`

## Capabilities

### Modified Capabilities

- `backend-api`：新增「`PatientBundle` 必含 opd 陣列」與「svc-patient 擁有 opd 批次／單筆端點」兩項 requirement；既有 gateway aggregation 行為不變

## Impact

- **修改檔案**：`backend/shared/shared/schemas.py`、`backend/svc-patient/svc_patient/app.py`、`backend/gateway/gateway/app.py`
- **不動**：`svc-lab`、`svc-disease`、`backend/mock-data/*`、前端任何檔案
- **相容性**：`PatientBundle` 新欄位預設 `[]`；既有消費者（前端）可直接讀 `.opd`，第三方消費者忽略未知欄位無感
- **驗證**：`curl -s http://localhost:8000/patients` 每筆必含 `opd` key；前端 `PatientSummary` 能正常渲染 `.opd.length`
- **風險**：gateway 多一次 fan-out（svc-patient `/opd/batch`），對 in-memory 查詢 latency 可忽略
