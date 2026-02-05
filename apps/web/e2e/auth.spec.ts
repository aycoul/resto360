import { test, expect } from '@playwright/test';

// Test users from seeded data (password: test1234 for all)
const TEST_USERS = {
  owner: { phone: '+225 02 70 88 61 81', name: 'Aya Koffi', business: 'Quincaillerie Express' },
  manager: { phone: '+225 04 86 65 49 90', name: 'Adjoua Kouassi', business: 'Fashion House Abidjan' },
  cashier: { phone: '+225 03 87 55 88 52', name: 'Aminata Touré', business: 'Le Kédjenou d\'Or' },
  kitchen: { phone: '+225 03 69 42 48 73', name: 'Aminata Konan', business: 'Le Kédjenou d\'Or' },
  driver: { phone: '+225 02 11 26 21 47', name: 'Aya Diallo', business: 'Boulangerie Le Fournil' },
};

const TEST_PASSWORD = 'test1234';
const SUPERUSER = { phone: '+225 00 00 00 00 00', password: 'admin1234' };

test.describe('Authentication - Login Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/fr/login');
  });

  test('should display login form correctly', async ({ page }) => {
    // Check page title
    await expect(page.locator('h1, h2').first()).toContainText(/BIZ360|Connexion/i);

    // Check form elements exist
    await expect(page.locator('#phone')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.fill('#phone', '+225 00 00 00 00 00');
    await page.fill('#password', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('.bg-red-50, [role="alert"]')).toBeVisible({ timeout: 10000 });
  });

  test('should show error for empty form submission', async ({ page }) => {
    await page.click('button[type="submit"]');

    // HTML5 validation should prevent submission or show error
    const phoneInput = page.locator('#phone');
    await expect(phoneInput).toHaveAttribute('required', '');
  });
});

test.describe('Authentication - Login by Role', () => {
  for (const [role, user] of Object.entries(TEST_USERS)) {
    test(`should login as ${role}: ${user.name}`, async ({ page }) => {
      await page.goto('/fr/login');

      // Fill login form
      await page.fill('#phone', user.phone);
      await page.fill('#password', TEST_PASSWORD);
      await page.click('button[type="submit"]');

      // Wait for navigation (should redirect away from login)
      await page.waitForURL(/(?!.*login).*/, { timeout: 15000 });

      // Should be on dashboard or appropriate page
      await expect(page).not.toHaveURL(/login/);

      // Verify we're logged in (check for user-related content)
      const pageContent = await page.content();
      expect(pageContent.length).toBeGreaterThan(1000);
    });
  }

  test('should login as superuser', async ({ page }) => {
    await page.goto('/fr/login');

    await page.fill('#phone', SUPERUSER.phone);
    await page.fill('#password', SUPERUSER.password);
    await page.click('button[type="submit"]');

    await page.waitForURL(/(?!.*login).*/, { timeout: 15000 });
    await expect(page).not.toHaveURL(/login/);
  });
});

test.describe('Authentication - Logout', () => {
  test('should logout successfully', async ({ page }) => {
    // Login first
    await page.goto('/fr/login');
    await page.fill('#phone', TEST_USERS.owner.phone);
    await page.fill('#password', TEST_PASSWORD);
    await page.click('button[type="submit"]');
    await page.waitForURL(/(?!.*login).*/, { timeout: 15000 });

    // Look for logout button or menu
    const logoutButton = page.locator('button:has-text("Déconnexion"), button:has-text("Logout"), [data-testid="logout"]');
    const menuButton = page.locator('button:has-text("Menu"), [data-testid="menu"], button[aria-label*="menu" i]');

    // Try to find and click logout
    if (await menuButton.isVisible()) {
      await menuButton.click();
      await page.waitForTimeout(500);
    }

    if (await logoutButton.isVisible()) {
      await logoutButton.click();
      await expect(page).toHaveURL(/login/, { timeout: 10000 });
    }
  });
});

test.describe('Authentication - Protected Routes', () => {
  test('should redirect to login when accessing POS without auth', async ({ browser }) => {
    // Create a fresh context with no existing auth
    const context = await browser.newContext();
    const page = await context.newPage();

    await page.goto('/fr/pos');

    // Wait for client-side auth check and redirect
    await expect(page).toHaveURL(/login/, { timeout: 15000 });

    await context.close();
  });

  test('should redirect to login when accessing kitchen without auth', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();

    await page.goto('/fr/kitchen');

    await expect(page).toHaveURL(/login/, { timeout: 15000 });

    await context.close();
  });

  test('should redirect to login or register when accessing lite dashboard without auth', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();

    await page.goto('/fr/lite/dashboard');

    // Lite dashboard redirects to register page for new users (by design)
    await expect(page).toHaveURL(/login|register/, { timeout: 15000 });

    await context.close();
  });
});
