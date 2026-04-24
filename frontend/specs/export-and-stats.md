# 基因醫學整合查詢中心 — Export and Stats E2E Test Plan

## Application Overview

**Application:** `http://localhost:8080` (Vite dev server, served via Playwright `webServer`)
**Mode:** Pure mock data (frontend-only; no backend), 5 fixed patients in `src/data/mockData.ts`
**Browser:** Chromium only
**Seed:** `tests/seed.spec.ts` (navigates to `/` and asserts URL)

This plan covers three new user-facing features of the integrated genetic medical query center: patient data export (CSV, JSON, XLSX download), a single-patient statistics dialog, and a cohort statistics cross-tab panel. It deliberately excludes edge cases (invalid input, keyboard navigation, RWD), per the change scope.

**Mock patient fixtures used by these scenarios:**

| chartno  | name   | sex | diagnosis                             | notable lab fixtures                  |
| -------- | ------ | --- | ------------------------------------- | ------------------------------------- |
| A1234567 | 陳志明 | 男  | Fabry disease (E75.21)                | Enzyme MPS1 = 2.1; Enzyme-MPS2 = 45.8 |
| C3456789 | 張偉翔 | 男  | Mucopolysaccharidosis type II (E76.1) | Enzyme Result = Deficient             |
| D4567890 | 黃淑芬 | 女  | Gaucher disease type 1 (E75.22)       | Enzyme Result = Deficient             |

## Conventions

- All scenarios assume a fresh page load (`page.goto('/')`) — the app has no persistent state, no auth, no global side effects.
- All Chinese strings appear verbatim in the UI; tests must use exact-match `getByText` / `getByRole` queries.
- **All locators MUST use `getByRole` / `getByText` / `getByPlaceholder` / `getByLabel` — no `data-testid` attributes.**
- After opening the export Dialog, scope further locators with `page.getByRole('dialog')` to disambiguate the Dialog's "匯出" confirm button from the PatientSummary trigger button with the same label.
- Radix UI `Select` renders options in a portal — use `page.getByRole('option', { name: ... })` to pick options; do NOT scope option locators inside the trigger element.
- **All download tests MUST wrap `page.waitForEvent('download')` and the confirm click inside the same `Promise.all([...])` call** to avoid race conditions where the download event fires before the listener is registered.
- Tests MUST NOT call `download.path()` to read binary content, and MUST NOT parse zip / xlsx workbook / JSON payload. Assertions are limited to `download.suggestedFilename()` string checks.
- Each `test()` MUST start with `await page.goto('/');`.
- Browser and setup match the existing seed: Chromium only, `baseURL` `http://localhost:8080`, seed file `tests/seed.spec.ts`.

## Test Scenarios

### 1. Patient Data Export

**Seed:** `tests/seed.spec.ts`

#### 1.1. CSV export → zip download

**File:** `tests/patient-export-csv.spec.ts`

**Steps:**

1. Navigate to `/`.
   - expect: The empty-state heading "開始查詢" is visible.

2. Fill the input with placeholder "輸入病人姓名或病歷號" with `A1234567`.
3. Click the button `getByRole('button', { name: '搜尋' })`.
   - expect: The patient summary heading "陳志明" and the chart number "A1234567" are visible.

4. Click the PatientSummary action button "匯出".
   - expect: A dialog with heading "匯出 — 陳志明" appears.

5. Within `page.getByRole('dialog')`, verify the radio button "CSV (zip)" is already checked (it is the default selection).
   - expect: The "CSV (zip)" radio is in a checked state.

6. Using `Promise.all([page.waitForEvent('download'), page.getByRole('dialog').getByRole('button', { name: '匯出' }).click()])`, fire the download and capture the `download` object.
   - expect: The browser emits a download event without error.

7. Assert `download.suggestedFilename().startsWith('A1234567_')`.
   - expect: The filename prefix matches `A1234567_`.

8. Assert `download.suggestedFilename().endsWith('.zip')`.
   - expect: The file extension is `.zip`.

#### 1.2. JSON export → json file download

**File:** `tests/patient-export-json.spec.ts`

**Steps:**

1. Navigate to `/`.
   - expect: The empty-state heading "開始查詢" is visible.

