import { test, expect } from "@playwright/test";

test.describe("Responsive — mobile", () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test("hamburger button is visible", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator(".nav-menu-toggle")).toBeVisible();
  });

  test("nav links are hidden by default", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("#nav-menu")).toBeHidden();
  });

  test("clicking hamburger reveals nav links", async ({ page }) => {
    await page.goto("/");
    await page.locator(".nav-menu-toggle").click();
    await expect(page.locator("#nav-menu")).toBeVisible();
  });

  test("aria-expanded toggles correctly", async ({ page }) => {
    await page.goto("/");
    const toggle = page.locator(".nav-menu-toggle");

    await expect(toggle).toHaveAttribute("aria-expanded", "false");

    await toggle.click();
    await expect(toggle).toHaveAttribute("aria-expanded", "true");

    await toggle.click();
    await expect(toggle).toHaveAttribute("aria-expanded", "false");
  });

  test("site title is visible", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator(".site-title")).toBeVisible();
  });
});

test.describe("Responsive — desktop", () => {
  test.use({ viewport: { width: 1280, height: 800 } });

  test("hamburger is hidden", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator(".nav-menu-toggle")).toBeHidden();
  });

  test("nav links are visible", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator('nav[aria-label="Main navigation"]')).toBeVisible();
  });
});
