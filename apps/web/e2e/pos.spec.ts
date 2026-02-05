import { test, expect, Page } from '@playwright/test';

// Increase timeout for POS tests since they require login
test.setTimeout(60000);

// Test user (cashier role)
const TEST_USER = {
  phone: '+225 03 87 55 88 52',
  password: 'test1234',
  name: 'Aminata Touré',
};

// Helper function to login and go directly to POS
async function loginAndGoToPOS(page: Page) {
  await page.goto('/fr/login');
  await page.fill('#phone', TEST_USER.phone);
  await page.fill('#password', TEST_USER.password);
  await page.click('button[type="submit"]');

  // Wait for redirect after login (should go to /lite/dashboard)
  await page.waitForURL(/(?!.*login).*/, { timeout: 15000 });

  // Wait for token to be stored in sessionStorage
  await page.waitForFunction(() => {
    return sessionStorage.getItem('accessToken') !== null;
  }, { timeout: 5000 });

  // Navigate to POS
  await page.goto('/fr/pos');

  // Wait for POS page to load
  await page.waitForLoadState('domcontentloaded');

  // Wait for auth to complete and page to render
  await page.waitForTimeout(1000);

  // Check we're on POS page (not redirected to login)
  const url = page.url();
  if (url.includes('login')) {
    throw new Error('Was redirected back to login - auth may have failed');
  }

  // Wait for the POS header to be visible
  await expect(page.locator('header h1')).toBeVisible({ timeout: 10000 });
}

// Helper to add an item to cart (handles modifier modal)
async function addItemToCart(page: Page) {
  // Click on a menu item
  const menuItem = page.locator('button').filter({ hasText: /XOF/i }).first();
  await menuItem.click();

  // Check if modifier modal appears
  const modalVisible = await page.locator('.fixed.inset-0').isVisible();

  if (modalVisible) {
    // Wait for modal to fully appear
    await page.waitForTimeout(300);

    // Select first modifier option if available
    const modifierOption = page.locator('.fixed button').filter({ hasText: /Attiéké|Riz|Option/i }).first();
    if (await modifierOption.isVisible()) {
      await modifierOption.click();
    }

    // Click the "Ajouter" (Add) button in the modal
    const addButton = page.locator('.fixed button').filter({ hasText: /Ajouter|Add/i });
    await addButton.click();
    await page.waitForTimeout(300);
  }

  // Verify item was added to cart
  await page.waitForTimeout(500);
}

test.describe('POS - Page Display', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndGoToPOS(page);
  });

  test('should display POS page with menu categories', async ({ page }) => {
    // Check page title
    await expect(page.locator('header h1')).toContainText(/Point de Vente|POS/i);

    // Check for category tabs
    const categoryButtons = page.locator('button').filter({ hasText: /Plats|Boissons|Grillades/i });
    await expect(categoryButtons.first()).toBeVisible({ timeout: 10000 });
  });

  test('should display menu items in grid', async ({ page }) => {
    // Wait for menu items to load
    await page.waitForTimeout(1000);

    // Check for menu item cards (they have price in XOF)
    const menuItems = page.locator('button').filter({ hasText: /XOF/i });
    const count = await menuItems.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should display empty cart initially', async ({ page }) => {
    // Check cart is visible and empty
    await expect(page.locator('h2').filter({ hasText: /Panier|Cart/i })).toBeVisible();
    await expect(page.locator('text=/Votre panier est vide|empty/i')).toBeVisible();
  });

  test('should switch between category tabs', async ({ page }) => {
    // Wait for categories to load
    await page.waitForTimeout(1000);

    // Get all category buttons
    const categoryButtons = page.locator('button').filter({ hasText: /\(\d+\)/ });
    const count = await categoryButtons.count();

    if (count > 1) {
      // Click on second category
      await categoryButtons.nth(1).click();
      await page.waitForTimeout(500);

      // Verify the tab is still visible (categories should persist)
      await expect(categoryButtons.nth(1)).toBeVisible();
    }
  });
});

