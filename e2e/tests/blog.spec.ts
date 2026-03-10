import { test, expect } from "@playwright/test";

test.describe("Blog list page", () => {
  test("renders h1 heading", async ({ page }) => {
    await page.goto("/blog");
    await expect(page.locator("h1")).toBeVisible();
  });

  test("renders article elements", async ({ page }) => {
    await page.goto("/blog");
    if (await page.locator("article").count() === 0) { test.skip(); return; }
    await expect(page.locator("article").first()).toBeVisible();
  });

  test("renders time elements with datetime attribute", async ({ page }) => {
    await page.goto("/blog");
    if (await page.locator("article").count() === 0) { test.skip(); return; }
    await expect(page.locator("time[datetime]").first()).toBeVisible();
  });

  test("post cards have links to /blog/<slug>", async ({ page }) => {
    await page.goto("/blog");
    if (await page.locator("article").count() === 0) { test.skip(); return; }
    const link = page.locator("article a[href^='/blog/']").first();
    await expect(link).toBeVisible();
  });

  test("returns 404 for nonexistent post slug", async ({ page }) => {
    const response = await page.goto("/blog/nonexistent-slug-12345");
    expect(response?.status()).toBe(404);
  });
});

test.describe("Blog post detail page", () => {
  test("blog post loads with h1", async ({ page }) => {
    await page.goto("/blog");
    const postLink = page.locator("article a[href^='/blog/']").first();
    if (await postLink.count() === 0) { test.skip("No published posts"); return; }
    const href = await postLink.getAttribute("href");
    await page.goto(href!);
    await expect(page.locator("h1")).toBeVisible();
  });

  test("blog post has time element with datetime", async ({ page }) => {
    await page.goto("/blog");
    const postLink = page.locator("article a[href^='/blog/']").first();
    if (await postLink.count() === 0) { test.skip("No published posts"); return; }
    const href = await postLink.getAttribute("href");
    await page.goto(href!);
    await expect(page.locator("time[datetime]")).toBeVisible();
  });

  test("blog post has prose content", async ({ page }) => {
    await page.goto("/blog");
    const postLink = page.locator("article a[href^='/blog/']").first();
    if (await postLink.count() === 0) { test.skip("No published posts"); return; }
    const href = await postLink.getAttribute("href");
    await page.goto(href!);
    await expect(page.locator(".prose")).toBeVisible();
  });

  test("blog post has ToC sidebar with #toc-nav", async ({ page }) => {
    await page.goto("/blog");
    const postLink = page.locator("article a[href^='/blog/']").first();
    if (await postLink.count() === 0) { test.skip("No published posts"); return; }
    const href = await postLink.getAttribute("href");
    await page.goto(href!);
    await expect(page.locator("aside.post-sidebar")).toBeVisible();
    await expect(page.locator("#toc-nav")).toBeVisible();
  });

  test("blog post ToC contains links to headings", async ({ page }) => {
    await page.goto("/blog");
    const postLink = page.locator("article a[href^='/blog/']").first();
    if (await postLink.count() === 0) { test.skip("No published posts"); return; }
    const href = await postLink.getAttribute("href");
    await page.goto(href!);
    const tocLinks = page.locator("#toc-nav a");
    const count = await tocLinks.count();
    expect(count).toBeGreaterThan(0);
  });

  test("blog post has tag links", async ({ page }) => {
    await page.goto("/blog");
    const postLink = page.locator("article a[href^='/blog/']").first();
    if (await postLink.count() === 0) { test.skip("No published posts"); return; }
    const href = await postLink.getAttribute("href");
    await page.goto(href!);
    const postTags = page.locator('nav.post-tags[aria-label="Post tags"]');
    await expect(postTags).toBeVisible();
    const tagLinks = postTags.locator("a");
    const count = await tagLinks.count();
    expect(count).toBeGreaterThan(0);
    const firstHref = await tagLinks.first().getAttribute("href");
    expect(firstHref).toMatch(/\/blog\?tag=/);
  });

  test("post tags link back to filtered blog list", async ({ page }) => {
    await page.goto("/blog");
    const postLink = page.locator("article a[href^='/blog/']").first();
    if (await postLink.count() === 0) { test.skip("No published posts"); return; }
    const href = await postLink.getAttribute("href");
    await page.goto(href!);
    const firstTag = page.locator('nav.post-tags[aria-label="Post tags"] a').first();
    const tagHref = await firstTag.getAttribute("href");
    expect(tagHref).toMatch(/\/blog\?tag=/);
  });
});
