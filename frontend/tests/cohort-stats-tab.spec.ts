// spec: specs/export-and-stats.md (Scenario 3.1)
// seed: tests/seed.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Cohort Statistics Tab', () => {
  test('renders 5×3 cross-tab with correct headers, row labels, and patient count', async ({
    page,
  }) => {
    // 1. Navigate to `/`.
    await page.goto('/');
    await expect(page.getByRole('heading', { name: '開始查詢' })).toBeVisible();

    // 2. Switch to 條件查詢 mode.
    await page.getByRole('button', { name: '條件查詢' }).first().click();
    await expect(page.getByRole('heading', { name: '條件查詢' })).toBeVisible();

    // 3. Apply the "酵素活性低下" template.
    await page.getByRole('button', { name: /酵素活性低下/ }).click();

    // 4. Execute the query; expect the 3 deficient-enzyme patients.
    await page.getByRole('button', { name: '執行條件查詢' }).click();
    await expect(
      page.getByText(/條件查詢（AND）.*命中.*3.*位病人/),
    ).toBeVisible();
    await expect(page.getByRole('cell', { name: 'A1234567' })).toBeVisible();
    await expect(page.getByRole('cell', { name: 'C3456789' })).toBeVisible();
    await expect(page.getByRole('cell', { name: 'D4567890' })).toBeVisible();

    // 5. Switch to 族群統計 tab.
    await page.getByRole('tab', { name: '族群統計' }).click();
    const cohortPanel = page.getByRole('tabpanel', { name: '族群統計' });

    // 6. Patient count label.
    await expect(cohortPanel.getByText('共 3 位病人')).toBeVisible();

    // 7. Column headers: 年齡 \ 性別, 男, 女, 全部性別.
    await expect(
      cohortPanel.getByRole('columnheader', { name: '年齡 \\ 性別' }),
    ).toBeVisible();
    await expect(
      cohortPanel.getByRole('columnheader', { name: '男' }),
    ).toBeVisible();
    await expect(
      cohortPanel.getByRole('columnheader', { name: '女' }),
    ).toBeVisible();
    await expect(
      cohortPanel.getByRole('columnheader', { name: '全部性別' }),
    ).toBeVisible();

    // 8. Row labels for the five age buckets.
    await Promise.all(
      ['0-17', '18-39', '40-59', '60+', '全部年齡'].map((row) =>
        expect(cohortPanel.getByRole('cell', { name: row })).toBeVisible(),
      ),
    );

    // 9. Pick the Enzyme module; Radix portal renders options at page scope.
    await cohortPanel.getByRole('combobox').first().click();
    await page.getByRole('option', { name: 'Enzyme · 酵素檢驗' }).click();
    await expect(cohortPanel.getByRole('combobox').first()).toContainText(
      'Enzyme · 酵素檢驗',
    );

    // 10. Pick the MPS1 numeric column.
    await cohortPanel.getByRole('combobox').nth(1).click();
    await page.getByRole('option', { name: 'MPS1' }).click();
    await expect(cohortPanel.getByRole('combobox').nth(1)).toContainText(
      'MPS1',
    );

    // 11. Patient count text remains stable after selection.
    await expect(cohortPanel.getByText('共 3 位病人')).toBeVisible();
  });
});
