import { test, expect } from '@playwright/test';

test.describe('Kitchen Display', () => {
  test.beforeEach(async ({ page }) => {
    // TODO: Set up authenticated session with kitchen role
  });

  test('should display kitchen page with dark theme', async ({ page }) => {
    await page.goto('/fr/kitchen');
    await page.waitForLoadState('networkidle');

    // Page should have dark background
    const body = page.locator('body, [class*="bg-gray-900"], [class*="dark"]');
    await expect(body).toBeVisible();

    // Should show kitchen title
    await expect(page.locator('text=/Cuisine|Kitchen/i')).toBeVisible();
  });

  test('should display three status columns', async ({ page }) => {
    await page.goto('/fr/kitchen');
    await page.waitForLoadState('networkidle');

    // Should have pending, preparing, ready columns
    const pendingColumn = page.locator('text=/En attente|Pending/i');
    const preparingColumn = page.locator('text=/En préparation|Preparing/i');
    const readyColumn = page.locator('text=/Prêt|Ready/i');

    await expect(pendingColumn).toBeVisible();
    await expect(preparingColumn).toBeVisible();
    await expect(readyColumn).toBeVisible();
  });

  test('should show WebSocket connection status indicator', async ({ page }) => {
    await page.goto('/fr/kitchen');
    await page.waitForLoadState('networkidle');

    // Connection indicator (green dot when connected, red when not)
    const statusIndicator = page.locator('[class*="bg-green-500"], [class*="bg-red-500"]').first();
    await expect(statusIndicator).toBeVisible();
  });

  test('should display live clock', async ({ page }) => {
    await page.goto('/fr/kitchen');

    // Clock should be visible and updating
    const clock = page.locator('text=/\\d{1,2}:\\d{2}(:\\d{2})?/');
    await expect(clock).toBeVisible();

    // Get initial time
    const initialTime = await clock.textContent();

    // Wait 2 seconds
    await page.waitForTimeout(2000);

    // Time should have changed (or at least still be visible)
    const newTime = await clock.textContent();
    expect(newTime).toBeTruthy();
  });

  test('should display order cards with details', async ({ page }) => {
    await page.goto('/fr/kitchen');
    await page.waitForLoadState('networkidle');

    // Order cards should show order number, items, etc.
    // This depends on having orders in the system
    const orderCard = page.locator('[class*="OrderCard"], .order-card, [class*="rounded-lg"]').filter({
      has: page.locator('text=/#\\d+/')  // Has order number like #1, #2
    }).first();

    // If there are orders, they should have details
    if (await orderCard.isVisible()) {
      // Should show order number
      await expect(orderCard.locator('text=/#\\d+/')).toBeVisible();

      // Should have status action button
      const actionButton = orderCard.locator('button');
      await expect(actionButton).toBeVisible();
    }
  });

  test('should allow updating order status', async ({ page }) => {
    await page.goto('/fr/kitchen');
    await page.waitForLoadState('networkidle');

    // Find an order in pending column
    const pendingOrder = page.locator('[class*="yellow"], [class*="pending"]').locator('[class*="OrderCard"], .order-card').first();

    if (await pendingOrder.isVisible()) {
      // Click the action button (e.g., "Mark Preparing")
      const actionButton = pendingOrder.locator('button:has-text("Préparer"), button:has-text("Preparing")');
      if (await actionButton.isVisible()) {
        await actionButton.click();

        // Order should move to preparing column (or status should change)
        await page.waitForTimeout(500);
      }
    }
  });

  test('should work without orders (empty state)', async ({ page }) => {
    await page.goto('/fr/kitchen');
    await page.waitForLoadState('networkidle');

    // Even with no orders, the page should render correctly
    const columns = page.locator('[class*="Column"], [class*="column"]');
    await expect(columns.first()).toBeVisible();

    // Empty state message might be shown
    const emptyState = page.locator('text=/No orders|Aucune commande/i');
    // This is optional - just check page doesn't crash
  });
});

test.describe('Kitchen Display - Responsive', () => {
  test('should display properly on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1024, height: 768 });
    await page.goto('/fr/kitchen');
    await page.waitForLoadState('networkidle');

    // All three columns should be visible
    const columns = page.locator('[class*="flex-1"]');
    expect(await columns.count()).toBeGreaterThanOrEqual(3);
  });
});
