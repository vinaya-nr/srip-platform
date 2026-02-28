import { expect, test } from "@playwright/test";

import { E2E_API_BASE_URL } from "./utils/constants";
import { ensureUiAuthenticated } from "./utils/ensure-ui-auth";
import { LoginPage } from "./pom/login-page";
import { SripApiClient } from "./utils/api-client";
import { randomSuffix } from "./utils/auth-files";

test.describe("Resilience and session handling", () => {
  test("redirects to login when bootstrap refresh fails", async ({ page }) => {
    await page.route(`${E2E_API_BASE_URL}/auth/refresh`, async (route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({
          success: false,
          error: { code: "AUTHORIZATION_FAILED", message: "Refresh failed for test." }
        })
      });
    });

    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  });

  test("redirects to login from protected products route when refresh is expired", async ({ page }) => {
    await page.route(`${E2E_API_BASE_URL}/auth/refresh`, async (route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({
          success: false,
          error: { code: "AUTHORIZATION_FAILED", message: "Expired refresh token." }
        })
      });
    });

    await page.goto("/products");
    await expect(page).toHaveURL(/\/login$/);
  });

  test("shows loading state during slow backend response", async ({ page }) => {
    await ensureUiAuthenticated(page);
    await page.route(`${E2E_API_BASE_URL}/dashboard/summary`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 2500));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          today_sales_total: 2,
          today_revenue_total: "120.00",
          active_products_count: 3,
          low_stock_count: 1,
          unread_notifications_count: 0
        })
      });
    });

    const startedAt = Date.now();
    await page.goto("/dashboard");
    await expect(page.getByTestId("summary-today-sales")).toBeVisible();
    expect(Date.now() - startedAt).toBeGreaterThanOrEqual(2_000);
  });

  test("shows error state when notifications endpoint returns server error", async ({ page }) => {
    const suffix = randomSuffix();
    const email = `resilience.notifications.${suffix}@example.com`;
    const password = "Passw0rd!123";
    const api = new SripApiClient(page.request);
    await api.register(email, password, `Resilience Notifications ${suffix}`);

    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login(email, password);
    await expect(page).toHaveURL(/\/dashboard$/);

    await page.route(`${E2E_API_BASE_URL}/notifications*`, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({
          success: false,
          error: { code: "INTERNAL_SERVER_ERROR", message: "Injected notifications failure." }
        })
      });
    });

    await page.goto("/notifications");
    await expect(page.locator(".danger")).toContainText("Injected notifications failure.");
  });
});
