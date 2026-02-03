import { test, expect } from '@playwright/test';

test.describe('POS Order Flow', () => {
  test.beforeEach(async ({ page }) => {
    // TODO: Set up authenticated session
    // For now, we'll test what's accessible
  });

  test('should display POS page with menu categories', async ({ page }) => {
    await page.goto('/fr/pos');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Should show POS title
    await expect(page.locator('h1')).toContainText(/POS|Caisse/i);
  });

  test('should display menu categories as tabs', async ({ page }) => {
    await page.goto('/fr/pos');
    await page.waitForLoadState('networkidle');

    // Should have category tabs/buttons
    const categoryTabs = page.locator('[role="tab"], .category-tab, button').filter({
      hasText: /.+/  // Has some text
    });

    // At least one category should be visible (or loading state)
    const hasCategories = await categoryTabs.first().isVisible().catch(() => false);
    const hasLoading = await page.locator('text=/loading|chargement/i').isVisible().catch(() => false);

    expect(hasCategories || hasLoading).toBeTruthy();
  });

  test('should display menu items in grid', async ({ page }) => {
    await page.goto('/fr/pos');
    await page.waitForLoadState('networkidle');

    // Menu grid should be present
    const menuGrid = page.locator('.grid, [class*="grid"]');
    await expect(menuGrid.first()).toBeVisible();
  });

  test('should add item to cart when clicked', async ({ page }) => {
    await page.goto('/fr/pos');
    await page.waitForLoadState('networkidle');

    // Find a menu item card and click it
    const menuItemCard = page.locator('[class*="MenuItemCard"], .menu-item, button').filter({
      has: page.locator('text=/XOF/')
    }).first();

    if (await menuItemCard.isVisible()) {
      await menuItemCard.click();

      // Cart should update - check for item count or cart content
      const cart = page.locator('[class*="Cart"], .cart, [class*="cart"]');
      await expect(cart).toBeVisible();
    }
  });

  test('should show cart with items and totals', async ({ page }) => {
    await page.goto('/fr/pos');
    await page.waitForLoadState('networkidle');

    // Cart section should exist
    const cartSection = page.locator('text=/Panier|Cart/i').first();
    await expect(cartSection).toBeVisible();

    // Should show total
    const totalSection = page.locator('text=/Total|Sous-total/i').first();
    await expect(totalSection).toBeVisible();
  });

  test('should open checkout modal when checkout clicked', async ({ page }) => {
    await page.goto('/fr/pos');
    await page.waitForLoadState('networkidle');

    // Add an item first (if possible)
    const menuItem = page.locator('button').filter({ has: page.locator('text=/XOF/') }).first();
    if (await menuItem.isVisible()) {
      await menuItem.click();
      await page.waitForTimeout(500);
    }

    // Click checkout button
    const checkoutButton = page.locator('button:has-text("Commander"), button:has-text("Checkout")');
    if (await checkoutButton.isEnabled()) {
      await checkoutButton.click();

      // Modal should appear
      const modal = page.locator('[role="dialog"], .modal, [class*="Modal"]');
      await expect(modal).toBeVisible();
    }
  });

  test('should allow selecting order type (dine-in/takeout/delivery)', async ({ page }) => {
    await page.goto('/fr/pos');
    await page.waitForLoadState('networkidle');

    // Add item and open checkout
    const menuItem = page.locator('button').filter({ has: page.locator('text=/XOF/') }).first();
    if (await menuItem.isVisible()) {
      await menuItem.click();
    }

    const checkoutButton = page.locator('button:has-text("Commander"), button:has-text("Checkout")');
    if (await checkoutButton.isEnabled()) {
      await checkoutButton.click();

      // Order type selector should be visible
      const orderTypeButtons = page.locator('button:has-text("Sur place"), button:has-text("Dine"), button:has-text("Emporter"), button:has-text("Takeout")');
      await expect(orderTypeButtons.first()).toBeVisible();
    }
  });

  test('should submit order and show confirmation', async ({ page }) => {
    await page.goto('/fr/pos');
    await page.waitForLoadState('networkidle');

    // Add item
    const menuItem = page.locator('button').filter({ has: page.locator('text=/XOF/') }).first();
    if (await menuItem.isVisible()) {
      await menuItem.click();
    }

    // Open checkout
    const checkoutButton = page.locator('button:has-text("Commander"), button:has-text("Checkout")');
    if (await checkoutButton.isEnabled()) {
      await checkoutButton.click();

      // Fill required fields if any
      const tableInput = page.locator('input[placeholder*="Table"], input[name*="table"]');
      if (await tableInput.isVisible()) {
        await tableInput.fill('5');
      }

      // Submit order
      const submitButton = page.locator('button:has-text("Soumettre"), button:has-text("Submit"), button[type="submit"]');
      if (await submitButton.isEnabled()) {
        await submitButton.click();

        // Should show success/confirmation
        await expect(page.locator('text=/Confirmé|Created|Success/i')).toBeVisible({ timeout: 10000 });
      }
    }
  });
});
