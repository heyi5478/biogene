// spec: specs/core-happy-paths.md (Scenario 3)
// seed: tests/seed.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Patient query: empty result for unknown query', () => {
  test('an unknown query shows the empty-state message', async ({ page }) => {
    await page.goto('/');

    await page
      .getByPlaceholder('輸入病人姓名或病歷號')
      .fill('XYZ_NO_SUCH_PATIENT');
    await page.getByRole('button', { name: '搜尋' }).click();

    await expect(
      page.getByRole('heading', { name: '找不到符合條件的病人' }),
    ).toBeVisible();
    await expect(
      page.getByText('請確認病人姓名或病歷號是否正確'),
    ).toBeVisible();
  });
});
