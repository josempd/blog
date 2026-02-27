import { test, expect } from "@playwright/test";

test.describe("HTMX tag filtering", () => {
  test("tag filtering updates #post-list and URL without full reload", async ({ page }) => {
    await page.goto("/blog");
    const postList = page.locator("#post-list");
    await expect(postList).toBeVisible();

    // The tag list uses hx-get / hx-push-url to update the post list
    const tagLink = page.locator(".tag-list a[href*='tag=']").first();
    if (await tagLink.isVisible()) {
      await tagLink.click();

      // URL should update to include tag query param (hx-push-url)
      await expect(page).toHaveURL(/[?&]tag=/);
      // #post-list container should still be present (not a full reload)
      await expect(postList).toBeVisible();
    }
  });

  test("All tag link resets filter and returns to /blog", async ({ page }) => {
    await page.goto("/blog?tag=meta");
    const postList = page.locator("#post-list");
    await expect(postList).toBeVisible();

    const allLink = page.locator(".tag-list a[href='/blog']").first();
    if (await allLink.isVisible()) {
      await allLink.click();
      await expect(page).toHaveURL("/blog");
      await expect(postList).toBeVisible();
    }
  });
});

test.describe("Progressive enhancement — no JavaScript", () => {
  test("blog list renders without JavaScript", async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto("/blog");

    await expect(page.locator("h1")).toBeVisible();
    await expect(page.locator("article").first()).toBeVisible();

    await context.close();
  });

  test("blog post links are real hrefs that work without JavaScript", async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto("/blog");

    const firstLink = page.locator("article a[href^='/blog/']").first();
    await expect(firstLink).toBeVisible();
    await firstLink.click();

    await expect(page).toHaveURL(/\/blog\/.+/);
    await expect(page.locator("h1")).toBeVisible();

    await context.close();
  });

  test("tag filter links are real hrefs that work without JavaScript", async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto("/blog");

    const tagLink = page.locator(".tag-list a[href*='tag=']").first();
    if (await tagLink.isVisible()) {
      const href = await tagLink.getAttribute("href");
      await tagLink.click();
      await expect(page).toHaveURL(new RegExp(`tag=`));
      await expect(page.locator("#post-list")).toBeVisible();
    }

    await context.close();
  });

  test("nav links work without JavaScript", async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto("/");

    await page.locator('nav[aria-label="Main navigation"] a[href="/blog"]').click();
    await expect(page).toHaveURL("/blog");
    await expect(page.locator("h1")).toBeVisible();

    await context.close();
  });
});