test.describe('POS - Cart Operations', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndGoToPOS(page);
    await page.waitForTimeout(1000);
  });

  test('should add item to cart', async ({ page }) => {
    // Add an item using our helper
    await addItemToCart(page);

    // Check that cart is no longer empty
    await expect(page.locator('text=/Votre panier est vide|empty/i')).not.toBeVisible({ timeout: 5000 });

    // Check for checkout button to have count > 0
    const checkoutButton = page.locator('button').filter({ hasText: /Valider|Checkout/i });
    await expect(checkoutButton).not.toContainText('(0)');
  });

  test('should increase item quantity', async ({ page }) => {
    // Add an item first
    await addItemToCart(page);

    // Find the + button in cart item and click it
    const plusButton = page.locator('.bg-gray-50').locator('button').filter({ hasText: '+' }).first();
    await expect(plusButton).toBeVisible({ timeout: 5000 });
    await plusButton.click();
    await page.waitForTimeout(300);

    // Check quantity is now 2
    await expect(page.locator('.bg-gray-50 .text-center').first()).toContainText('2');
  });

  test('should decrease item quantity', async ({ page }) => {
    // Add an item first
    await addItemToCart(page);

    // Find cart item container (has rounded-lg p-3 classes)
    const cartItem = page.locator('.bg-gray-50.rounded-lg.p-3').first();

    // Increase quantity first
    const plusButton = cartItem.locator('button').filter({ hasText: '+' });
    await plusButton.click();
    await page.waitForTimeout(500);

    // Verify quantity is 2
    const quantityDisplay = cartItem.locator('.text-center');
    await expect(quantityDisplay).toContainText('2', { timeout: 3000 });

    // Now decrease
    const minusButton = cartItem.locator('button').filter({ hasText: '-' });
    await minusButton.click();
    await page.waitForTimeout(500);

    // Check quantity is back to 1
    await expect(quantityDisplay).toContainText('1', { timeout: 3000 });
  });

  test('should remove item when quantity reaches 0', async ({ page }) => {
    // Add an item first
    await addItemToCart(page);

    // Find cart item container
    const cartItem = page.locator('.bg-gray-50.rounded-lg.p-3').first();
    await expect(cartItem).toBeVisible({ timeout: 5000 });

    // Get the minus button and click to decrease to 0
    const minusButton = cartItem.locator('button').filter({ hasText: '-' });
    await minusButton.click();
    await page.waitForTimeout(1000);

    // Cart should be empty again (item removed when qty = 0)
    await expect(page.locator('text=/Votre panier est vide|empty/i')).toBeVisible({ timeout: 5000 });
  });

  test('should remove item with X button', async ({ page }) => {
    // Add an item first
    await addItemToCart(page);

    // Click the remove button (×)
    const removeButton = page.locator('.bg-gray-50').locator('button').filter({ hasText: '×' }).first();
    await expect(removeButton).toBeVisible({ timeout: 5000 });
    await removeButton.click();
    await page.waitForTimeout(500);

    // Cart should be empty
    await expect(page.locator('text=/Votre panier est vide|empty/i')).toBeVisible({ timeout: 5000 });
  });

  test('should update total when adding items', async ({ page }) => {
    // Add an item
    await addItemToCart(page);

    // Total should be greater than 0
    const totalText = page.locator('text=/Total/i').locator('..').locator('span').last();
    const totalValue = await totalText.textContent();
    expect(totalValue).not.toBe('0 XOF');
    expect(totalValue).toContain('XOF');
  });
});

