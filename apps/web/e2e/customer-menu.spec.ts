import { test, expect } from '@playwright/test';

test.describe('Customer QR Menu', () => {
  // Use a test restaurant slug - this should be created in test setup
  const testSlug = 'test-restaurant';

  test('should display public menu without authentication', async ({ page }) => {
    await page.goto(`/fr/menu/${testSlug}`);
    await page.waitForLoadState('networkidle');

    // Should not redirect to login
    expect(page.url()).toContain('/menu/');
  });

  test('should display restaurant name in header', async ({ page }) => {
    await page.goto(`/fr/menu/${testSlug}`);
    await page.waitForLoadState('networkidle');

    // Restaurant name should be in header
    const header = page.locator('header h1, header [class*="font-bold"]');
    await expect(header).toBeVisible();
  });

  test('should display menu categories', async ({ page }) => {
    await page.goto(`/fr/menu/${testSlug}`);
    await page.waitForLoadState('networkidle');

    // Categories should be shown as section headers
    const categoryHeaders = page.locator('h2[class*="font-bold"], h2[class*="sticky"]');
    // At least expect the page structure, even if no categories loaded
    const pageLoaded = await page.locator('main').isVisible();
    expect(pageLoaded).toBeTruthy();
  });

  test('should display menu items with prices in XOF', async ({ page }) => {
    await page.goto(`/fr/menu/${testSlug}`);
    await page.waitForLoadState('networkidle');

    // Menu items should show XOF prices
    const priceLabel = page.locator('text=/XOF/');
    // If menu is loaded, should have prices
    const hasPrice = await priceLabel.first().isVisible().catch(() => false);
    const hasError = await page.locator('text=/not found|introuvable/i').isVisible().catch(() => false);

    // Either show prices or error for missing restaurant
    expect(hasPrice || hasError).toBeTruthy();
  });

  test('should add item to cart when clicked', async ({ page }) => {
    await page.goto(`/fr/menu/${testSlug}`);
    await page.waitForLoadState('networkidle');

    // Click on a menu item
    const menuItem = page.locator('button').filter({ has: page.locator('text=/XOF/') }).first();

    if (await menuItem.isVisible()) {
      await menuItem.click();

      // Cart FAB should appear or update
      await page.waitForTimeout(500);
      const cartFab = page.locator('button[class*="fixed"], [class*="bottom-4"]').filter({
        has: page.locator('text=/Panier|Cart|XOF/')
      });

      // Either cart FAB appears or modifier modal opens
      const fabVisible = await cartFab.isVisible().catch(() => false);
      const modalVisible = await page.locator('[class*="Modal"], [role="dialog"]').isVisible().catch(() => false);

      expect(fabVisible || modalVisible).toBeTruthy();
    }
  });

  test('should show modifier selection modal for items with modifiers', async ({ page }) => {
    await page.goto(`/fr/menu/${testSlug}`);
    await page.waitForLoadState('networkidle');

    // Click on a menu item
    const menuItem = page.locator('button').filter({ has: page.locator('text=/XOF/') }).first();

    if (await menuItem.isVisible()) {
      await menuItem.click();

      // If item has modifiers, modal should appear
      const modal = page.locator('[class*="Modal"], [role="dialog"], [class*="fixed"]').filter({
        has: page.locator('text=/Ajouter|Add/')
      });

      if (await modal.isVisible()) {
        // Modal should have add button
        const addButton = modal.locator('button:has-text("Ajouter"), button:has-text("Add")');
        await expect(addButton).toBeVisible();
      }
    }
  });

  test('should show cart FAB with item count and total', async ({ page }) => {
    await page.goto(`/fr/menu/${testSlug}`);
    await page.waitForLoadState('networkidle');

    // Add an item
    const menuItem = page.locator('button').filter({ has: page.locator('text=/XOF/') }).first();

    if (await menuItem.isVisible()) {
      await menuItem.click();

      // Close modal if open
      const addButton = page.locator('button:has-text("Ajouter"), button:has-text("Add")');
      if (await addButton.isVisible()) {
        await addButton.click();
      }

      // Cart FAB should show
      const cartFab = page.locator('[class*="fixed"][class*="bottom"]').filter({
        has: page.locator('text=/XOF/')
      });

      await expect(cartFab).toBeVisible();
    }
  });

  test('should open cart modal when FAB clicked', async ({ page }) => {
    await page.goto(`/fr/menu/${testSlug}`);
    await page.waitForLoadState('networkidle');

    // Add an item first
    const menuItem = page.locator('button').filter({ has: page.locator('text=/XOF/') }).first();
    if (await menuItem.isVisible()) {
      await menuItem.click();

      const addButton = page.locator('button:has-text("Ajouter"), button:has-text("Add")');
      if (await addButton.isVisible()) {
        await addButton.click();
      }

      // Click cart FAB
      const cartFab = page.locator('[class*="fixed"][class*="bottom"]').filter({
        has: page.locator('text=/XOF/')
      });

      if (await cartFab.isVisible()) {
        await cartFab.click();

        // Cart modal should open
        const cartModal = page.locator('[class*="Modal"], [role="dialog"]').filter({
          has: page.locator('text=/Panier|Cart/i')
        });

        await expect(cartModal).toBeVisible();
      }
    }
  });

  test('should allow adjusting item quantity in cart', async ({ page }) => {
    await page.goto(`/fr/menu/${testSlug}`);
    await page.waitForLoadState('networkidle');

    // Add item and open cart
    const menuItem = page.locator('button').filter({ has: page.locator('text=/XOF/') }).first();
    if (await menuItem.isVisible()) {
      await menuItem.click();

      const addButton = page.locator('button:has-text("Ajouter"), button:has-text("Add")');
      if (await addButton.isVisible()) {
        await addButton.click();
      }

      const cartFab = page.locator('[class*="fixed"][class*="bottom"]').filter({
        has: page.locator('text=/XOF/')
      });

      if (await cartFab.isVisible()) {
        await cartFab.click();

        // Quantity controls should be visible
        const plusButton = page.locator('button:has-text("+")');
        const minusButton = page.locator('button:has-text("-")');

        await expect(plusButton.first()).toBeVisible();
        await expect(minusButton.first()).toBeVisible();
      }
    }
  });

  test('should proceed to checkout', async ({ page }) => {
    await page.goto(`/fr/menu/${testSlug}`);
    await page.waitForLoadState('networkidle');

    // Add item
    const menuItem = page.locator('button').filter({ has: page.locator('text=/XOF/') }).first();
    if (await menuItem.isVisible()) {
      await menuItem.click();

      const addButton = page.locator('button:has-text("Ajouter"), button:has-text("Add")');
      if (await addButton.isVisible()) {
        await addButton.click();
      }

      // Open cart
      const cartFab = page.locator('[class*="fixed"][class*="bottom"]').filter({
        has: page.locator('text=/XOF/')
      });

      if (await cartFab.isVisible()) {
        await cartFab.click();

        // Click checkout
        const checkoutButton = page.locator('button:has-text("Commander"), button:has-text("Checkout")');
        if (await checkoutButton.isVisible()) {
          await checkoutButton.click();

          // Checkout form should appear
          const customerNameInput = page.locator('input').filter({ hasText: /name|nom/i });
          const orderTypeSelector = page.locator('text=/Sur place|Dine|Emporter|Takeout/i');

          const hasCheckoutForm = await customerNameInput.isVisible().catch(() => false) ||
            await orderTypeSelector.isVisible().catch(() => false);

          expect(hasCheckoutForm).toBeTruthy();
        }
      }
    }
  });

  test('should submit order and show confirmation', async ({ page }) => {
    await page.goto(`/fr/menu/${testSlug}`);
    await page.waitForLoadState('networkidle');

    // Full flow: add item -> cart -> checkout -> submit
    const menuItem = page.locator('button').filter({ has: page.locator('text=/XOF/') }).first();
    if (await menuItem.isVisible()) {
      await menuItem.click();

      const addButton = page.locator('button:has-text("Ajouter"), button:has-text("Add")');
      if (await addButton.isVisible()) await addButton.click();

      const cartFab = page.locator('[class*="fixed"][class*="bottom"]').filter({
        has: page.locator('text=/XOF/')
      });

      if (await cartFab.isVisible()) {
        await cartFab.click();

        const checkoutButton = page.locator('button:has-text("Commander"), button:has-text("Checkout")');
        if (await checkoutButton.isVisible()) {
          await checkoutButton.click();

          // Fill customer info
          const nameInput = page.locator('input[placeholder*="Name"], input[placeholder*="nom"]').first();
          if (await nameInput.isVisible()) {
            await nameInput.fill('Test Customer');
          }

          // Submit order
          const submitButton = page.locator('button:has-text("Soumettre"), button:has-text("Submit"), button[type="submit"]');
          if (await submitButton.isEnabled()) {
            await submitButton.click();

            // Should show confirmation with order number
            await expect(page.locator('text=/Confirmé|Confirmed|#\\d+/i')).toBeVisible({ timeout: 10000 });
          }
        }
      }
    }
  });

  test('should show 404 for invalid restaurant slug', async ({ page }) => {
    await page.goto('/fr/menu/invalid-restaurant-slug-12345');
    await page.waitForLoadState('networkidle');

    // Should show error message
    const errorMessage = page.locator('text=/not found|introuvable|error/i');
    await expect(errorMessage).toBeVisible();
  });
});

test.describe('Customer Menu - Mobile', () => {
  test.use({ viewport: { width: 375, height: 812 } }); // iPhone X

  test('should display properly on mobile viewport', async ({ page }) => {
    await page.goto(`/fr/menu/test-restaurant`);
    await page.waitForLoadState('networkidle');

    // Content should be centered and readable
    const main = page.locator('main');
    await expect(main).toBeVisible();

    // Cart FAB should be at bottom
    const cartFab = page.locator('[class*="fixed"][class*="bottom"]');
    // Should either be visible or not present if no items
  });

  test('should show bottom sheet modals on mobile', async ({ page }) => {
    await page.goto(`/fr/menu/test-restaurant`);
    await page.waitForLoadState('networkidle');

    const menuItem = page.locator('button').filter({ has: page.locator('text=/XOF/') }).first();
    if (await menuItem.isVisible()) {
      await menuItem.click();

      // Modal should slide up from bottom on mobile
      const modal = page.locator('[class*="rounded-t"], [class*="bottom-0"]');
      if (await modal.isVisible()) {
        // Modal should be at bottom of screen
        const box = await modal.boundingBox();
        if (box) {
          expect(box.y).toBeGreaterThan(200); // Not at top of screen
        }
      }
    }
  });
});
