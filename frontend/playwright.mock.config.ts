import { defineConfig, devices } from "@playwright/test";

const frontendUrl = process.env.E2E_FRONTEND_URL ?? "http://localhost:3000";
const apiUrl = process.env.E2E_API_BASE_URL ?? "http://localhost:8000/api/v1";

export default defineConfig({
  testDir: "./tests/e2e-mock",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  timeout: 60_000,
  expect: {
    timeout: 10_000
  },
  reporter: [["list"]],
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
  metadata: {
    mockedApiBaseUrl: apiUrl
  },
  projects: [
    {
      name: "chromium-mock",
      use: {
        ...devices["Desktop Chrome"]
      }
    }
  ],
  outputDir: "test-results/mock-artifacts"
});

