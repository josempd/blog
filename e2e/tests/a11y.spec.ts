import { test, expect } from "@playwright/test";

test.describe("Skip-to-content", () => {
  test("skip-to-content is the first focusable element on home page", async ({ page }) => {
    await page.goto("/");
    await page.keyboard.press("Tab");
    const focused = page.locator(":focus");
    await expect(focused).toHaveAttribute("href", "#main");
    await expect(focused).toHaveText(/skip to content/i);
  });

  test("skip-to-content is the first focusable element on blog page", async ({ page }) => {
    await page.goto("/blog");
    await page.keyboard.press("Tab");
    const focused = page.locator(":focus");
    await expect(focused).toHaveAttribute("href", "#main");
    await expect(focused).toHaveText(/skip to content/i);
  });

  test("skip-to-content link points to #main landmark", async ({ page }) => {
    await page.goto("/");
    // #main must exist for the skip link to be useful
    await expect(page.locator("main#main")).toBeAttached();
  });
});

test.describe("Heading hierarchy", () => {
  test("blog list page has no skipped heading levels", async ({ page }) => {
    await page.goto("/blog");
    const headings = await page.locator("h1, h2, h3, h4, h5, h6").all();
    let lastLevel = 0;
    for (const heading of headings) {
      const tag = await heading.evaluate((el) => el.tagName);
      const level = parseInt(tag[1], 10);
      // Each heading may increase by at most 1 level relative to the previous
      expect(level).toBeLessThanOrEqual(lastLevel + 1);
      lastLevel = level;
    }
  });

  test("blog post page has exactly one h1", async ({ page }) => {
    await page.goto("/blog/hello-world");
    const h1Count = await page.locator("h1").count();
    expect(h1Count).toBe(1);
  });

  test("home page has exactly one h1", async ({ page }) => {
    await page.goto("/");
    const h1Count = await page.locator("h1").count();
    expect(h1Count).toBe(1);
  });
});

test.describe("ARIA landmarks and labels", () => {
  test("all nav elements have aria-label on home page", async ({ page }) => {
    await page.goto("/");
    const navs = page.locator("nav");
    const count = await navs.count();
    for (let i = 0; i < count; i++) {
      await expect(navs.nth(i)).toHaveAttribute("aria-label");
    }
  });

  test("all nav elements have aria-label on blog page", async ({ page }) => {
    await page.goto("/blog");
    const navs = page.locator("nav");
    const count = await navs.count();
    for (let i = 0; i < count; i++) {
      await expect(navs.nth(i)).toHaveAttribute("aria-label");
    }
  });

  test("all nav elements have aria-label on blog post page", async ({ page }) => {
    await page.goto("/blog/hello-world");
    const navs = page.locator("nav");
    const count = await navs.count();
    for (let i = 0; i < count; i++) {
      await expect(navs.nth(i)).toHaveAttribute("aria-label");
    }
  });

  test("page has main landmark", async ({ page }) => {
    await page.goto("/blog");
    await expect(page.locator("main")).toBeVisible();
  });

  test("page has header landmark", async ({ page }) => {
    await page.goto("/blog");
    await expect(page.locator("header")).toBeVisible();
  });

  test("theme toggle button has aria-label", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator('button[aria-label="Toggle dark mode"]')).toBeAttached();
  });
});

test.describe("Images", () => {
  test("all images on blog list have alt attribute", async ({ page }) => {
    await page.goto("/blog");
    const images = page.locator("img");
    const count = await images.count();
    for (let i = 0; i < count; i++) {
      await expect(images.nth(i)).toHaveAttribute("alt");
    }
  });

  test("all images on blog post have alt attribute", async ({ page }) => {
    await page.goto("/blog/hello-world");
    const images = page.locator("img");
    const count = await images.count();
    for (let i = 0; i < count; i++) {
      await expect(images.nth(i)).toHaveAttribute("alt");
    }
  });
});

test.describe("Interactive element accessibility", () => {
  test("search link has aria-label", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator('a[aria-label="Search"]')).toBeAttached();
  });

  test("page lang attribute is set", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
  });
});
