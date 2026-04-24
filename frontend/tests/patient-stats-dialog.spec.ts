// spec: specs/export-and-stats.md (Scenario 2.1)
// seed: tests/seed.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Single-Patient Statistics Dialog', () => {
  test('shows n / mean / sd / min / max and disables date input for dateless modules', async ({
    page,
  }) => {
    // 1. Navigate to `/`.
    await page.goto('/');
    await expect(page.getByRole('heading', { name: '開始查詢' })).toBeVisible();

    // 2. Look up 陳志明 (A1234567).
    await page.getByPlaceholder('輸入病人姓名或病歷號').fill('A1234567');
    await page.getByRole('button', { name: '搜尋' }).click();
    await expect(page.getByText('陳志明').first()).toBeVisible();
    await expect(page.getByText('A1234567').first()).toBeVisible();

    // 3. Click PatientSummary 統計 trigger. The text "統計" also appears inside
    // the dialog (as a section label), so scope subsequent locators to the
    // dialog to stay unambiguous.
    await page.getByRole('button', { name: '統計' }).click();
    const dialog = page.getByRole('dialog');
    await expect(
      dialog.getByRole('heading', { name: '單病人統計 — 陳志明' }),
    ).toBeVisible();
    await expect(dialog.getByText('請選擇模組與欄位')).toBeVisible();

    // 4. Open the module Select (first combobox in the ModuleFieldPicker) and
    // pick "Enzyme · 酵素檢驗". Radix renders options in a portal — use a
    // page-scoped option query, not one scoped into the trigger.
    await dialog.getByRole('combobox').first().click();
    await page.getByRole('option', { name: 'Enzyme · 酵素檢驗' }).click();
    await expect(dialog.getByRole('combobox').first()).toContainText(
      'Enzyme · 酵素檢驗',
    );

    // 5. Enzyme has no date column → both date inputs are disabled.
    const dateInputs = dialog.locator('input[type="date"]');
    await expect(dateInputs).toHaveCount(2);
    await expect(dateInputs.nth(0)).toBeDisabled();
    await expect(dateInputs.nth(1)).toBeDisabled();

    // 6. Dateless helper text is visible.
    await expect(dialog.getByText('此模組資料無採檢日期欄位')).toBeVisible();

    // 7. Open the numeric column Select and pick MPS1.
    await dialog.getByRole('combobox').nth(1).click();
    await page.getByRole('option', { name: 'MPS1' }).click();
    await expect(dialog.getByRole('combobox').nth(1)).toContainText('MPS1');

    // 8–12. Stats output labels appear with adjacent numeric (or "—") values.
    await Promise.all(
      ['n', 'mean', 'sd', 'min', 'max'].map((label) =>
        expect(dialog.getByText(label, { exact: true })).toBeVisible(),
      ),
    );
  });
});
