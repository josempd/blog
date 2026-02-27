import { test as base } from "@playwright/test";

export const test = base.extend<{ seededBlog: void }>({
  seededBlog: [
    async ({}, use) => {
      // Content synced via prestart — no extra seeding needed
      await use();
    },
    { auto: true },
  ],
});

export { expect } from "@playwright/test";
