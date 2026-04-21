# 基因醫學整合查詢中心 — Core Happy Path E2E Test Plan

**Application:** `http://localhost:8080` (Vite dev server, served via Playwright `webServer`)
**Mode:** Pure mock data (frontend-only; no backend), 5 fixed patients in `src/data/mockData.ts`
**Browser:** Chromium only
**Seed:** `tests/seed.spec.ts` (navigates to `/` and asserts URL)

## Scope

This plan covers the 6 core user journeys of the integrated genetic medical query center as confirmed in the change proposal. It deliberately excludes edge cases (invalid input, keyboard navigation, RWD), per the change scope.

**Mock patient fixtures used by these scenarios:**

| chartno  | name   | sex | diagnosis                             | notable lab fixtures                   |
| -------- | ------ | --- | ------------------------------------- | -------------------------------------- |
| A1234567 | 陳志明 | 男  | Fabry disease (E75.21)                | DBS LysoGb3 = 12.8; Enzyme = Deficient |
| B2345678 | 林雅婷 | 女  | Phenylketonuria (E70.0)               | AA Phe = 890 / 1120 (both Abnormal)    |
| C3456789 | 張偉翔 | 男  | Mucopolysaccharidosis type II (E76.1) | MPS2 = 1.2; GAG DMGGAG = 425.8         |
| D4567890 | 黃淑芬 | 女  | Gaucher disease type 1 (E75.22)       | Enzyme = Deficient                     |
| E5678901 | 王建國 | 男  | AADC deficiency (E70.8)               | AA in CSF; AADC samples                |

## Conventions

- All scenarios assume a fresh page load (`page.goto('/')`) — the app has no persistent state, no auth, no global side effects.
- All Chinese strings appear verbatim in the UI; tests must use exact-match `getByText` / `getByRole` queries.
- The "搜尋" string appears in the input placeholder, the empty-state header ("開始查詢"), and the submit button. Tests must use `getByRole('button', { name: '搜尋' })` for the submit button to avoid ambiguity.
- The "找不到符合條件的病人" empty-state appears in BOTH patient mode (`Index.tsx`) and condition mode (`ConditionResults.tsx`); tests in different scopes must not cross-assert.
- Radix UI `Select` renders options in a portal — use `page.getByRole('option', { name: ... })` rather than scoping into the trigger.

---

## Scenario 1: Search a Patient by Name

**Goal:** Verify name-based search returns matching patients and renders the patient summary card with tabs.

**Suggested file:** `tests/patient-search-by-name.spec.ts`

**Starting state:** Fresh page load, default "病人查詢" mode.

**Steps:**

1. Navigate to `/`.
2. Verify the empty state shows the heading "開始查詢".
3. Locate the input with placeholder "輸入病人姓名或病歷號" and fill in `陳志明`.
4. Click the button "搜尋".
5. Verify the search summary line appears (it includes the submitted query and the patient count).
6. Verify the patient summary section shows `陳志明` and the chart number `A1234567`.
7. Verify the tab list is visible with tabs "全部", "基本資料", "門診", "檢驗", "檢體" — and "全部" is the active tab.

**Success criteria:**

- The empty-state "開始查詢" heading is no longer in view after submitting.
- The patient summary contains the literal strings `陳志明` and `A1234567`.
- All five tab triggers are visible.

---

## Scenario 2: Look Up a Patient by Chart Number

**Goal:** Verify exact chart-number lookup yields a single result and the result tabs render.

**Suggested file:** `tests/patient-lookup-by-chartno.spec.ts`

**Starting state:** Fresh page load, default "病人查詢" mode.

**Steps:**

1. Navigate to `/`.
2. Fill the patient search input with `B2345678`.
3. Click the button "搜尋".
4. Verify the patient summary shows `林雅婷` and `B2345678`.
5. Verify the diagnosis text "Phenylketonuria" appears somewhere on the page (in the patient summary).
6. Click the tab "檢驗".
7. Verify a heading or section related to lab modules (e.g., text "AA — 胺基酸" or "MS/MS") becomes visible — proving the tab actually switched the lab view in.

**Success criteria:**

- Single patient result rendered (no patient-list table).
- "林雅婷" + "B2345678" both visible after submit.
- "檢驗" tab activation reveals lab module content.

---

## Scenario 3: Empty Result for Unknown Search String

**Goal:** Verify the patient-mode empty result message renders for a query with no match.

**Suggested file:** `tests/patient-search-empty.spec.ts`

