import { test, expect } from "@playwright/test";

test.describe("JSON-LD structured data", () => {
  test("home page has WebSite JSON-LD schema", async ({ page }) => {
    await page.goto("/");
    const jsonLdScripts = page.locator('script[type="application/ld+json"]');
    await expect(jsonLdScripts.first()).toBeAttached();

    // Find the WebSite schema among all JSON-LD blocks
    const count = await jsonLdScripts.count();
    let found = false;
    for (let i = 0; i < count; i++) {
      const content = await jsonLdScripts.nth(i).textContent();
      try {
        const data = JSON.parse(content!);
        if (data["@type"] === "WebSite") {
          found = true;
          expect(data["@context"]).toBe("https://schema.org");
          expect(data.name).toBeTruthy();
          expect(data.url).toBeTruthy();
        }
      } catch {
        // Not valid JSON — skip
      }
    }
    expect(found).toBe(true);
  });

  test("blog list page has WebSite JSON-LD schema", async ({ page }) => {
    await page.goto("/blog");
    const jsonLdScripts = page.locator('script[type="application/ld+json"]');

    const count = await jsonLdScripts.count();
    let found = false;
    for (let i = 0; i < count; i++) {
      const content = await jsonLdScripts.nth(i).textContent();
      try {
        const data = JSON.parse(content!);
        if (data["@type"] === "WebSite") {
          found = true;
        }
      } catch {
        // skip
      }
    }
    expect(found).toBe(true);
  });

  test("hello-world post has BlogPosting JSON-LD with headline", async ({ page }) => {
    await page.goto("/blog/hello-world");
    const jsonLdScripts = page.locator('script[type="application/ld+json"]');

    const count = await jsonLdScripts.count();
    let found = false;
    for (let i = 0; i < count; i++) {
      const content = await jsonLdScripts.nth(i).textContent();
      try {
        const data = JSON.parse(content!);
        if (data["@type"] === "BlogPosting") {
          found = true;
          expect(data.headline).toBeTruthy();
          expect(data["@context"]).toBe("https://schema.org");
        }
      } catch {
        // skip
      }
    }
    expect(found).toBe(true);
  });

  test("hello-world post has BreadcrumbList JSON-LD", async ({ page }) => {
    await page.goto("/blog/hello-world");
    const jsonLdScripts = page.locator('script[type="application/ld+json"]');

    const count = await jsonLdScripts.count();
    let found = false;
    for (let i = 0; i < count; i++) {
      const content = await jsonLdScripts.nth(i).textContent();
      try {
        const data = JSON.parse(content!);
        if (data["@type"] === "BreadcrumbList") {
          found = true;
          expect(Array.isArray(data.itemListElement)).toBe(true);
          expect(data.itemListElement.length).toBeGreaterThan(0);
        }
      } catch {
        // skip
      }
    }
    expect(found).toBe(true);
  });
});

test.describe("Open Graph meta tags", () => {
  for (const path of ["/", "/blog", "/about"]) {
    test(`${path} has og:title meta tag`, async ({ page }) => {
      await page.goto(path);
      await expect(page.locator('meta[property="og:title"]')).toBeAttached();
    });

    test(`${path} has og:type meta tag`, async ({ page }) => {
      await page.goto(path);
      await expect(page.locator('meta[property="og:type"]')).toBeAttached();
    });

    test(`${path} has og:url meta tag`, async ({ page }) => {
      await page.goto(path);
      await expect(page.locator('meta[property="og:url"]')).toBeAttached();
    });

    test(`${path} has og:description meta tag`, async ({ page }) => {
      await page.goto(path);
      await expect(page.locator('meta[property="og:description"]')).toBeAttached();
    });
  }

  test("blog post has og:type of article", async ({ page }) => {
    await page.goto("/blog/hello-world");
    const ogType = page.locator('meta[property="og:type"]');
    await expect(ogType).toBeAttached();
    expect(await ogType.getAttribute("content")).toBe("article");
  });
});

test.describe("Canonical URLs", () => {
  for (const path of ["/", "/blog", "/blog/hello-world", "/about"]) {
    test(`${path} has canonical link element`, async ({ page }) => {
      await page.goto(path);
      await expect(page.locator('link[rel="canonical"]')).toBeAttached();
    });
  }
});

test.describe("RSS autodiscovery", () => {
  test("base template includes RSS autodiscovery link", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.locator('link[rel="alternate"][type="application/rss+xml"]')
    ).toBeAttached();
  });

  test("blog list page includes RSS autodiscovery link", async ({ page }) => {
    await page.goto("/blog");
    const rssLink = page.locator('link[rel="alternate"][type="application/rss+xml"]');
    await expect(rssLink).toBeAttached();
    const href = await rssLink.getAttribute("href");
    expect(href).toBe("/feed.xml");
  });
});
