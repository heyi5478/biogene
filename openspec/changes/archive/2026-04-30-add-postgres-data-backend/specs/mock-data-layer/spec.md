## ADDED Requirements

### Requirement: data_loader SHALL 支援由 GIMC_DATA_BACKEND 切換的 PostgreSQL 後端

`backend/shared/shared/data_loader.py` MUST 尊重環境變數 `GIMC_DATA_BACKEND`，值為 `json`（預設）或 `postgres`。`data_loader` 對外的兩個函式（`load_all` 與 `validate`）MUST 行為如下：

- 當 `GIMC_DATA_BACKEND` 未設定或為 `json`：行為 MUST 與目前 mock-data-layer 的 JSON 行為位元等價（既有 requirement 完全不變、繼續適用）。
- 當 `GIMC_DATA_BACKEND=postgres`：`load_all()` MUST 回傳同形狀的 dict（`dict[str, dict[str, list[dict]]]`，key 為 schema/table，row 為 camelCase dict 且 key 與 `schemas.py` 一致）；`validate()` MUST 對 PostgreSQL 資料庫執行 FK 驗證查詢，失敗時以相同訊息契約拋出 `ValueError`。

四個 FastAPI service（`gateway`、`svc-patient`、`svc-lab`、`svc-disease`）MUST 完全比照今日呼叫 `data_loader`，且 MUST NOT 在自己程式碼裡加上後端相關分支。後端切換 MUST 完全在 `data_loader.py` 內部完成。

#### Scenario: 同一 patientId 在跨後端時得到相同回應形狀

- **WHEN** 同一 anchor `patientId` 透過 `GET /patients/{patientId}` 先以 `GIMC_DATA_BACKEND=json` 請求一次，再以 `GIMC_DATA_BACKEND=postgres` 請求一次（且 DB 已透過 `seed_from_json.py` 灌入同一份 mock 資料）
- **THEN** 兩次回應 body MUST 具有相同的 JSON 鍵集
- **AND** `patientId`、`name`、`birthday`、`sex`、`chartno` 的值 MUST 完全相同

#### Scenario: 切換後端時 service 程式碼不變

- **WHEN** 操作員把 `GIMC_DATA_BACKEND` 由 `json` 改為 `postgres` 並重啟四個 service
- **THEN** `backend/gateway/`、`backend/svc-patient/`、`backend/svc-lab/`、`backend/svc-disease/` 下的原始檔在前後兩次跑時 MUST 位元相等
- **AND** 服務 MUST 順利啟動並讓 `/health` 回 200

#### Scenario: PostgreSQL 後端的 validate() 在 FK violation 時拋出有型例外

- **WHEN** `main.aa` 中故意注入懸空 `patient_id`、且 `GIMC_DATA_BACKEND=postgres`
- **AND** 由某 FastAPI service 的 lifespan 啟動呼叫 `validate()`
- **THEN** MUST 拋出 `ValueError`，訊息 MUST 標出 schema（`main`）、table（`aa`）、冒犯的 `patient_id`
- **AND** Service MUST 拒絕啟動（lifespan 啟動將例外往外傳）

#### Scenario: GIMC_DATA_BACKEND 預設值為 json

- **WHEN** `GIMC_DATA_BACKEND` 未設定且 service 呼叫 `load_all()`
- **THEN** 該函式 MUST 從 `backend/mock-data/` 讀 mock 資料，行為與今日完全相同
- **AND** MUST NOT 嘗試開 PostgreSQL 連線