**Starting state:** Fresh page load, default "病人查詢" mode.

**Steps:**

1. Navigate to `/`.
2. Fill the patient search input with `XYZ_NO_SUCH_PATIENT`.
3. Click the button "搜尋".
4. Verify the heading "找不到符合條件的病人" is visible.
5. Verify the helper text "請確認病人姓名或病歷號是否正確" is visible.

**Success criteria:**

- Both empty-state strings render.
- No patient summary card or tab list appears.

> **Selector note:** "找不到符合條件的病人" also appears in condition-query mode (`ConditionResults.tsx`). Because this scenario stays in patient mode, the assertion is unambiguous in this file. Do not combine this assertion with the condition-mode flow.

---

## Scenario 4: Apply a Condition Template and Run an AND Query

**Goal:** Verify mode switch to condition query, template application, AND-logic execution, and result table rendering.

**Suggested file:** `tests/condition-query-template-and.spec.ts`

**Starting state:** Fresh page load, default "病人查詢" mode.

**Steps:**

1. Navigate to `/`.
2. Click the mode-toggle button "條件查詢".
3. Verify the condition-mode empty state heading "條件查詢" is visible.
4. Click the template button labeled "Biomarker 異常" (its description "篩選 DBS LysoGb3 > 5 的病人" is visible).
5. Verify the logic toggle "AND（全部符合）" is the active state (Biomarker 異常 template uses AND).
6. Click the button "執行條件查詢".
7. Verify the condition summary text matches `條件查詢（AND）· 命中 1 位病人` (one match expected — patient 陳志明 has DBS LysoGb3 = 12.8).
8. Verify the result table contains a row with `A1234567` and `陳志明`.

**Success criteria:**

- Template application populates conditions and logic without manual selection.
- "執行條件查詢" runs and renders a one-row result table for this fixture.

---

## Scenario 5: Drill into a Patient from Condition Results

**Goal:** Verify clicking "查看" on a condition-results row opens the patient detail panel and a back button.

**Suggested file:** `tests/condition-drill-into-patient.spec.ts`

**Starting state:** Fresh page load, default "病人查詢" mode.

**Steps:**

1. Navigate to `/`.
2. Click the mode-toggle button "條件查詢".
3. Click the template button "酵素活性低下" (description "篩選 Enzyme result 為 Deficient 的病人").
4. Click "執行條件查詢".
5. Verify the result table includes `陳志明` (A1234567), `張偉翔` (C3456789), and `黃淑芬` (D4567890) — three matches.
6. Within the row for `A1234567`, click the action button "查看".
7. Verify the patient summary now shows `陳志明` and `A1234567`.
8. Verify the back button "返回條件查詢結果" is visible.
9. Click "返回條件查詢結果".
10. Verify the result table is visible again with all three patients listed.

**Success criteria:**

- "查看" navigates to the patient detail view.
- "返回條件查詢結果" returns to the result list with state preserved.

---

## Scenario 6: Toggle Between Patient Query and Condition Query Modes

**Goal:** Verify mode switching between "病人查詢" and "條件查詢" preserves the per-mode empty states and clears any drilled-in patient.

**Suggested file:** `tests/mode-toggle.spec.ts`

**Starting state:** Fresh page load, default "病人查詢" mode.

**Steps:**

1. Navigate to `/`.
2. Verify the patient-mode empty heading "開始查詢" is visible.
3. Click the mode toggle "條件查詢".
4. Verify the condition-mode empty heading "條件查詢" is visible (the empty-state H2, not just the toggle button text).
5. Click the mode toggle "病人查詢".
6. Verify the patient-mode empty heading "開始查詢" is visible again.
7. Fill the patient search input with `陳志明`, click "搜尋", and verify the patient summary shows `陳志明`.
8. Click the mode toggle "條件查詢".
9. Verify the condition-mode empty heading "條件查詢" is visible (the previously displayed patient summary should not appear).

**Success criteria:**

- Mode toggle visibly switches the right panel between the two empty states.
- Switching to condition mode after a patient was displayed clears the patient view (per `setConditionPatient(null)` in `handleModeChange`).

---

## Out of Scope (Deferred to Future Changes)

- Form validation and error toasts
- Keyboard navigation, focus management, accessibility audits
- Responsive / mobile layout
- Network stubbing — the app is fully client-side until backend services land
- Visual regression / screenshot baselines
- Multi-browser (Firefox, WebKit) — only Chromium is enabled in this iteration
