# Genetic Medicine Integrated Query Center

Internal medical information system that lets geneticists search patient data across 14 data modules (basic info, OPD, AA, MS/MS, Biomarker, LSD, Enzyme, GAG, DNAbank, Outbank, AADC, ALD, MMA, MPS2) using two query modes: **patient query** and **condition query**. The frontend is a Vite + React SPA; the backend is a FastAPI microservice architecture that aggregates results from three internal services behind a single gateway, reading either JSON fixtures (default for dev) or an alembic-managed PostgreSQL `gimc` database.

## Architecture

```
Browser
   │
   ▼
┌──────────────────────────┐
│  frontend (Vite SPA)     │  dev: vite :8080  │  prod: nginx in container
└─────────────┬────────────┘
              │
              ▼
┌──────────────────┐      ┌───────────────┐
│ gateway  :8000   │──────▶ svc-patient   │  :8001 ─┐
│  (BFF / CORS /   │──────▶ svc-lab       │  :8002 ─┼──▶  PostgreSQL :5432
│   aggregation)   │──────▶ svc-disease   │  :8003 ─┘     (gimc / 5 schemas)
└──────────────────┘      └───────────────┘
```

- The frontend SPA only calls `gateway`; `gateway` fans out to the three internal services via `httpx.AsyncClient`.
- Internal services never call each other — all aggregation happens in `gateway`.
- Internal services have no CORS middleware, so direct browser calls are blocked by design.
- The data source is chosen by `GIMC_DATA_BACKEND`: `json` (default, reads `backend/mock-data/`) or `postgres` (reads the alembic-managed `gimc` database — schemas `main` / `external` / `nbs` / `links` / `ref`). Both modes return identical row shapes, so service code is unchanged across the two. At startup `shared.data_loader.validate()` checks FK integrity and exits non-zero on the first violation before the service binds its port.

## Project Layout

```
my-project/
├── frontend/           # Vite + React 19 + TypeScript + Tailwind + shadcn/ui
│   ├── Dockerfile      # Bun build → nginx runtime (multi-stage)
│   ├── nginx.conf      # SPA fallback + cache rules + /healthz
│   └── docker-entrypoint.sh   # injects VITE_API_BASE_URL at container start
├── backend/
│   ├── gateway/        # Frontend-facing entry point (:8000)
│   ├── svc-patient/    # Patient base records (:8001)
│   ├── svc-lab/        # Lab results + specimens (:8002)
│   ├── svc-disease/    # Disease-project modules (:8003)
│   ├── shared/         # Pydantic schemas + SQLAlchemy models + dual-backend data_loader
│   ├── alembic/        # Migration scripts (alembic.ini lives at backend/ root)
│   ├── etl/            # One-shot 1.0 / 2.0 → PG ETL (retired post-cutover)
│   ├── mock-data/      # Fixture JSON; data source for `json` mode AND `make seed-pg`
│   ├── scripts/        # dev.sh, setup-postgres.sh, load_mock.py, seed_from_json.py, docker-entrypoint.sh
│   ├── Makefile        # install / alembic-up / alembic-check / seed-pg / verify-pg
│   └── Dockerfile      # One image; SERVICE env var selects which app runs
├── compose/
│   └── init-db/        # PG bootstrap SQL run on first `db` container start
├── docker-compose.yml  # Full-stack orchestration (db, migrate, 4 services, frontend)
├── openspec/           # Change proposals and specs (OpenSpec workflow)
├── PLAN.md             # Initial architecture and implementation plan
└── genetic_medicine_search_page_spec_v2_with_mermaid.md  # Feature spec
```

## Quick Start

Requirements: Python 3.10+, Node.js (or Bun).

### 1. Start the backend

