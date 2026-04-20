import { test, expect } from '@playwright/test';

test.describe('Test group', () => {
  test('seed', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/localhost:8080/);
  });
});
