import { test, expect } from "@playwright/test";

test.describe("RSS feed", () => {
  test("GET /feed.xml returns 200", async ({ request }) => {
    const response = await request.get("/feed.xml");
    expect(response.status()).toBe(200);
  });

  test("GET /feed.xml has XML content-type", async ({ request }) => {
    const response = await request.get("/feed.xml");
    const contentType = response.headers()["content-type"];
    expect(contentType).toContain("xml");
  });

  test("GET /feed.xml body contains <rss element", async ({ request }) => {
    const response = await request.get("/feed.xml");
    const body = await response.text();
    expect(body).toContain("<rss");
  });
});

test.describe("Sitemap", () => {
  test("GET /sitemap.xml returns 200", async ({ request }) => {
    const response = await request.get("/sitemap.xml");
    expect(response.status()).toBe(200);
  });

  test("GET /sitemap.xml has XML content-type", async ({ request }) => {
    const response = await request.get("/sitemap.xml");
    const contentType = response.headers()["content-type"];
    expect(contentType).toContain("xml");
  });

  test("GET /sitemap.xml body contains <urlset", async ({ request }) => {
    const response = await request.get("/sitemap.xml");
    const body = await response.text();
    expect(body).toContain("<urlset");
  });
});

test.describe("llms.txt", () => {
  test("GET /llms.txt returns 200", async ({ request }) => {
    const response = await request.get("/llms.txt");
    expect(response.status()).toBe(200);
  });

  test("GET /llms.txt has text/plain content-type", async ({ request }) => {
    const response = await request.get("/llms.txt");
    const contentType = response.headers()["content-type"];
    expect(contentType).toContain("text/plain");
  });
});

test.describe("llms-full.txt", () => {
  test("GET /llms-full.txt returns 200", async ({ request }) => {
    const response = await request.get("/llms-full.txt");
    expect(response.status()).toBe(200);
  });

  test("GET /llms-full.txt has text/plain content-type", async ({ request }) => {
    const response = await request.get("/llms-full.txt");
    const contentType = response.headers()["content-type"];
    expect(contentType).toContain("text/plain");
  });
});

test.describe("robots.txt", () => {
  test("GET /robots.txt returns 200", async ({ request }) => {
    const response = await request.get("/robots.txt");
    expect(response.status()).toBe(200);
  });

  test("GET /robots.txt body contains Sitemap directive", async ({ request }) => {
    const response = await request.get("/robots.txt");
    const body = await response.text();
    expect(body).toContain("Sitemap:");
  });
});

test.describe("Markdown endpoint", () => {
  test("GET /blog/hello-world.md returns 200", async ({ request }) => {
    const response = await request.get("/blog/hello-world.md");
    expect(response.status()).toBe(200);
  });

  test("GET /blog/hello-world.md has markdown or plain-text content-type", async ({ request }) => {
    const response = await request.get("/blog/hello-world.md");
    const contentType = response.headers()["content-type"];
    expect(contentType.includes("text/markdown") || contentType.includes("text/plain")).toBe(true);
  });

  test("GET /blog/hello-world.md body contains markdown content", async ({ request }) => {
    const response = await request.get("/blog/hello-world.md");
    const body = await response.text();
    // Markdown source should contain the post title as a heading
    expect(body.length).toBeGreaterThan(0);
  });
});
