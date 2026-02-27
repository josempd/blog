import { test, expect } from "@playwright/test";

test.describe("Blog list page", () => {
  test("renders h1 heading", async ({ page }) => {
    await page.goto("/blog");
    await expect(page.locator("h1")).toBeVisible();
  });

  test("renders article elements", async ({ page }) => {
    await page.goto("/blog");
    await expect(page.locator("article").first()).toBeVisible();
  });

  test("renders time elements with datetime attribute", async ({ page }) => {
    await page.goto("/blog");
    await expect(page.locator("time[datetime]").first()).toBeVisible();
  });

  test("post cards have links to /blog/<slug>", async ({ page }) => {
    await page.goto("/blog");
    const link = page.locator("article a[href^='/blog/']").first();
    await expect(link).toBeVisible();
  });

  test("returns 404 for nonexistent post slug", async ({ page }) => {
    const response = await page.goto("/blog/nonexistent-slug-12345");
    expect(response?.status()).toBe(404);
  });
});

test.describe("Blog post detail page", () => {
  test("hello-world post loads with h1", async ({ page }) => {
    await page.goto("/blog/hello-world");
    await expect(page.locator("h1")).toBeVisible();
  });

  test("hello-world post has time element with datetime", async ({ page }) => {
    await page.goto("/blog/hello-world");
    await expect(page.locator("time[datetime]")).toBeVisible();
  });

  test("hello-world post has prose content", async ({ page }) => {
    await page.goto("/blog/hello-world");
    await expect(page.locator(".prose")).toBeVisible();
  });

  test("hello-world post has ToC sidebar with #toc-nav", async ({ page }) => {
    await page.goto("/blog/hello-world");
    await expect(page.locator("aside.post-sidebar")).toBeVisible();
    await expect(page.locator("#toc-nav")).toBeVisible();
  });

  test("hello-world post ToC contains links to headings", async ({ page }) => {
    await page.goto("/blog/hello-world");
    const tocLinks = page.locator("#toc-nav a");
    const count = await tocLinks.count();
    expect(count).toBeGreaterThan(0);
  });

  test("hello-world post displays Meta tag", async ({ page }) => {
    await page.goto("/blog/hello-world");
    const postTags = page.locator('nav.post-tags[aria-label="Post tags"]');
    await expect(postTags).toBeVisible();
    await expect(postTags.locator('a', { hasText: "Meta" })).toBeVisible();
  });

  test("hello-world post displays Writing tag", async ({ page }) => {
    await page.goto("/blog/hello-world");
    const postTags = page.locator('nav.post-tags[aria-label="Post tags"]');
    await expect(postTags.locator('a', { hasText: "Writing" })).toBeVisible();
  });

  test("post tags link back to filtered blog list", async ({ page }) => {
    await page.goto("/blog/hello-world");
    const firstTag = page.locator('nav.post-tags[aria-label="Post tags"] a').first();
    const href = await firstTag.getAttribute("href");
    expect(href).toMatch(/\/blog\?tag=/);
  });
});
