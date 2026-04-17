# 基因醫學整合查詢中心 — 開發環境建置計畫

## Context

建立「基因醫學整合查詢中心」的開發環境，採用 microservice 架構。這是一個內部醫療系統，讓基因醫學醫師可以透過「病人查詢」和「條件查詢」兩種模式，查詢 14 個資料模組。

**前端現況**（已上傳到 VM）：
- Vite + React 18 + TypeScript + Tailwind CSS + shadcn/ui
- 由 Lovable 產生，UI 已完成
- Dev server port: **8080**
- 使用 mock data（`src/data/mockData.ts`，5 位假病人）
- React Query 已安裝但未使用，準備好接後端 API
- 關鍵前端檔案：
  - `src/types/medical.ts` — 14 個模組的完整型別定義、欄位、operators
  - `src/data/mockData.ts` — mock 資料
  - `src/pages/Index.tsx` — 主頁面
  - `src/components/ConditionBuilder.tsx` — 條件查詢建構器
  - `src/components/ConditionResults.tsx` — 條件查詢結果（含 client-side evaluation）
  - `src/components/FilterPanel.tsx` — 左側篩選面板
  - `src/components/ResultModules.tsx` — 14 個模組的結果顯示
  - `src/components/PatientSummary.tsx` — 病人摘要卡片

**後端**：Python / FastAPI，microservice 架構
**資料庫**：連線外部機器
**VM**：1 GB RAM — 決定了服務數量上限
**Production 部署**（Docker/k8s）之後再做

---

## 架構：3+1 Microservices

1 GB RAM 下，每個 Uvicorn process 約 60-70 MB。拆成 **4 個服務**是記憶體上限：

| 服務 | Port | 負責模組 | 說明 |
|---|---|---|---|
| `gateway` | 8000 | — | API Gateway / BFF，負責路由、聚合、CORS、認證 |
| `svc-patient` | 8001 | 基本資料、OPD | 病人身份與門診紀錄 |
| `svc-lab` | 8002 | AA、MS/MS、Biomarker、LSD、Enzyme、GAG、DNAbank、Outbank | 檢驗結果 + 檢體管理 |
| `svc-disease` | 8003 | AADC、ALD、MMA、MPS2 | 疾病專案模組 |

**記憶體預算：**

| 元件 | 預估 RAM |
|---|---|
| gateway (1 worker) | ~60 MB |
| svc-patient (1 worker) | ~60 MB |
| svc-lab (1 worker) | ~70 MB |
| svc-disease (1 worker) | ~60 MB |
| Vite dev server (port 8080) | ~150 MB |
| OS + 系統 | ~200 MB |
| DB connections + 請求處理 | ~400 MB |
| **合計** | **~1000 MB** |

---

## 服務間通訊

- 前端 (port 8080) → Vite proxy → gateway (port 8000) → 下游服務
- gateway 用 `httpx.AsyncClient` 呼叫下游服務
- 下游服務之間**不互相呼叫**，由 gateway 負責聚合
- 不需要 message queue（全部是同步 request-response）
- 所有服務連同一個外部 DB（不同 table/schema）

---

## 專案結構