From the repo root, create a venv and install the five backend packages (`shared` + four services) using the Makefile:

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -U pip
make -C backend install
```

Then pick a data backend:

#### Option A — JSON fixture mode (default, no PostgreSQL needed)

```bash
bash backend/scripts/dev.sh
```

`shared.data_loader` reads `backend/mock-data/` directly. This is the fastest path for everyday frontend work — `Ctrl-C` propagates to every child.

#### Option B — PostgreSQL mode

If you want to develop against a live `gimc` database:

```bash
sudo bash backend/scripts/setup-postgres.sh    # one-time: install PG 16, create role / db / 5 schemas
cp backend/.env.example backend/.env            # then set GIMC_DATA_BACKEND=postgres
make -C backend alembic-up                      # apply migrations
make -C backend seed-pg                         # load mock-data into PG (idempotent)
bash backend/scripts/dev.sh                     # services now read PG instead of JSON
```

`make -C backend verify-pg` runs the 7-check parity suite once the services are up.

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

## Containerised Deploy (Docker Compose)

A `docker-compose.yml` at the repo root brings up the full stack — PostgreSQL, alembic migration, the four FastAPI services, and the nginx-served SPA — in one command. Use it for stage smoke tests, or as a reference for prod (where `db` is typically swapped for managed PostgreSQL).

### Bring it up

```bash
docker compose up -d --build                      # build images + start everything
docker compose ps                                 # confirm every service is healthy
docker compose --profile seed run --rm seed       # one-shot: load mock-data into PG
open http://localhost                             # SPA → proxy → gateway → services → PG
```

### Topology

| Service       | Host port  | Role                                                                |
|---------------|------------|---------------------------------------------------------------------|
| `db`          | 5432       | `postgres:16` (open to host so DBeaver can connect; drop in prod)   |
| `migrate`     | —          | one-shot `alembic upgrade head`                                     |
| `svc-patient` / `svc-lab` / `svc-disease` | — | internal services (no host port)                          |
| `gateway`     | —          | internal only; reached via the proxy under `/api/`                  |
| `frontend`    | —          | internal only; nginx serves the Vite bundle                         |
| `proxy`       | 80         | nginx edge — `/` → frontend, `/api/` → gateway (prefix stripped)    |
| `seed`        | —          | `--profile seed` only; mounts `backend/mock-data/`                  |

The backend is **one image**; the `SERVICE` env var picks the entrypoint (`gateway`, `svc-patient`, `svc-lab`, `svc-disease`, `migrate`, `seed`, or `shell`).

### Stage / prod URL overrides

The gateway's CORS allow-origin and the SPA's API base URL are env-driven. Drop a `.env` at the repo root:

```bash
PUBLIC_API_URL=https://stage.example.com/api    # same origin as the SPA, under /api
PUBLIC_WEB_URL=https://stage.example.com        # gateway CORS allow-origin (no port)
```

The frontend image bakes a build-time sentinel; its container entrypoint sed-replaces it with the runtime `VITE_API_BASE_URL` before nginx starts — so the same image runs unchanged across environments. With the reverse proxy in front, `PUBLIC_API_URL` is typically a same-origin path like `/api`.

### Going prod-flavoured

In real prod you usually want managed PostgreSQL (RDS, Cloud SQL, ...):

1. Remove the `db` service (or override via `compose.override.yaml`); the `pg-data` volume and `compose/init-db` mount go with it.
2. Apply `compose/init-db/01-schemas.sql` to the managed DB once, by hand.
3. Point every backend service's `DATABASE_URL` at the external host. Pass the password via Docker secrets or orchestrator-managed env, not `.env`.

## Smoke Tests

End-to-end via the gateway (works in both data backends):

```bash
# gateway healthcheck
curl -s http://localhost:8000/healthz

# full patient list
curl -s http://localhost:8000/patients | jq 'length'

# single aggregated patient bundle
curl -s http://localhost:8000/patients/4e645243-fe58-5f74-b0bf-4271b5fdc0bf | jq '.aa | length'
```

Backend-specific checks without going through the gateway:

```bash
# JSON mode — FK sweep over backend/mock-data/, no DB needed
python3 backend/scripts/load_mock.py

# PG mode — confirm migrations match SQLAlchemy metadata (non-zero on drift)
make -C backend alembic-check

# PG mode — full 7-check parity suite (counts, FK integrity, perf baseline, ...)
make -C backend verify-pg
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

Backend (run from repo root or `backend/`; see also [`backend/README.md`](backend/README.md)):

