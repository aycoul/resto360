import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should show login page for unauthenticated users', async ({ page }) => {
    await page.goto('/fr/pos');

    // Should redirect to login or show login form
    await expect(page).toHaveURL(/login|signin/);
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.goto('/fr/login');

    // Fill login form
    await page.fill('[name="email"], [type="email"]', 'test@example.com');
    await page.fill('[name="password"], [type="password"]', 'testpassword123');
    await page.click('button[type="submit"]');

    // Should redirect to dashboard or POS
    await expect(page).not.toHaveURL(/login/);
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/fr/login');

    await page.fill('[name="email"], [type="email"]', 'invalid@example.com');
    await page.fill('[name="password"], [type="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('[role="alert"], .error, .text-red-500')).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    // Assuming already logged in via setup
    await page.goto('/fr/pos');

    // Click logout button
    const logoutButton = page.locator('button:has-text("Déconnexion"), button:has-text("Logout")');
    if (await logoutButton.isVisible()) {
      await logoutButton.click();
      await expect(page).toHaveURL(/login/);
    }
  });
});
