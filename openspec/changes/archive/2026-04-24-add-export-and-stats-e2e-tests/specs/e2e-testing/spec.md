## ADDED Requirements

### Requirement: 匯出功能 e2e 覆蓋

`frontend/tests/` SHALL 為 `PatientSummary` 的「匯出」流程提供三支 Playwright 測試，分別驗證 CSV (zip)、JSON、XLSX 三種格式的下載行為。每支測試 MUST 使用 `page.waitForEvent('download')` 等待實際 download 事件，並對 `download.suggestedFilename()` 做副檔名與 `{chartno}_` 前綴斷言。

測試 SHALL 使用 mock data 中 chartno `A1234567`（陳志明）作為 fixture，因其涵蓋 Enzyme、Biomarker、DBS LysoGb3 等多個模組且資料穩定。測試 MUST NOT 讀取或解析下載內容本體，只驗證檔名與副檔名；這確保測試與後端/序列化實作細節解耦。

#### Scenario: CSV 匯出產生 zip
- **WHEN** 使用者搜尋 `A1234567`、開啟 PatientSummary 的「匯出」Dialog、選擇 CSV 格式、按下 Dialog 內的「匯出」確認鈕
- **THEN** Playwright SHALL 捕捉到一個 `download` 事件，且 `download.suggestedFilename()` SHALL 以 `.zip` 結尾並以 `A1234567_` 開頭

#### Scenario: JSON 匯出產生 json 檔
- **WHEN** 使用者在匯出 Dialog 選擇 JSON 格式並按下確認
- **THEN** Playwright SHALL 捕捉到一個 `download` 事件，且 `download.suggestedFilename()` SHALL 以 `.json` 結尾並以 `A1234567_` 開頭

#### Scenario: XLSX 匯出產生 xlsx 檔
- **WHEN** 使用者在匯出 Dialog 選擇 XLSX 格式並按下確認
- **THEN** Playwright SHALL 捕捉到一個 `download` 事件，且 `download.suggestedFilename()` SHALL 以 `.xlsx` 結尾並以 `A1234567_` 開頭

#### Scenario: 匯出測試檔名符合命名慣例
- **WHEN** 讀取 `frontend/tests/` 目錄
- **THEN** 三個檔案 SHALL 存在：`patient-export-csv.spec.ts`、`patient-export-json.spec.ts`、`patient-export-xlsx.spec.ts`

### Requirement: 統計功能 e2e 覆蓋

`frontend/tests/` SHALL 為單病人統計（`StatsDialog`）與族群統計（`CohortStatsPanel` tab）各提供至少一支 Playwright 測試。測試 MUST 驗證模組 / 欄位選擇後的輸出文字（n/mean/sd/min/max 或交叉表表頭），以防止統計函式或 UI 回退。

#### Scenario: 單病人統計 Dialog 顯示 n/mean/sd/min/max
- **WHEN** 使用者搜尋 `A1234567`、點 PatientSummary 的「統計」按鈕、在 Dialog 中選模組與數值欄位
- **THEN** Dialog SHALL 顯示 `n`、`mean`、`sd`、`min`、`max` 五個標籤與其對應數值；若選到無日期欄位的模組（如 `enzyme`），日期 input SHALL disabled 且顯示 helper text「此模組資料無採檢日期欄位」

#### Scenario: 族群統計 tab 顯示 5×3 交叉表
- **WHEN** 使用者切「條件查詢」模式、套用「酵素活性低下」模板、執行查詢、切到「族群統計」tab、在 `CohortStatsPanel` 選模組與數值欄位
- **THEN** 畫面 SHALL 顯示含表頭「年齡 \ 性別」與欄 `男`/`女`/`全部性別`、列 `0-17`/`18-39`/`40-59`/`60+`/`全部年齡` 的表格，以及「共 {N} 位病人」文字

#### Scenario: 統計測試檔名符合命名慣例
- **WHEN** 讀取 `frontend/tests/` 目錄
- **THEN** 兩個檔案 SHALL 存在：`patient-stats-dialog.spec.ts`、`cohort-stats-tab.spec.ts`

### Requirement: 下載事件斷言策略

任何驗證檔案下載的 e2e 測試 SHALL 使用 Playwright 的 `page.waitForEvent('download')` 模式，並以 `Promise.all` 包裹觸發動作以避免 race。測試 MUST NOT 讀取下載檔案的 binary 內容做深度比對；驗證限於 `suggestedFilename()` 的副檔名與已知 prefix。

#### Scenario: 下載事件用 Promise.all 包裹
- **WHEN** 審查任何使用 `waitForEvent('download')` 的測試
- **THEN** 該 `waitForEvent` 呼叫 SHALL 與觸發 click 動作在同一個 `Promise.all([...])` 中，確保下載事件不會在 listener 註冊前發生

#### Scenario: 不解析下載內容
- **WHEN** 審查 `frontend/tests/patient-export-*.spec.ts`
- **THEN** 測試 SHALL NOT 呼叫 `download.path()` 後讀取檔案 binary、解析 zip、解析 XLSX workbook 或 parse JSON；斷言限於 `download.suggestedFilename()` 的字串匹配
