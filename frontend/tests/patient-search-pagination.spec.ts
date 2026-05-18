import { test, expect } from '@playwright/test';

// The mock dataset holds 100 patients, 63 of them surnamed 王 — enough to
// span two pages at PATIENT_PAGE_SIZE = 50. These specs exercise the
// integration end of pagination; the pager's own page-math and disabled
// states are unit-tested in src/components/PatientListPager.test.tsx.
test.describe('patient search pagination', () => {
  test('a multi-page result set renders a working pager', async ({ page }) => {
    await page.goto('/');

    await page.getByPlaceholder('輸入病人姓名或病歷號').fill('王');
    await page.getByRole('button', { name: '搜尋' }).click();

    // 63 hits at page size 50 → two pages; page one shows 50 rows.
    await expect(page.getByText(/找到 63 位病人/)).toBeVisible();
    await expect(page.getByTestId('patient-row')).toHaveCount(50);

    const pager = page.getByRole('navigation', { name: 'pagination' });
    await expect(pager).toBeVisible();

    // Selecting page 2 swaps the list to the remaining 13 patients while
    // the hit-count summary keeps reporting the full total.
    await pager.getByText('2', { exact: true }).click();
    await expect(page.getByTestId('patient-row')).toHaveCount(13);
    await expect(page.getByText(/找到 63 位病人/)).toBeVisible();
  });

  test('a single-page result set renders no pager', async ({ page }) => {
    await page.goto('/');

    await page.getByPlaceholder('輸入病人姓名或病歷號').fill('外院');
    await page.getByRole('button', { name: '搜尋' }).click();

    // 18 hits ≤ one page → the list renders but no pager.
    await expect(page.getByText(/找到 18 位病人/)).toBeVisible();
    await expect(page.getByTestId('patient-row')).toHaveCount(18);
    await expect(
      page.getByRole('navigation', { name: 'pagination' }),
    ).toHaveCount(0);
  });
});