| Command | Purpose |
| --- | --- |
| `make -C backend install` | Install all five packages (`shared` + 4 services) into the active venv as editable |
| `make -C backend alembic-up` | Apply pending PG migrations (`alembic upgrade head`) |
| `make -C backend alembic-check` | Compare metadata vs DB; non-zero on drift |
| `make -C backend seed-pg` | Load `mock-data/` JSON into PG (idempotent: `TRUNCATE … CASCADE` then bulk insert) |
| `make -C backend verify-pg` | 7-check parity suite (row counts, FKs, anchor UUID round-trip, perf baseline) |
| `bash backend/scripts/dev.sh` | Start all four FastAPI services in parallel |
| `python3 backend/scripts/load_mock.py` | Validate mock-data FK integrity without booting a service |

Individual services can also be run with `uvicorn <pkg>.app:app --reload`.

## Further Reading

- [`PLAN.md`](PLAN.md) — initial architecture, memory budget, implementation steps
- [`genetic_medicine_search_page_spec_v2_with_mermaid.md`](genetic_medicine_search_page_spec_v2_with_mermaid.md) — query-page feature spec (with mermaid diagrams)
- [`backend/README.md`](backend/README.md) — microservice endpoints, CORS, error-code details
- [`frontend/README.md`](frontend/README.md) — frontend env setup and common troubleshooting
- [`docker-compose.yml`](docker-compose.yml) — full-stack stage / smoke-test orchestration
- [`openspec/`](openspec/) — change proposals and specs (OpenSpec workflow)

## License

Proprietary — internal use only. All rights reserved.

---

# 基因醫學整合查詢中心

內部醫療資訊系統，讓基因醫學醫師以「病人查詢」與「條件查詢」兩種模式跨 14 個資料模組（基本資料、OPD、AA、MS/MS、Biomarker、LSD、Enzyme、GAG、DNAbank、Outbank、AADC、ALD、MMA、MPS2）檢索病人資料。前端由 Vite + React 提供 UI，後端以 FastAPI 微服務架構聚合資料；資料來源可在 JSON fixture（dev 預設）與 alembic 管理的 PostgreSQL `gimc` 資料庫之間切換。

## 架構總覽

```
Browser
   │
   ▼
┌──────────────────────────┐
│  frontend (Vite SPA)     │  開發: vite :8080  │  正式: container 內 nginx
└─────────────┬────────────┘
              │
              ▼
┌──────────────────┐      ┌───────────────┐
│ gateway  :8000   │──────▶ svc-patient   │  :8001 ─┐
│  (BFF / CORS /   │──────▶ svc-lab       │  :8002 ─┼──▶  PostgreSQL :5432
│   aggregation)   │──────▶ svc-disease   │  :8003 ─┘     (gimc / 5 schemas)
└──────────────────┘      └───────────────┘
```

- 前端 SPA 只打 `gateway`，由 `gateway` 透過 `httpx.AsyncClient` 扇出到三個內部服務。
- 內部服務之間不互相呼叫，聚合責任全在 `gateway`。
- 內部服務沒有 CORS middleware，瀏覽器直接存取會被阻擋（設計如此）。
- 資料來源由 `GIMC_DATA_BACKEND` 決定：`json`（預設，讀 `backend/mock-data/`）或 `postgres`（讀 alembic 管理的 `gimc` 資料庫，含 `main` / `external` / `nbs` / `links` / `ref` 五個 schema）。兩種模式回傳的 row 形狀完全一致，service code 在兩條路徑下不需修改。啟動時由 `shared.data_loader.validate()` 檢查 FK 完整性，失敗即在綁 port 前 non-zero 離開。

## 專案結構