2. Fill the input with placeholder "輸入病人姓名或病歷號" with `A1234567` and click the button "搜尋".
   - expect: The patient summary for "陳志明" (A1234567) is displayed.

3. Click the PatientSummary action button "匯出".
   - expect: A dialog with heading "匯出 — 陳志明" appears.

4. Within `page.getByRole('dialog')`, click the radio button "JSON" to select JSON format.
   - expect: The "JSON" radio becomes checked.

5. Using `Promise.all([page.waitForEvent('download'), page.getByRole('dialog').getByRole('button', { name: '匯出' }).click()])`, fire the download and capture the `download` object.
   - expect: The browser emits a download event without error.

6. Assert `download.suggestedFilename().startsWith('A1234567_')`.
   - expect: The filename prefix matches `A1234567_`.

7. Assert `download.suggestedFilename().endsWith('.json')`.
   - expect: The file extension is `.json`. The test does NOT read or parse the JSON file content.

#### 1.3. XLSX export → xlsx file download

**File:** `tests/patient-export-xlsx.spec.ts`

**Steps:**

1. Navigate to `/`.
   - expect: The empty-state heading "開始查詢" is visible.

2. Fill the input with placeholder "輸入病人姓名或病歷號" with `A1234567` and click the button "搜尋".
   - expect: The patient summary for "陳志明" (A1234567) is displayed.

3. Click the PatientSummary action button "匯出".
   - expect: A dialog with heading "匯出 — 陳志明" appears.

4. Within `page.getByRole('dialog')`, click the radio button "XLSX" to select XLSX format.
   - expect: The "XLSX" radio becomes checked.

5. Using `Promise.all([page.waitForEvent('download'), page.getByRole('dialog').getByRole('button', { name: '匯出' }).click()])`, fire the download and capture the `download` object.
   - expect: The browser emits a download event without error.

6. Assert `download.suggestedFilename().startsWith('A1234567_')`.
   - expect: The filename prefix matches `A1234567_`.

7. Assert `download.suggestedFilename().endsWith('.xlsx')`.
   - expect: The file extension is `.xlsx`. The test does NOT read or parse the xlsx workbook content.

### 2. Single-Patient Statistics Dialog

**Seed:** `tests/seed.spec.ts`

#### 2.1. Stats dialog shows n / mean / sd / min / max values and disables date input for dateless modules

**File:** `tests/patient-stats-dialog.spec.ts`

**Steps:**

1. Navigate to `/`.
   - expect: The empty-state heading "開始查詢" is visible.

2. Fill the input with placeholder "輸入病人姓名或病歷號" with `A1234567` and click "搜尋".
   - expect: The patient summary for "陳志明" (A1234567) is displayed.

3. Click the PatientSummary action button "統計". (Note: the string "統計" appears both as the trigger button label and as text inside the opened dialog. Use `getByRole('button', { name: '統計' })` for the trigger; scope all subsequent locators to `page.getByRole('dialog')` to stay within the dialog context.)
   - expect: A dialog with heading "單病人統計 — 陳志明" is open. The statistics output area shows the placeholder text "請選擇模組與欄位".

4. Within `page.getByRole('dialog')`, click the module combobox (showing "選擇模組"). Radix Select renders options in a portal, so use `page.getByRole('option', { name: 'Enzyme · 酵素檢驗' })` — not scoped into the trigger — to select the Enzyme module.
   - expect: The module combobox displays "Enzyme · 酵素檢驗".

5. Assert that the two `textbox` inputs in the "日期區間" section of the dialog are disabled.
   - expect: Both date-range inputs are disabled, because the Enzyme module has no date column.

6. Within `page.getByRole('dialog')`, assert `page.getByText('此模組資料無採檢日期欄位')` is visible.
   - expect: The helper text "此模組資料無採檢日期欄位" is visible inside the dialog.

7. Click the numeric column combobox (showing "選擇欄位"). Use `page.getByRole('option', { name: 'MPS1' })` to select the "MPS1" column.
   - expect: The numeric column combobox displays "MPS1".

8. Within `page.getByRole('dialog')`, assert the statistics output section contains the label "n" and an adjacent numeric count cell.
   - expect: The label "n" and a numeric value (e.g. "1") are both visible.

