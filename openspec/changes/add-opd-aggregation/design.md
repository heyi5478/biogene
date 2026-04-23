## Context

微服務骨架（`add-fastapi-microservices-skeleton`）建立了 `svc-patient`（患者基本）、`svc-lab`（AA/MSMS/biomarker/outbank/dnabank）、`svc-disease`（NBS + 疾病模組）三個下游。opd（門診紀錄）既非 lab 也非 disease，當時從三個 service 都未被 own，同時 `PatientBundle` schema 亦未納入 opd 欄位。

`wire-index-page-to-api` 合入後，前端 `PatientSummary` 依契約讀 `patient.opd.length`，觸發 runtime 錯誤，暴露此空缺。

## Goals / Non-Goals

**Goals**

- 補齊 `PatientBundle.opd`，讓 `GET /patients` 回應對齊前端契約
- 維持既有微服務拓樸：不新增 service、不破壞既有端點

**Non-Goals**

- 不改 CORS 預設值（另一處遺留；Vite 實際 port 為 8080 而非預設的 5173，值得另開 change）
- 不動前端；本 change 刻意採「後端補足、前端無 workaround」
- 不處理 opd 的 write / mutation（目前仍為唯讀）

## Decisions

### 決策 1：opd 歸屬 svc-patient

**選擇：由 svc-patient 擁有 opd**

理由：

- opd 是患者門診紀錄，屬於臨床基本歷程，與 patient 基本資料耦合度高
- 與 lab／disease（分析結果）語意不同，放進 svc-lab 會讓 service 邊界模糊
- svc-patient 的 `data_loader.load_all()` 已讀三個 DB，再抓 `opd.json` 幾乎零成本
- 避免為單一 table 新起 svc-opd（違反 YAGNI）

### 決策 2：Bundle 形狀沿用 `LabBundle` / `DiseaseBundle` pattern

svc-patient 的 `/opd/{id}` 回 `OpdBundle { opd: [...] }`；batch 回 `dict[patientId, OpdBundle]`。

理由：

- gateway 的 `_merge_bundle` 以 `{**patient, **opd, **labs, **diseases}` flat merge — bundle 必須是 dict 才能直接 spread
- 與 svc-lab / svc-disease 對稱，gateway 程式碼保留平行結構

### 決策 3：Gateway fan-out 併發新增一路

`GET /patients` 內 `asyncio.gather(opd_task, labs_task, diseases_task)` — 三路並行，critical path 由 max 決定，不因新增 opd 拉長。

## Risks / Trade-offs

- **風險：opd schema 漂移** — `_Base` 既設 `extra='ignore'`，JSON 新增欄位不會破既有消費者；新增必填欄位才需同步更新前後端
- **Trade-off：svc-patient 同時 own 兩類資料**（基本資料 + opd）— 可接受：兩者同屬病人 level 核心；未來若 opd 量體暴增再切出新 svc

## Migration Plan

1. 本地：後端四服務 `--reload` 自動重啟後，`curl /patients` 驗每筆 `opd` 存在
2. PR 合入 main
3. 若任何下游因 opd 缺漏做了 workaround（目前已知無），合入後可移除

Rollback：revert PR；但前端 `PatientSummary` 仍假設 `opd` 存在會再度破，需同時處理。

## Open Questions

- CORS 預設 origin 是否應同步改為 `http://localhost:8080`（Vite 實際 port）？—— 本 change 不動，建議另開一個小 change 處理。
