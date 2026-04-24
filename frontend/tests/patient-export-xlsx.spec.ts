// spec: specs/export-and-stats.md (Scenario 1.3)
// seed: tests/seed.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Patient Data Export', () => {
  test('XLSX export → xlsx file download', async ({ page }) => {
    // 1. Navigate to `/`.
    await page.goto('/');
    await expect(page.getByRole('heading', { name: '開始查詢' })).toBeVisible();

    // 2. Fill input and 搜尋 for A1234567 / 陳志明.
    await page.getByPlaceholder('輸入病人姓名或病歷號').fill('A1234567');
    await page.getByRole('button', { name: '搜尋' }).click();
    await expect(page.getByText('陳志明').first()).toBeVisible();
    await expect(page.getByText('A1234567').first()).toBeVisible();

    // 3. Open the export dialog.
    await page.getByRole('button', { name: '匯出' }).click();
    const dialog = page.getByRole('dialog');
    await expect(
      dialog.getByRole('heading', { name: '匯出 — 陳志明' }),
    ).toBeVisible();

    // 4. Switch format to XLSX.
    await dialog.getByRole('radio', { name: 'XLSX' }).click();
    await expect(dialog.getByRole('radio', { name: 'XLSX' })).toBeChecked();

    // 5. Fire download via Promise.all.
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      dialog.getByRole('button', { name: '匯出' }).click(),
    ]);

    // 6–7. Filename assertions; do not parse the workbook body.
    const filename = download.suggestedFilename();
    expect(filename.startsWith('A1234567_')).toBe(true);
    expect(filename.endsWith('.xlsx')).toBe(true);
  });
});
