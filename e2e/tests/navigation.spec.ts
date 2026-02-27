import { test, expect } from "@playwright/test";

test.describe("Navigation", () => {
  test("home page loads with h1", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("h1")).toBeVisible();
  });

  test("nav link to /blog works", async ({ page }) => {
    await page.goto("/");
    await page.locator('nav[aria-label="Main navigation"] a[href="/blog"]').click();
    await expect(page).toHaveURL("/blog");
    await expect(page.locator("h1")).toBeVisible();
  });

  test("nav link to /projects works", async ({ page }) => {
    await page.goto("/");
    await page.locator('nav[aria-label="Main navigation"] a[href="/projects"]').click();
    await expect(page).toHaveURL("/projects");
    await expect(page.locator("h1")).toBeVisible();
  });

  test("nav link to /about works", async ({ page }) => {
    await page.goto("/");
    await page.locator('nav[aria-label="Main navigation"] a[href="/about"]').click();
    await expect(page).toHaveURL("/about");
    await expect(page.locator("h1")).toBeVisible();
  });

  test("skip-to-content link exists and points to #main", async ({ page }) => {
    await page.goto("/");
    const skipLink = page.locator('a.skip-link[href="#main"]');
    await expect(skipLink).toBeAttached();
    await expect(skipLink).toHaveText(/skip to content/i);
  });

  test("returns 404 for nonexistent pages", async ({ page }) => {
    const response = await page.goto("/nonexistent-page-12345");
    expect(response?.status()).toBe(404);
  });

  test("main navigation is present on all pages", async ({ page }) => {
    for (const path of ["/", "/blog", "/projects", "/about"]) {
      await page.goto(path);
      await expect(page.locator('nav[aria-label="Main navigation"]')).toBeVisible();
    }
  });
});
