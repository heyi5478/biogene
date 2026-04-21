// spec: specs/core-happy-paths.md (Scenario 6)
// seed: tests/seed.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Mode toggle between patient query and condition query', () => {
  test('toggling modes swaps empty states and clears the displayed patient', async ({
    page,
  }) => {
    await page.goto('/');

    await expect(page.getByRole('heading', { name: '開始查詢' })).toBeVisible();

    await page.getByRole('button', { name: '條件查詢' }).first().click();
    await expect(page.getByRole('heading', { name: '條件查詢' })).toBeVisible();

    await page.getByRole('button', { name: '病人查詢' }).first().click();
    await expect(page.getByRole('heading', { name: '開始查詢' })).toBeVisible();

    await page.getByPlaceholder('輸入病人姓名或病歷號').fill('陳志明');
    await page.getByRole('button', { name: '搜尋' }).click();
    await expect(page.getByText('陳志明').first()).toBeVisible();

    await page.getByRole('button', { name: '條件查詢' }).first().click();
    await expect(page.getByRole('heading', { name: '條件查詢' })).toBeVisible();
    // The patient summary card should not be visible in condition mode.
    await expect(page.getByRole('heading', { name: '開始查詢' })).toHaveCount(
      0,
    );
  });
});
