// spec: specs/core-happy-paths.md (Scenario 1)
// seed: tests/seed.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Patient query: search by name', () => {
  test('searching for 陳志明 reveals the patient summary and tabs', async ({
    page,
  }) => {
    await page.goto('/');

    await expect(page.getByRole('heading', { name: '開始查詢' })).toBeVisible();

    await page.getByPlaceholder('輸入病人姓名或病歷號').fill('陳志明');
    await page.getByRole('button', { name: '搜尋' }).click();

    await expect(page.getByText('A1234567').first()).toBeVisible();
    await expect(page.getByText('陳志明').first()).toBeVisible();

    await expect(page.getByRole('tab', { name: '全部' })).toBeVisible();
    await expect(page.getByRole('tab', { name: '基本資料' })).toBeVisible();
    await expect(page.getByRole('tab', { name: '門診' })).toBeVisible();
    await expect(page.getByRole('tab', { name: '檢驗' })).toBeVisible();
    await expect(page.getByRole('tab', { name: '檢體' })).toBeVisible();
  });
});
