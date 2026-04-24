# Genetic Medicine Integrated Query Center

Internal medical information system that lets geneticists search patient data across 14 data modules (basic info, OPD, AA, MS/MS, Biomarker, LSD, Enzyme, GAG, DNAbank, Outbank, AADC, ALD, MMA, MPS2) using two query modes: **patient query** and **condition query**. The frontend is a Vite + React SPA; the backend is a FastAPI microservice architecture that aggregates results from three internal services behind a single gateway.

## Architecture

```
Browser (Vite dev server, :8080)
        │
        ▼
┌──────────────────┐      ┌───────────────┐
│ gateway  :8000   │──────▶ svc-patient   │  :8001
│  (BFF / CORS /   │──────▶ svc-lab       │  :8002
│   aggregation)   │──────▶ svc-disease   │  :8003
└──────────────────┘      └───────────────┘
```

- The browser only talks to `gateway`; `gateway` fans out to the three internal services via `httpx.AsyncClient`.
- Internal services never call each other — all aggregation happens in `gateway`.
- Internal services have no CORS middleware, so direct browser calls are blocked by design.
- In the development environment, JSON files under `backend/mock-data/` are the data source. At startup, `shared.data_loader.validate()` walks the mock data and checks FK integrity; on failure the service logs the offending row and exits non-zero before binding its port.

## Project Layout

```
my-project/
├── frontend/           # Vite + React 19 + TypeScript + Tailwind + shadcn/ui
├── backend/
│   ├── gateway/        # Frontend-facing entry point (:8000)
│   ├── svc-patient/    # Patient base records (:8001)
│   ├── svc-lab/        # Lab results + specimens (:8002)
│   ├── svc-disease/    # Disease-project modules (:8003)
│   ├── shared/         # Shared Pydantic schemas / data_loader
│   ├── mock-data/      # Dev-time seed JSON
│   └── scripts/        # dev.sh, load_mock.py
├── openspec/           # Change proposals and specs (OpenSpec workflow)
├── PLAN.md             # Initial architecture and implementation plan
└── genetic_medicine_search_page_spec_v2_with_mermaid.md  # Feature spec
```

## Quick Start

Requirements: Python 3.10+, Node.js (or Bun).

### 1. Start the backend

From the repo root, create a venv and install all four services as editable packages:

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -U pip
pip install -e backend/shared \
            -e backend/gateway \
            -e backend/svc-patient \
            -e backend/svc-lab \
            -e backend/svc-disease
```

Launch all four services at once (`Ctrl-C` propagates to every child):

```bash
bash backend/scripts/dev.sh
```

### 2. Start the frontend

```bash
cd frontend
npm install       # or: bun install
npm run dev       # Vite serves http://localhost:8080
```

The frontend reads `VITE_API_BASE_URL` to locate the gateway. The default `http://localhost:8000` lives in `frontend/.env.development`. To override per machine, copy `frontend/.env.example` to `frontend/.env.local`.

### 3. ⚠️ CORS gotcha

The gateway's `GATEWAY_CORS_ORIGIN` defaults to `http://localhost:5173`, but the Vite dev server actually runs on `8080`. You must override the env var before starting the gateway, or browser calls will be blocked:

```bash
export GATEWAY_CORS_ORIGIN=http://localhost:8080
bash backend/scripts/dev.sh
```

## Smoke Tests

```bash
# gateway healthcheck
curl -s http://localhost:8000/healthz

# full patient list
curl -s http://localhost:8000/patients | jq 'length'

# single aggregated patient bundle
curl -s http://localhost:8000/patients/4e645243-fe58-5f74-b0bf-4271b5fdc0bf | jq '.aa | length'
```

Validate mock-data FK integrity without booting any service:

```bash
python3 backend/scripts/load_mock.py
```

## Error Model

- `GET /patients/{id}` not found → `404` `{"error": "patient_not_found", "patientId": "<id>"}`
- Any downstream service fails → `502` `{"error": "upstream_unavailable", "service": "<name>"}`. The gateway is fail-fast and never returns a partial bundle.

## Dev Scripts

Frontend (run from `frontend/`):

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start Vite dev server (:8080) |
| `npm run build` | Production build |
| `npm run lint` / `lint:fix` | ESLint (Airbnb + TypeScript + Prettier) |
| `npm run typecheck` | `tsc -b --noEmit` |
| `npm run format` / `format:check` | Prettier |
| `npm test` / `test:watch` | Vitest unit tests |
| `npm run test:e2e` | Playwright E2E |

Backend: see `backend/README.md`. Individual services can be run with `uvicorn <pkg>.app:app --reload`.

## Further Reading

- [`PLAN.md`](PLAN.md) — initial architecture, memory budget, implementation steps
- [`genetic_medicine_search_page_spec_v2_with_mermaid.md`](genetic_medicine_search_page_spec_v2_with_mermaid.md) — query-page feature spec (with mermaid diagrams)
- [`backend/README.md`](backend/README.md) — microservice endpoints, CORS, error-code details
- [`frontend/README.md`](frontend/README.md) — frontend env setup and common troubleshooting
- [`openspec/`](openspec/) — change proposals and specs (OpenSpec workflow)

## License

Proprietary — internal use only. All rights reserved.

---

# 基因醫學整合查詢中心

