const { test, expect } = require('@playwright/test');

// Runs before every test: open the homepage.
test.beforeEach(async ({ page }) => {
  await page.goto('/');
});

test('page has the right title', async ({ page }) => {
  await expect(page).toHaveTitle(/.+/);
});

test('theme toggle switches dark/light', async ({ page }) => {
  const html = page.locator('html');
  const toggle = page.locator('#themeToggle');

  await toggle.click();
  await expect(html).toHaveAttribute('data-theme', 'dark');

  await toggle.click();
  await expect(html).toHaveAttribute('data-theme', 'light');
});

test('project filter shows only matching cards', async ({ page }) => {
  const visibleCards = page.locator('.project-card:visible');
  const total = await visibleCards.count();

  await page.getByRole('button', { name: 'HR & Operations' }).click();

  // Fewer cards than before, and every visible one is in the "hr" category.
  expect(await visibleCards.count()).toBeLessThan(total);
  for (const card of await visibleCards.all()) {
    await expect(card).toHaveAttribute('data-category', 'hr');
  }

  // Clicking "All" brings everything back.
  await page.getByRole('button', { name: 'All', exact: true }).click();
  await expect(visibleCards).toHaveCount(total);
});

test('nav link scrolls to its section', async ({ page }) => {
  await page.getByRole('link', { name: 'Contact', exact: true }).first().click();
  await expect(page).toHaveURL(/#contact$/);
  await expect(page.locator('#contact')).toBeInViewport();
});

test('back-to-top button appears after scrolling and works', async ({ page }) => {
  const toTop = page.locator('#toTop');
  await page.evaluate(() => window.scrollTo(0, 2000));
  await expect(toTop).toHaveClass(/show/);

  await toTop.click();
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBeLessThan(10);
});

test('mobile menu opens and closes', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 700 });
  const toggle = page.locator('#navToggle');

  await toggle.click();
  await expect(toggle).toHaveAttribute('aria-expanded', 'true');

  await toggle.click();
  await expect(toggle).toHaveAttribute('aria-expanded', 'false');
});