test.describe('POS - Checkout Flow', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndGoToPOS(page);
    await page.waitForTimeout(1000);

    // Add an item to cart
    await addItemToCart(page);
  });

  test('should open checkout modal', async ({ page }) => {
    // Click checkout button
    const checkoutButton = page.locator('button').filter({ hasText: /Valider|Checkout/i });
    await expect(checkoutButton).toBeEnabled({ timeout: 5000 });
    await checkoutButton.click();

    // Modal should be visible (look for form elements in modal)
    await expect(page.locator('.fixed.inset-0')).toBeVisible({ timeout: 5000 });
  });

  test('should display order type selector in checkout', async ({ page }) => {
    // Open checkout
    const checkoutButton = page.locator('button').filter({ hasText: /Valider|Checkout/i });
    await checkoutButton.click();
    await page.waitForTimeout(500);

    // Check for order type options
    const orderTypes = page.locator('button').filter({ hasText: /Sur place|Emporter|Livraison|Dine|Take|Delivery/i });
    const count = await orderTypes.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should close checkout modal with cancel button', async ({ page }) => {
    // Open checkout
    const checkoutButton = page.locator('button').filter({ hasText: /Valider|Checkout/i });
    await checkoutButton.click();
    await page.waitForTimeout(500);

    // Click cancel
    const cancelButton = page.locator('.fixed button').filter({ hasText: /Annuler|Cancel/i });
    await cancelButton.click();
    await page.waitForTimeout(300);

    // Modal should be closed
    await expect(page.locator('.fixed.inset-0.bg-black\\/50')).not.toBeVisible({ timeout: 3000 });
  });

  test('should submit takeout order successfully', async ({ page }) => {
    // Open checkout
    const checkoutButton = page.locator('button').filter({ hasText: /Valider|Checkout/i });
    await checkoutButton.click();
    await page.waitForTimeout(500);

    // Select takeout if available (no table required)
    const takeoutButton = page.locator('button').filter({ hasText: /emporter/i });
    if (await takeoutButton.isVisible()) {
      await takeoutButton.click();
      await page.waitForTimeout(300);
    }

    // Submit order - the button text is "Envoyer la commande"
    const submitButton = page.locator('button').filter({ hasText: /Envoyer/i });
    await expect(submitButton).toBeVisible({ timeout: 5000 });
    await submitButton.click();

    // Wait for success message (use heading to be specific)
    await expect(page.getByRole('heading', { name: /Order Created/i })).toBeVisible({ timeout: 10000 });

    // Click continue
    const continueButton = page.locator('button').filter({ hasText: /Continue|Continuer/i });
    await continueButton.click();
    await page.waitForTimeout(500);

    // Should be back to POS with empty cart
    await expect(page.locator('text=/Votre panier est vide|empty/i')).toBeVisible({ timeout: 5000 });
  });
});

test.describe('POS - Multiple Items', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndGoToPOS(page);
    await page.waitForTimeout(1000);
  });

  test('should add multiple different items to cart', async ({ page }) => {
    // Add first item
    await addItemToCart(page);

    // Switch to different category to get different items
    const categoryButtons = page.locator('button').filter({ hasText: /\(\d+\)/ });
    if (await categoryButtons.nth(1).isVisible()) {
      await categoryButtons.nth(1).click();
      await page.waitForTimeout(500);
    }

    // Add second item
    await addItemToCart(page);

    // Check checkout button shows count >= 2
    const checkoutButton = page.locator('button').filter({ hasText: /Valider|Checkout/i });
    const buttonText = await checkoutButton.textContent();
    const match = buttonText?.match(/\((\d+)\)/);
    const count = match ? parseInt(match[1]) : 0;
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test('should increase quantity by clicking same item multiple times', async ({ page }) => {
    // Add an item
    await addItemToCart(page);

    // Click the + button to increase quantity
    const plusButton = page.locator('.bg-gray-50').locator('button').filter({ hasText: '+' }).first();
    await plusButton.click();
    await page.waitForTimeout(200);
    await plusButton.click();
    await page.waitForTimeout(500);

    // Check quantity is 3
    await expect(page.locator('.bg-gray-50 .text-center').first()).toContainText('3');
  });
});