```
my-project/
├── frontend/           # Vite + React 19 + TypeScript + Tailwind + shadcn/ui
│   ├── Dockerfile      # Bun 建置 → nginx 服務（multi-stage）
│   ├── nginx.conf      # SPA fallback + 快取策略 + /healthz
│   └── docker-entrypoint.sh   # 啟動時注入 VITE_API_BASE_URL
├── backend/
│   ├── gateway/        # 前端唯一入口（:8000）
│   ├── svc-patient/    # 病人基本資料（:8001）
│   ├── svc-lab/        # 檢驗 + 檢體（:8002）
│   ├── svc-disease/    # 疾病專案（:8003）
│   ├── shared/         # Pydantic schemas + SQLAlchemy models + dual-backend data_loader
│   ├── alembic/        # Migration 腳本（alembic.ini 在 backend/ 根目錄）
│   ├── etl/            # 1.0 / 2.0 → PG 一次性 ETL（cutover 後退役）
│   ├── mock-data/      # Fixture JSON；`json` 模式跟 `make seed-pg` 共用
│   ├── scripts/        # dev.sh、setup-postgres.sh、load_mock.py、seed_from_json.py、docker-entrypoint.sh
│   ├── Makefile        # install / alembic-up / alembic-check / seed-pg / verify-pg
│   └── Dockerfile      # 一個 image；用 SERVICE 環境變數決定跑哪個入口
├── compose/
│   └── init-db/        # PG 第一次啟動時跑的 bootstrap SQL
├── docker-compose.yml  # 全堆疊 orchestration（db、migrate、四個服務、前端）
├── openspec/           # 變更提案與規格（OpenSpec 工作流程）
├── PLAN.md             # 初始架構與實作計畫
└── genetic_medicine_search_page_spec_v2_with_mermaid.md  # 功能規格
```

## 快速啟動

需求：Python 3.10+、Node.js（或 Bun）。

### 1. 啟動後端

在 repo 根目錄建立 venv，並用 Makefile 安裝五個 backend 套件（`shared` + 四個服務）：

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -U pip
make -C backend install
```

接著選一個資料來源：

#### 選項 A — JSON fixture 模式（預設，不需要 PostgreSQL）

```bash
bash backend/scripts/dev.sh
```

`shared.data_loader` 會直接讀 `backend/mock-data/`。日常前端工作走這條路最快 — `Ctrl-C` 會傳給全部子行程。

#### 選項 B — PostgreSQL 模式

如要對著 live `gimc` 資料庫開發：

```bash
sudo bash backend/scripts/setup-postgres.sh    # 一次性：裝 PG 16、建立 role / db / 5 個 schema
cp backend/.env.example backend/.env            # 然後把 GIMC_DATA_BACKEND 改成 postgres
make -C backend alembic-up                      # 套用 migrations
make -C backend seed-pg                         # 把 mock-data 灌進 PG（idempotent）
bash backend/scripts/dev.sh                     # 服務改從 PG 讀，不再讀 JSON
```

服務起來後可用 `make -C backend verify-pg` 跑 7-check parity 套件。

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

## 容器化部署 (Docker Compose)

repo 根目錄的 `docker-compose.yml` 一鍵起整個 stack — PostgreSQL、alembic migration、四個 FastAPI 服務、nginx 服務的 SPA。Stage 煙霧測試適用，也可當 prod 部署的參考（prod 通常把 `db` 換成 managed PostgreSQL）。

### 啟動

```bash
docker compose up -d --build                      # build images + 全部啟動
docker compose ps                                 # 確認每個服務都 healthy
docker compose --profile seed run --rm seed       # 一次性灌 mock-data 進 PG
open http://localhost                             # SPA → proxy → gateway → services → PG
```

### 服務拓撲

| 服務          | 對外 port  | 角色                                                                |
|---------------|------------|---------------------------------------------------------------------|
| `db`          | 5432       | `postgres:16`（給 DBeaver 連的；prod 要關掉這個 `ports`）            |
| `migrate`     | —          | 一次性跑 `alembic upgrade head`                                     |
| `svc-patient` / `svc-lab` / `svc-disease` | — | 內部服務（不對外）                                       |
| `gateway`     | —          | 純內部；經 proxy 的 `/api/` 對外                                    |
| `frontend`    | —          | 純內部；nginx 服務 Vite bundle                                      |
| `proxy`       | 80         | nginx edge — `/` → frontend、`/api/` → gateway（會 strip 前綴）     |
| `seed`        | —          | 只有 `--profile seed` 才啟動；會掛 `backend/mock-data/`             |

後端是 **一個 image**；由 `SERVICE` 環境變數決定入口（`gateway`、`svc-patient`、`svc-lab`、`svc-disease`、`migrate`、`seed`、`shell`）。

### Stage / prod 環境覆寫網址

Gateway 的 CORS allow-origin 跟 SPA 的 API base URL 都是環境變數驅動。在 repo 根目錄放一份 `.env`：

```bash
PUBLIC_API_URL=https://stage.example.com/api    # 跟 SPA 同 origin，掛在 /api 下
PUBLIC_WEB_URL=https://stage.example.com        # gateway CORS allow-origin（無 port）
```

Frontend image 在 build 時打進一個 sentinel 字串，container entrypoint 啟動 nginx 前用 sed 替換成 runtime 的 `VITE_API_BASE_URL` —— 同一個 image 可在 stage / prod 跨環境跑。有 reverse proxy 之後 `PUBLIC_API_URL` 通常就是相對路徑 `/api`。

### 改成 prod 風格

實務 prod 通常用 managed PostgreSQL（RDS、Cloud SQL …）：

1. 移除 `db` service（或用 `compose.override.yaml` 覆寫），連同 `pg-data` volume 跟 `compose/init-db` mount 一起拿掉。
2. 對 managed DB 手動跑一次 `compose/init-db/01-schemas.sql`。
3. 把所有後端 service 的 `DATABASE_URL` 指向外部主機。密碼透過 Docker secrets 或 orchestrator 管理，不要走 `.env`。

## 煙霧測試

End-to-end 走 gateway（兩種資料模式都適用）：

```bash
# gateway 健康檢查
curl -s http://localhost:8000/healthz