9. Within `page.getByRole('dialog')`, assert the label "mean" is visible with an adjacent numeric value.
   - expect: The label "mean" and a decimal value (e.g. "2.10") are both visible.

10. Within `page.getByRole('dialog')`, assert the label "sd" is visible.
    - expect: The label "sd" is visible (value may be "—" when n = 1).

11. Within `page.getByRole('dialog')`, assert the label "min" and its adjacent value are visible.
    - expect: The label "min" and a numeric value are both visible.

12. Within `page.getByRole('dialog')`, assert the label "max" and its adjacent value are visible.
    - expect: The label "max" and a numeric value are both visible. No cell is blank.

### 3. Cohort Statistics Tab

**Seed:** `tests/seed.spec.ts`

#### 3.1. Cohort stats tab renders a 5×3 cross-tab with correct headers, row labels, and patient count

**File:** `tests/cohort-stats-tab.spec.ts`

**Steps:**

1. Navigate to `/`.
   - expect: The empty-state heading "開始查詢" is visible.

2. Click the mode-toggle button "條件查詢".
   - expect: The condition-query panel becomes active. The empty-state heading "條件查詢" is visible in the main panel.

3. Click the template button "酵素活性低下" (its description "篩選 Enzyme result 為 Deficient 的病人" is visible alongside it).
   - expect: The template is applied. A condition row showing Enzyme / Result / 等於 / Deficient appears in the sidebar.

4. Click the button "執行條件查詢".
   - expect: The main panel renders a tablist with tabs "名單" and "族群統計". The "名單" tab is active and shows "條件查詢（AND）· 命中 3 位病人". The result table contains rows for A1234567 (陳志明), C3456789 (張偉翔), and D4567890 (黃淑芬).

5. Click the tab "族群統計".
   - expect: The "族群統計" tabpanel becomes active. A module combobox (showing "選擇模組") and a disabled column combobox (showing "選擇欄位") are visible.

6. Assert the patient count text "共 3 位病人" is visible within the tabpanel.
   - expect: The text "共 3 位病人" is visible.

7. Assert the cross-tab table column headers: use `page.getByRole('columnheader', { name: '年齡 \\ 性別' })`, `getByRole('columnheader', { name: '男' })`, `getByRole('columnheader', { name: '女' })`, and `getByRole('columnheader', { name: '全部性別' })`.
   - expect: All four column header cells — "年齡 \ 性別", "男", "女", "全部性別" — are visible.

8. Assert the cross-tab table row labels: use `page.getByRole('cell', { name: '0-17' })`, "18-39", "40-59", "60+", and "全部年齡".
   - expect: All five age-band row label cells are visible in the table body.

9. Click the module combobox in the 族群統計 tabpanel. Use `page.getByRole('option', { name: 'Enzyme · 酵素檢驗' })` to select the Enzyme module.
   - expect: The module combobox shows "Enzyme · 酵素檢驗". The numeric column combobox becomes enabled.

10. Click the column combobox (showing "選擇欄位"). Use `page.getByRole('option', { name: 'MPS1' })` to select "MPS1".
    - expect: The column combobox shows "MPS1". The cross-tab cells are populated with aggregated statistics strings (e.g. mean ± sd and n-count format).

11. Assert the patient count text "共 3 位病人" is still visible after module and column selection.
    - expect: The text "共 3 位病人" remains visible.

---

## Out of Scope (Deferred to Future Changes)

- Form validation and error toasts (e.g., trying to export with no patient loaded).
- Keyboard navigation, focus management, accessibility audits.
- Responsive / mobile layout.
- Network stubbing — the app is fully client-side; downloads are generated in-browser.
- Visual regression / screenshot baselines.
- Multi-browser (Firefox, WebKit) — only Chromium is enabled.
- Parsing the contents of any downloaded file (zip, JSON payload, XLSX workbook). Assertions are limited to `download.suggestedFilename()` string matching.
- Statistical correctness of computed values beyond presence — tests confirm the n / mean / sd / min / max labels and that some numeric value renders, but do not assert exact values (those are covered by unit tests).
- Edge cases around empty cohorts (zero matching patients) or extreme age boundaries.