```
/home/user/my-project/
├── frontend/                          # React 應用（已存在，Lovable 產生）
│   ├── src/
│   │   ├── components/                # UI 元件（已完成）
│   │   ├── data/mockData.ts           # Mock data → 之後改成打 API
│   │   ├── types/medical.ts           # 14 模組型別定義
│   │   ├── hooks/                     # 新增 API hooks（用 React Query）
│   │   └── lib/api.ts                 # 新增 API client
│   ├── vite.config.ts                 # 需加 proxy 設定
│   └── package.json
│
├── backend/
│   ├── shared/                        # 共用 Python 套件
│   │   ├── pyproject.toml
│   │   └── shared/
│   │       ├── __init__.py
│   │       ├── db.py                  # SQLAlchemy engine + session
│   │       ├── config.py              # 共用設定（DB URL, ports）
│   │       ├── auth.py                # 認證工具
│   │       ├── models/                # SQLAlchemy models（全部 table）
│   │       │   ├── patient.py
│   │       │   ├── lab.py
│   │       │   ├── specimen.py
│   │       │   └── disease.py
│   │       └── schemas/               # Pydantic schemas（對應前端 types/medical.ts）
│   │           ├── patient.py
│   │           ├── lab.py
│   │           ├── specimen.py
│   │           └── disease.py
│   │
│   ├── gateway/                       # API Gateway
│   │   ├── pyproject.toml
│   │   └── gateway/
│   │       ├── main.py                # FastAPI app, CORS (allow localhost:8080)
│   │       ├── proxy.py               # httpx client 呼叫下游
│   │       ├── aggregator.py          # 聚合多服務回應
│   │       └── routes/
│   │           ├── auth.py
│   │           ├── patient_query.py   # 病人查詢模式編排
│   │           ├── condition_query.py # 條件查詢模式編排
│   │           └── patient_detail.py  # 病人詳情聚合
│   │
│   ├── svc-patient/                   # 病人服務
│   │   ├── pyproject.toml
│   │   └── svc_patient/
│   │       ├── main.py
│   │       ├── routes/
│   │       │   ├── basic_info.py
│   │       │   ├── opd.py
│   │       │   └── search.py
│   │       └── services/
│   │           └── patient_service.py
│   │
│   ├── svc-lab/                       # 檢驗 + 檢體服務
│   │   ├── pyproject.toml
│   │   └── svc_lab/
│   │       ├── main.py
│   │       ├── routes/
│   │       │   ├── amino_acid.py      # AA
│   │       │   ├── msms.py            # MS/MS
│   │       │   ├── biomarker.py       # Biomarker
│   │       │   ├── lsd.py             # LSD panel
│   │       │   ├── enzyme.py          # Enzyme
│   │       │   ├── gag.py             # GAG
│   │       │   ├── dnabank.py         # DNAbank
│   │       │   └── outbank.py         # Outbank
│   │       └── services/
│   │           ├── lab_service.py
│   │           └── specimen_service.py
│   │
│   ├── svc-disease/                   # 疾病專案服務
│   │   ├── pyproject.toml
│   │   └── svc_disease/
│   │       ├── main.py
│   │       ├── routes/
│   │       │   ├── aadc.py
│   │       │   ├── ald.py
│   │       │   ├── mma.py
│   │       │   └── mps2.py
│   │       └── services/
│   │           └── disease_service.py
│   │
│   └── scripts/
│       ├── dev-start.sh               # 一鍵啟動所有服務
│       └── dev-stop.sh                # 一鍵停止
│
├── .env                               # DATABASE_URL, SECRET_KEY 等
├── .env.example
├── .gitignore
└── Makefile                           # make dev, make test 等
```

---

## 實作步驟

### Step 1：系統準備

```bash
sudo apt update && sudo apt install -y python3-pip python3-venv git
```

### Step 2：前端安裝依賴

```bash
cd /home/user/my-project/frontend
npm install
```

### Step 3：修改 `frontend/vite.config.ts` — 加入 API proxy

在現有 server 設定中加入 proxy：
```typescript
server: {
  host: "::",
  port: 8080,
  hmr: { overlay: false },
  proxy: {
    '/api': 'http://localhost:8000'   // → gateway
  }
}
```

### Step 4：建立前端 API 層

新增 `src/lib/api.ts` — API client（fetch wrapper），取代 mock data：
- `searchPatient(query)` → `GET /api/query/patient?q=...`
- `conditionSearch(conditions)` → `POST /api/query/condition`
- `getPatientDetail(patientId, modules)` → `GET /api/patient-detail/:id`

新增 `src/hooks/usePatientQuery.ts` 等 — 用 React Query 包裝 API calls：
- 利用已安裝的 `@tanstack/react-query`
- 取代 `ConditionResults.tsx` 中的 client-side `evaluateConditions()`
- 取代 `Index.tsx` 中對 `mockPatients` 的直接 filter

### Step 5：建立 Python 虛擬環境與 shared 套件

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -e backend/shared/
```

shared 套件包含：
- `db.py`：SQLAlchemy async engine，`pool_size=2, max_overflow=3`
- `config.py`：讀取 `.env`，ports 和 DB URL
- `schemas/`：**對應前端 `types/medical.ts` 的 Pydantic schemas**，保持前後端型別一致
- `models/`：SQLAlchemy ORM models

### Step 6：建立 4 個 FastAPI 服務

每個服務獨立的 FastAPI app，安裝依賴後可單獨啟動：
- `fastapi`, `uvicorn[standard]`, `httpx`, `sqlalchemy[asyncio]`, `pydantic-settings`
- Gateway CORS 允許 `http://localhost:8080`

