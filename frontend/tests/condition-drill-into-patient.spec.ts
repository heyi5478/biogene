// spec: specs/core-happy-paths.md (Scenario 5)
// seed: tests/seed.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Condition query: drill into patient detail', () => {
  test('clicking 查看 in result row opens patient detail; back returns to list', async ({
    page,
  }) => {
    await page.goto('/');

    await page.getByRole('button', { name: '條件查詢' }).first().click();
    await page.getByRole('button', { name: /酵素活性低下/ }).click();
    await page.getByRole('button', { name: '執行條件查詢' }).click();

    await expect(page.getByRole('cell', { name: 'A1234567' })).toBeVisible();
    await expect(page.getByRole('cell', { name: 'C3456789' })).toBeVisible();
    await expect(page.getByRole('cell', { name: 'D4567890' })).toBeVisible();

    const targetRow = page.getByRole('row', { name: /A1234567/ });
    await targetRow.getByRole('button', { name: '查看' }).click();

    await expect(page.getByText('A1234567')).toBeVisible();
    await expect(page.getByText('陳志明').first()).toBeVisible();
    await expect(
      page.getByRole('button', { name: '返回條件查詢結果' }),
    ).toBeVisible();

    await page.getByRole('button', { name: '返回條件查詢結果' }).click();

    await expect(page.getByRole('cell', { name: 'A1234567' })).toBeVisible();
    await expect(page.getByRole('cell', { name: 'C3456789' })).toBeVisible();
    await expect(page.getByRole('cell', { name: 'D4567890' })).toBeVisible();
  });
});