內部醫療資訊系統，讓基因醫學醫師以「病人查詢」與「條件查詢」兩種模式跨 14 個資料模組（基本資料、OPD、AA、MS/MS、Biomarker、LSD、Enzyme、GAG、DNAbank、Outbank、AADC、ALD、MMA、MPS2）檢索病人資料。前端由 Vite + React 提供 UI，後端以 FastAPI 微服務架構聚合資料。

## 架構總覽

```
Browser (Vite dev server, :8080)
        │
        ▼
┌──────────────────┐      ┌───────────────┐
│ gateway  :8000   │──────▶ svc-patient   │  :8001
│  (BFF / CORS /   │──────▶ svc-lab       │  :8002
│   aggregation)   │──────▶ svc-disease   │  :8003
└──────────────────┘      └───────────────┘
```

- 瀏覽器只直接打 `gateway`，由 `gateway` 透過 `httpx.AsyncClient` 扇出到三個內部服務。
- 內部服務之間不互相呼叫，聚合責任全在 `gateway`。
- 內部服務沒有 CORS middleware，瀏覽器直接存取會被阻擋（設計如此）。
- 開發環境以 `backend/mock-data/` 的 JSON 當資料來源，啟動時由 `shared.data_loader.validate()` 檢查 FK 完整性，失敗即 non-zero 離開。

## 專案結構

```
my-project/
├── frontend/           # Vite + React 19 + TypeScript + Tailwind + shadcn/ui
├── backend/
│   ├── gateway/        # 前端唯一入口（:8000）
│   ├── svc-patient/    # 病人基本資料（:8001）
│   ├── svc-lab/        # 檢驗 + 檢體（:8002）
│   ├── svc-disease/    # 疾病專案（:8003）
│   ├── shared/         # 共用 Pydantic schemas / data_loader
│   ├── mock-data/      # 開發用 JSON 種子資料
│   └── scripts/        # dev.sh、load_mock.py
├── openspec/           # 變更提案與規格（OpenSpec 工作流程）
├── PLAN.md             # 初始架構與實作計畫
└── genetic_medicine_search_page_spec_v2_with_mermaid.md  # 功能規格
```

## 快速啟動

需求：Python 3.10+、Node.js（或 Bun）。

### 1. 啟動後端

在 repo 根目錄建立 venv 並安裝四個服務（都是 editable install）：

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -U pip
pip install -e backend/shared \
            -e backend/gateway \
            -e backend/svc-patient \
            -e backend/svc-lab \
            -e backend/svc-disease
```

一鍵啟動四個服務（`Ctrl-C` 會傳遞給全部子行程）：

```bash
bash backend/scripts/dev.sh
```

### 2. 啟動前端

```bash
cd frontend
npm install       # 或 bun install
npm run dev       # Vite 開在 http://localhost:8080
```

前端讀取 `VITE_API_BASE_URL` 指向 gateway，預設值 `http://localhost:8000` 放在 `frontend/.env.development`。如需每台機器覆寫，複製 `frontend/.env.example` 成 `frontend/.env.local`。

### 3. ⚠️ CORS 設定

Gateway 的 `GATEWAY_CORS_ORIGIN` 預設是 `http://localhost:5173`，但 Vite dev server 實際跑在 `8080`。啟動 gateway 前必須覆寫此環境變數，否則瀏覽器呼叫會被擋：

```bash
export GATEWAY_CORS_ORIGIN=http://localhost:8080
bash backend/scripts/dev.sh
```

## 煙霧測試

```bash
# gateway 健康檢查
curl -s http://localhost:8000/healthz

# 完整病人清單
curl -s http://localhost:8000/patients | jq 'length'

# 單一病人聚合 bundle
curl -s http://localhost:8000/patients/4e645243-fe58-5f74-b0bf-4271b5fdc0bf | jq '.aa | length'
```

不經 gateway 只驗證 mock 資料的 FK 完整性：

```bash
python3 backend/scripts/load_mock.py
```

## 錯誤模型

- `GET /patients/{id}` 找不到 → `404` `{"error": "patient_not_found", "patientId": "<id>"}`
- 任一下游服務失敗 → `502` `{"error": "upstream_unavailable", "service": "<name>"}`。Gateway 一律 fail-fast，不回傳部分 bundle。

## 開發腳本

前端（在 `frontend/` 下執行）：

| 指令 | 用途 |
| --- | --- |
| `npm run dev` | 啟動 Vite dev server（:8080） |
| `npm run build` | Production build |
| `npm run lint` / `lint:fix` | ESLint（Airbnb + TypeScript + Prettier） |
| `npm run typecheck` | `tsc -b --noEmit` |
| `npm run format` / `format:check` | Prettier |
| `npm test` / `test:watch` | Vitest 單元測試 |
| `npm run test:e2e` | Playwright E2E |

後端：見 `backend/README.md`，可用 `uvicorn <pkg>.app:app --reload` 逐個跑。

## 延伸文件

- [`PLAN.md`](PLAN.md) — 初始架構、記憶體預算、實作步驟
- [`genetic_medicine_search_page_spec_v2_with_mermaid.md`](genetic_medicine_search_page_spec_v2_with_mermaid.md) — 查詢頁面功能規格（含 mermaid 圖）
- [`backend/README.md`](backend/README.md) — 微服務 API 端點、CORS、錯誤碼細節
- [`frontend/README.md`](frontend/README.md) — 前端 env 設定與常見錯誤排查
- [`openspec/`](openspec/) — 變更提案與 specs（OpenSpec 工作流程）

## 授權

Proprietary — internal use only. All rights reserved.（專屬授權，僅供內部使用，保留所有權利。）
