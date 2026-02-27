import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: "http://localhost:8000",
    trace: "on-first-retry",
  },
  webServer: {
    command: "docker compose up -d",
    url: "http://localhost:8000/api/v1/utils/health-check/",
    reuseExistingServer: true,
    timeout: 30_000,
    cwd: "..",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
