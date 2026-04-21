// spec: specs/core-happy-paths.md (Scenario 4)
// seed: tests/seed.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Condition query: template + AND execution', () => {
  test('Biomarker 異常 template runs AND query and returns 陳志明', async ({
    page,
  }) => {
    await page.goto('/');

    await page.getByRole('button', { name: '條件查詢' }).first().click();

    await expect(page.getByRole('heading', { name: '條件查詢' })).toBeVisible();

    await page.getByRole('button', { name: /Biomarker 異常/ }).click();

    await page.getByRole('button', { name: '執行條件查詢' }).click();

    // Match the condition summary line; uses non-breaking spaces around the
    // count, so allow flexible whitespace.
    await expect(
      page.getByText(/條件查詢（AND）.*命中.*1.*位病人/),
    ).toBeVisible();

    await expect(page.getByRole('cell', { name: 'A1234567' })).toBeVisible();
    await expect(page.getByRole('cell', { name: '陳志明' })).toBeVisible();
  });
});
