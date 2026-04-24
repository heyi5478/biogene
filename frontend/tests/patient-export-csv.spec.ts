// spec: specs/export-and-stats.md (Scenario 1.1)
// seed: tests/seed.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Patient Data Export', () => {
  test('CSV export → zip download', async ({ page }) => {
    // 1. Navigate to `/`.
    await page.goto('/');
    await expect(page.getByRole('heading', { name: '開始查詢' })).toBeVisible();

    // 2. Fill the chart-number input.
    await page.getByPlaceholder('輸入病人姓名或病歷號').fill('A1234567');

    // 3. Click 搜尋; expect 陳志明 / A1234567.
    await page.getByRole('button', { name: '搜尋' }).click();
    await expect(page.getByText('陳志明').first()).toBeVisible();
    await expect(page.getByText('A1234567').first()).toBeVisible();

    // 4. Click PatientSummary 匯出 trigger.
    await page.getByRole('button', { name: '匯出' }).click();

    // Scope subsequent locators to the opened dialog to disambiguate the
    // 匯出 trigger button from the 匯出 confirm button inside the dialog.
    const dialog = page.getByRole('dialog');
    await expect(
      dialog.getByRole('heading', { name: '匯出 — 陳志明' }),
    ).toBeVisible();

    // 5. CSV (zip) radio is the default; confirm checked state.
    await expect(
      dialog.getByRole('radio', { name: 'CSV (zip)' }),
    ).toBeChecked();

    // 6. Wrap waitForEvent and click in Promise.all to avoid the race where
    // the download fires before the listener is registered.
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      dialog.getByRole('button', { name: '匯出' }).click(),
    ]);

    // 7–8. Filename assertions: {chartno}_ prefix and .zip suffix.
    const filename = download.suggestedFilename();
    expect(filename.startsWith('A1234567_')).toBe(true);
    expect(filename.endsWith('.zip')).toBe(true);
  });
});
