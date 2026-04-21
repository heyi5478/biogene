// spec: specs/core-happy-paths.md (Scenario 2)
// seed: tests/seed.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Patient query: lookup by chart number', () => {
  test('looking up B2345678 returns 林雅婷 and the lab tab reveals lab modules', async ({
    page,
  }) => {
    await page.goto('/');

    await page.getByPlaceholder('輸入病人姓名或病歷號').fill('B2345678');
    await page.getByRole('button', { name: '搜尋' }).click();

    await expect(page.getByText('林雅婷').first()).toBeVisible();
    await expect(page.getByText('B2345678').first()).toBeVisible();
    await expect(page.getByText(/Phenylketonuria/)).toBeVisible();

    await page.getByRole('tab', { name: '檢驗' }).click();

    // After clicking 檢驗 the lab section anchors render; assert at least
    // one lab module title is present (AA — 胺基酸 or MS/MS).
    await expect(page.getByText(/AA|MS\/MS|胺基酸/).first()).toBeVisible();
  });
});
