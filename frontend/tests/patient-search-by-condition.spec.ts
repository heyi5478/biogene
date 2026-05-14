// spec: openspec/changes/server-side-patient-search/specs/frontend-patient-data/spec.md
// Scenario: "Condition results come from the server"
// seed: tests/seed.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Condition query: server-side basic.diagnosis contains Fabry', () => {
  test('configuring basic / diagnosis / contains / "Fabry" returns the matching patient', async ({
    page,
  }) => {
    await page.goto('/');

    // Switch to condition query mode.
    await page.getByRole('button', { name: '條件查詢' }).first().click();
    await expect(page.getByRole('heading', { name: '條件查詢' })).toBeVisible();

    // Add a fresh condition row.
    await page.getByRole('button', { name: '新增條件' }).click();

    // Module: pick "基本資料".
    await page.getByRole('combobox').filter({ hasText: '選擇模組' }).click();
    await page.getByRole('option', { name: '基本資料 — 基本資料' }).click();

    // Field: pick "主診斷". Default operator for text fields is `contains`.
    await page.getByRole('combobox').filter({ hasText: '選擇欄位' }).click();
    await page.getByRole('option', { name: '主診斷' }).click();

    // Value.
    await page.getByPlaceholder('值', { exact: true }).fill('Fabry');

    // Execute the search — server-driven, fires POST /patients/condition-query.
    await page.getByRole('button', { name: '執行條件查詢' }).click();

    // The result table shows 命中 1 位 with 陳志明 + Fabry diagnosis cell.
    await expect(
      page.getByText(/條件查詢（AND）.*命中.*1.*位病人/),
    ).toBeVisible();
    await expect(page.getByRole('cell', { name: '陳志明' })).toBeVisible();
    await expect(
      page.getByRole('cell', { name: 'Fabry disease (E75.21)', exact: true }),
    ).toBeVisible();
  });
});