# 完整病人清單
curl -s http://localhost:8000/patients | jq 'length'

# 單一病人聚合 bundle
curl -s http://localhost:8000/patients/4e645243-fe58-5f74-b0bf-4271b5fdc0bf | jq '.aa | length'
```

不經 gateway 的後端檢查：

```bash
# JSON 模式 — 對 backend/mock-data/ 做 FK sweep，不需要 DB
python3 backend/scripts/load_mock.py

# PG 模式 — 確認 migrations 跟 SQLAlchemy metadata 一致（不一致就 non-zero）
make -C backend alembic-check

# PG 模式 — 7-check parity 套件（row count、FK 完整性、效能基線 ...）
make -C backend verify-pg
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

後端（在 repo 根目錄或 `backend/` 下執行；詳見 [`backend/README.md`](backend/README.md)）：

| 指令 | 用途 |
| --- | --- |
| `make -C backend install` | 把五個套件（`shared` + 四個服務）以 editable 模式裝進 venv |
| `make -C backend alembic-up` | 套用 PG migrations（`alembic upgrade head`） |
| `make -C backend alembic-check` | 比對 metadata 跟實際 DB；有 drift 時 non-zero 退出 |
| `make -C backend seed-pg` | 把 `mock-data/` JSON 灌進 PG（idempotent：先 `TRUNCATE … CASCADE` 再 bulk insert） |
| `make -C backend verify-pg` | 7-check parity 套件（row count、FK、anchor UUID round-trip、效能基線） |
| `bash backend/scripts/dev.sh` | 並行啟動四個 FastAPI 服務 |
| `python3 backend/scripts/load_mock.py` | 不啟動服務直接驗證 mock-data FK 完整性 |

也可以用 `uvicorn <pkg>.app:app --reload` 逐個跑單一服務。

## 延伸文件

- [`PLAN.md`](PLAN.md) — 初始架構、記憶體預算、實作步驟
- [`genetic_medicine_search_page_spec_v2_with_mermaid.md`](genetic_medicine_search_page_spec_v2_with_mermaid.md) — 查詢頁面功能規格（含 mermaid 圖）
- [`backend/README.md`](backend/README.md) — 微服務 API 端點、CORS、錯誤碼細節
- [`frontend/README.md`](frontend/README.md) — 前端 env 設定與常見錯誤排查
- [`docker-compose.yml`](docker-compose.yml) — 全堆疊 stage / 煙霧測試 orchestration
- [`openspec/`](openspec/) — 變更提案與 specs（OpenSpec 工作流程）

## 授權

Proprietary — internal use only. All rights reserved.（專屬授權，僅供內部使用，保留所有權利。）
