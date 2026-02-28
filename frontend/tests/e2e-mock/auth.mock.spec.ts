import { expect, test } from "@playwright/test";

const API_BASE = process.env.E2E_API_BASE_URL ?? "http://localhost:8000/api/v1";

test("login success navigates to dashboard with mocked API", async ({ page }) => {
  await page.route(`${API_BASE}/auth/login`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "token-1",
        token_type: "bearer",
        expires_in: 900,
        user: { id: "u1", email: "mock@example.com", shop_id: "shop-mock" }
      })
    });
  });

  await page.route(`${API_BASE}/auth/refresh`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "token-1",
        token_type: "bearer",
        expires_in: 900,
        user: { id: "u1", email: "mock@example.com", shop_id: "shop-mock" }
      })
    });
  });

  await page.route(`${API_BASE}/dashboard/summary`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        today_sales_total: 1,
        today_revenue_total: "100.00",
        active_products_count: 1,
        low_stock_count: 0,
        unread_notifications_count: 0
      })
    });
  });

  await page.goto("/login");
  await page.getByTestId("login-email").fill("mock@example.com");
  await page.getByTestId("login-password").fill("Passw0rd!123");
  await page.getByTestId("login-submit").click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByTestId("dashboard-page")).toBeVisible();
});

test("login failure shows error with mocked API", async ({ page }) => {
  await page.route(`${API_BASE}/auth/login`, async (route) => {
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({
        success: false,
        error: { code: "AUTHORIZATION_FAILED", message: "Invalid email or password." }
      })
    });
  });

  await page.route(`${API_BASE}/auth/refresh`, async (route) => {
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({
        success: false,
        error: { code: "AUTHORIZATION_FAILED", message: "Refresh missing." }
      })
    });
  });

  await page.goto("/login");
  await page.getByTestId("login-email").fill("bad@example.com");
  await page.getByTestId("login-password").fill("bad");
  await page.getByTestId("login-submit").click();
  await expect(page.getByTestId("login-error")).toContainText("Invalid email or password.");
});

