import { expect, test } from "@playwright/test";

const API_BASE = process.env.E2E_API_BASE_URL ?? "http://localhost:8000/api/v1";

test("dashboard and notifications render with mocked API only", async ({ page }) => {
  await page.route(`${API_BASE}/auth/refresh`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "mock-access-token",
        token_type: "bearer",
        expires_in: 900,
        user: { id: "u-mock", email: "mock@example.com", shop_id: "shop-mock" }
      })
    });
  });

  await page.route(`${API_BASE}/dashboard/summary`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        today_sales_total: 3,
        today_revenue_total: "240.00",
        active_products_count: 8,
        low_stock_count: 1,
        unread_notifications_count: 1
      })
    });
  });

  await page.route(`${API_BASE}/notifications*`, async (route, request) => {
    if (request.method() === "PATCH") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "n-1",
          shop_id: "shop-mock",
          event_type: "low_stock_detected",
          title: "Low Stock Alert",
          message: "Milk stock is 1 (threshold 2).",
          is_read: true,
          created_at: new Date().toISOString()
        })
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          {
            id: "n-1",
            shop_id: "shop-mock",
            event_type: "low_stock_detected",
            title: "Low Stock Alert",
            message: "Milk stock is 1 (threshold 2).",
            is_read: false,
            created_at: new Date().toISOString()
          }
        ],
        total: 1,
        skip: 0,
        limit: 20
      })
    });
  });

  await page.goto("/dashboard");
  await expect(page.getByTestId("dashboard-page")).toBeVisible();
  await expect(page.getByTestId("summary-low-stock")).toContainText("1");

  await page.getByTestId("summary-low-stock").click();
  await expect(page).toHaveURL(/\/notifications$/);
  await expect(page.getByTestId("notifications-page")).toBeVisible();
  await expect(page.getByTestId("notifications-table")).toContainText("Low Stock Alert");
  await expect(page.getByTestId("notifications-table")).toContainText("Milk stock is 1 (threshold 2).");
});

