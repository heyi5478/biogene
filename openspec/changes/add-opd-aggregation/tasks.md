## 1. Schema

- [x] 1.1 `backend/shared/shared/schemas.py` 新增 `OpdRecord`（`patientId` + `visitDate` + `sex` + `birthday` + `diagCode` + `diagName` + 可選 `subDiag1` / `subDiag2`）
- [x] 1.2 新增 `OpdBundle { opd: list[OpdRecord] = [] }`
- [x] 1.3 `PatientBundle` 加 `opd: list[OpdRecord] = []`
- [x] 1.4 `__all__` 補 `OpdRecord`、`OpdBundle`

## 2. svc-patient

- [x] 2.1 docstring 更新：「serves merged patient base records **and opd visit history**」
- [x] 2.2 啟動 lifespan 內額外載入三個 DB 的 `opd.json`，建 `_opd_by_id` 索引（defaultdict）
- [x] 2.3 新增 `GET /opd/{patient_id}` → `OpdBundle`
- [x] 2.4 新增 `POST /opd/batch` → `dict[str, OpdBundle]`
- [x] 2.5 log 訊息包含 opd 載入筆數

## 3. gateway

- [x] 3.1 `_merge_bundle` 簽章加 `opd: dict` 參數
- [x] 3.2 `GET /patients` 於 `asyncio.gather` 多加一路 `svc-patient /opd/batch`
- [x] 3.3 `GET /patients/{id}` 於 `asyncio.gather` 多加一路 `svc-patient /opd/{id}`，null 檢查後對應 502

## 4. 驗收

- [x] 4.1 `backend/.venv/bin/python -c "from shared.schemas import PatientBundle, OpdRecord, OpdBundle"` 可 import
- [x] 4.2 `curl -s http://127.0.0.1:8000/patients` 每筆含 `opd` key；13 筆中至少一筆 `opd` 非空（陳志明：3 筆、林雅婷：2 筆、張偉翔：4 筆）
- [x] 4.3 `curl -s http://127.0.0.1:8000/patients/4e645243-fe58-5f74-b0bf-4271b5fdc0bf` 含 `opd`
- [x] 4.4 前端 `PatientSummary` 能渲染，不再出現 `Cannot read properties of undefined (reading 'length')`
- [x] 4.5 `openspec validate add-opd-aggregation --strict` 通過
