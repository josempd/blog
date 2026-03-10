import { test, expect } from "@playwright/test";

test.describe("Print stylesheet", () => {
  test("header is hidden in print", async ({ page }) => {
    await page.goto("/");
    await page.emulateMedia({ media: "print" });
    await expect(page.locator(".site-header")).toBeHidden();
  });

  test("footer is hidden in print", async ({ page }) => {
    await page.goto("/");
    await page.emulateMedia({ media: "print" });
    await expect(page.locator(".site-footer")).toBeHidden();
  });

  test("main content is visible in print", async ({ page }) => {
    await page.goto("/");
    await page.emulateMedia({ media: "print" });
    await expect(page.locator("main#main")).toBeVisible();
  });

  test("tag list is hidden in print", async ({ page }) => {
    await page.goto("/blog");
    await page.emulateMedia({ media: "print" });
    const tagList = page.locator(".tag-list");
    if (await tagList.count() > 0) {
      await expect(tagList.first()).toBeHidden();
    }
  });

  test("search island is hidden in print", async ({ page }) => {
    await page.goto("/");
    await page.emulateMedia({ media: "print" });
    await expect(page.locator("#search-island")).toBeHidden();
  });
});
