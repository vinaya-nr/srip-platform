import { defineConfig, devices } from "@playwright/test";

if (process.env.E2E_INTEGRATION !== "true") {
  throw new Error(
    "Integration Playwright config is disabled by default to avoid real DB writes. Use `npm run test:e2e` for mocked tests, or run integration with E2E_INTEGRATION=true."
  );
}

const frontendUrl = process.env.E2E_FRONTEND_URL ?? "http://localhost:3000";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  timeout: 60_000,
  expect: {
    timeout: 10_000
  },
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report" }],
    ["junit", { outputFile: "test-results/junit.xml" }]
  ],
  use: {
    baseURL: frontendUrl,
    testIdAttribute: "data-testid",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure"
  },
  webServer: {
    command: "npm run dev",
    url: `${frontendUrl}/login`,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000
  },
  projects: [
    {
      name: "setup",
      testMatch: /.*\.setup\.ts/
    },
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        storageState: "./tests/.auth/user.json"
      },
      dependencies: ["setup"]
    }
  ],
  outputDir: "test-results/artifacts"
});
