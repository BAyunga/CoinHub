import { test, expect } from '@playwright/test';

test.describe('Recharge form', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/recharge.html?app=baat');
    await expect(page.locator('#appName')).toHaveText('Baat');
    await page.fill('#appUserId', '1234567890');   // 10 digits
  });

  for (const phone of ['712345678', '0712345678', '0112345678']) {
    test(`accepts phone ${phone}`, async ({ page }) => {
      await page.fill('#phoneNumber', phone);
      await page.fill('#coinQty', '10000');
      await expect(page.locator('#btnNext')).toBeEnabled();
    });
  }

  test('invalid amount snaps up to the next valid amount', async ({ page }) => {
    await page.fill('#coinQty', '10500');
    await page.locator('#coinQty').press('Tab');
    await expect(page.locator('#coinQty')).toHaveValue('11000');
    await expect(page.locator('#kesAmount')).toHaveText('165');
    await expect(page.locator('#coinHint')).toContainText('multiples of 1,000');
  });

  test('below the minimum snaps up to the minimum', async ({ page }) => {
    await page.fill('#coinQty', '5000');
    await page.locator('#coinQty').press('Tab');
    await expect(page.locator('#coinQty')).toHaveValue('10000');
    await expect(page.locator('#kesAmount')).toHaveText('150');
  });

  test('quick-pick button fills the amount', async ({ page }) => {
    await page.locator('.coin-chip').nth(1).click();   // 2 x minimum
    await expect(page.locator('#coinQty')).toHaveValue('20000');
    await expect(page.locator('#kesAmount')).toHaveText('300');
  });

  test('calculates KES for 10000 Baat coins', async ({ page }) => {
    await page.fill('#coinQty', '10000');
    await expect(page.locator('#kesAmount')).toHaveText('150');  // 15 per 1000
  });

  test('Crush Live starts at 1000 coins', async ({ page }) => {
    await page.goto('/recharge.html?app=crush');
    await page.fill('#coinQty', '1000');
    await expect(page.locator('#kesAmount')).toHaveText('15');
  });

  test('Poppo only accepts whole 8,000-coin packs', async ({ page }) => {
    await page.goto('/recharge.html?app=poppo');
    await page.fill('#coinQty', '16000');
    await expect(page.locator('#kesAmount')).toHaveText('222');
  });

  test('confirm screen shows the full phone number', async ({ page }) => {
    await page.fill('#phoneNumber', '0712345678');
    await page.fill('#coinQty', '10000');
    await page.click('#btnNext');
    await expect(page.locator('#confPhone')).toHaveText('+254712345678');
  });
});