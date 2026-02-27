import { test, expect } from "@playwright/test";

test.describe("Search island", () => {
  test("search island container is present in the DOM", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("#search-island")).toBeAttached();
  });

  test("pressing / key opens search dialog", async ({ page }) => {
    await page.goto("/blog");
    // Wait for Svelte island to mount (renders the search trigger button)
    await expect(page.locator("#search-island .search-trigger")).toBeVisible();

    await page.keyboard.press("/");
    const dialog = page.locator('[role="dialog"]');
    await expect(dialog).toBeVisible();
  });

  test("Escape key closes search dialog", async ({ page }) => {
    await page.goto("/blog");
    await expect(page.locator("#search-island .search-trigger")).toBeVisible();

    await page.keyboard.press("/");
    const dialog = page.locator('[role="dialog"]');
    await expect(dialog).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(dialog).not.toBeVisible();
  });

  test("search results appear after typing a query", async ({ page }) => {
    await page.goto("/blog");
    await expect(page.locator("#search-island .search-trigger")).toBeVisible();

    await page.keyboard.press("/");
    const searchInput = page.locator('#search-island input[type="search"]');
    await expect(searchInput).toBeVisible();

    await searchInput.fill("hello");
    // Wait for search results to appear (debounced fetch)
    const results = page.locator(".search-dialog-results");
    await expect(results).toBeVisible({ timeout: 5000 });
  });
});

test.describe("Table of Contents island", () => {
  test("hello-world post has #toc-island div", async ({ page }) => {
    await page.goto("/blog/hello-world");
    await expect(page.locator("#toc-island")).toBeAttached();
  });

  test("ToC nav has links to headings", async ({ page }) => {
    await page.goto("/blog/hello-world");
    const tocLinks = page.locator("#toc-nav a");
    await expect(tocLinks.first()).toBeVisible();
    const count = await tocLinks.count();
    expect(count).toBeGreaterThan(0);
  });
});

test.describe("Islands without JavaScript", () => {
  test("#search-island is empty without JavaScript", async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto("/");

    const island = page.locator("#search-island");
    await expect(island).toBeAttached();
    // Without JS the island div should be empty (Svelte never mounts)
    await expect(island).toBeEmpty();

    await context.close();
  });

  test("#toc-island is empty without JavaScript", async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto("/blog/hello-world");

    const tocIsland = page.locator("#toc-island");
    await expect(tocIsland).toBeAttached();
    await expect(tocIsland).toBeEmpty();

    await context.close();
  });

  test("server-rendered ToC nav is visible without JavaScript", async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto("/blog/hello-world");

    // The static ToC from Jinja2 should still be visible
    await expect(page.locator("#toc-nav")).toBeVisible();

    await context.close();
  });
});