### Step 7：Git 初始化並推上 GitHub

```bash
cd /home/user/my-project
# 安裝 gh CLI
gh auth login
git init
git add .
git commit -m "Initial commit"
gh repo create --private --source=. --push
```

### Step 8：啟動腳本與 Makefile

`make dev` 一鍵啟動所有服務 + 前端

---

## Gateway 路由對照表

```
前端 (localhost:8080)
  ↓ Vite proxy /api/*
Gateway (localhost:8000)
  ├── /api/auth/*           → gateway 直接處理
  ├── /api/patient/*        → proxy 到 svc-patient:8001
  ├── /api/lab/*            → proxy 到 svc-lab:8002
  ├── /api/disease/*        → proxy 到 svc-disease:8003
  ├── /api/query/patient    → gateway 編排（呼叫 svc-patient）
  ├── /api/query/condition  → gateway 編排（依 module 路由）
  └── /api/patient-detail/* → gateway 聚合（並行呼叫 3 個服務）
```

Module → 服務對應（對齊前端 `ModuleId` 型別）：
```
basic, opd                              → svc-patient
aa, msms, biomarker, lsd,
enzyme, gag, dnabank, outbank           → svc-lab
aadc, ald, mma, mps2                    → svc-disease
```

---

## 前端 → 後端 整合重點

前端目前是全 client-side，整合後端需要改動的檔案：

| 前端檔案 | 改動說明 |
|---|---|
| `src/data/mockData.ts` | 開發初期保留作為 fallback，最終移除 |
| `src/lib/api.ts` | **新增** — API client |
| `src/hooks/usePatientQuery.ts` | **新增** — React Query hooks |
| `src/hooks/useConditionSearch.ts` | **新增** — 條件查詢 hook |
| `src/pages/Index.tsx` | 改用 hooks 取代直接存取 mockPatients |
| `src/components/ConditionResults.tsx` | `evaluateConditions()` 邏輯移到後端 |
| `vite.config.ts` | 加 proxy 設定 |

後端 Pydantic schemas 需對齊前端型別：
- `Patient` → `shared/schemas/patient.py`
- `ConditionRow`, `ConditionLogic` → gateway condition query request schema
- 各模組的 Sample types → 對應服務的 response schemas

---

## 開發時啟動方式

```bash
# 一鍵啟動（Makefile）
make dev

# 或分別啟動
# Terminal 1 — gateway
uvicorn gateway.main:app --reload --port 8000

# Terminal 2 — svc-patient
uvicorn svc_patient.main:app --reload --port 8001

# Terminal 3 — svc-lab
uvicorn svc_lab.main:app --reload --port 8002

# Terminal 4 — svc-disease
uvicorn svc_disease.main:app --reload --port 8003

# Terminal 5 — frontend
cd frontend && npm run dev   # port 8080
```

---

## 未來 Production 部署（之後再做）

每個服務目錄加 `Dockerfile`：
- `shared/` 打包成 wheel，安裝到每個 container
- `docker-compose.yml` 定義所有服務 + nginx
- `localhost:PORT` 換成 k8s service DNS name
- 前端 `npm run build` 產出靜態檔，由 nginx 提供
- 專案結構和程式碼不需要改

---

## 驗證方式

1. `curl http://localhost:8000/api/health` — gateway 正常
2. `curl http://localhost:8001/internal/health` — svc-patient 正常
3. `curl http://localhost:8002/internal/health` — svc-lab 正常
4. `curl http://localhost:8003/internal/health` — svc-disease 正常
5. 瀏覽器開 `http://localhost:8080` — 前端正常載入
6. 前端搜尋病人 → 透過 Vite proxy 打到 gateway → 正確回傳結果
7. 條件查詢 → gateway 路由到正確的下游服務 → 回傳病人清單
8. `free -h` — 記憶體使用在合理範圍（< 900 MB）
