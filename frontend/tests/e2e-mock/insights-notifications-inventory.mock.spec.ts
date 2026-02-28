import { expect, test } from "@playwright/test";

const API_BASE = process.env.E2E_API_BASE_URL ?? "http://localhost:8000/api/v1";

function todayLocalIso(): string {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

test.beforeEach(async ({ page }) => {
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
});

test("notifications defaults to today date range and sends date filters", async ({ page }) => {
  const seenUrls: string[] = [];
  await page.route(`${API_BASE}/notifications*`, async (route, request) => {
    seenUrls.push(request.url());
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [],
        total: 0,
        skip: 0,
        limit: 20
      })
    });
  });

  await page.goto("/notifications");
  await expect(page.getByTestId("notifications-page")).toBeVisible();

  const today = todayLocalIso();
  await expect(page.getByTestId("notifications-from-date")).toHaveValue(today);
  await expect(page.getByTestId("notifications-to-date")).toHaveValue(today);

  expect(seenUrls.length).toBeGreaterThan(0);
  expect(seenUrls[0]).toContain(`from_date=${today}`);
  expect(seenUrls[0]).toContain(`to_date=${today}`);
});

test("notifications shows validation when from-date is after to-date", async ({ page }) => {
  await page.route(`${API_BASE}/notifications*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [],
        total: 0,
        skip: 0,
        limit: 20
      })
    });
  });

  await page.goto("/notifications");
  await expect(page.getByTestId("notifications-page")).toBeVisible();

  await page.getByTestId("notifications-from-date").fill("2026-02-27");
  await page.getByTestId("notifications-to-date").fill("2026-02-26");

  await expect(page.getByText("From date cannot be after To date.")).toBeVisible();
  await expect(page.getByTestId("notifications-table")).toContainText("No notifications in selected date range.");
});

test("inventory hides inactive rows by default and shows them when toggle enabled", async ({ page }) => {
  await page.route(`${API_BASE}/inventory/batches*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          {
            id: "batch-active-1",
            shop_id: "shop-mock",
            product_id: "prod-active-1",
            quantity: 10,
            unit_cost: "9.00",
            expiry_date: "2031-01-01"
          },
          {
            id: "batch-inactive-1",
            shop_id: "shop-mock",
            product_id: "prod-inactive-1",
            quantity: 4,
            unit_cost: "5.00",
            expiry_date: "2031-02-01"
          }
        ],
        total: 2,
        skip: 0,
        limit: 20
      })
    });
  });

  await page.route(`${API_BASE}/products*`, async (route, request) => {
    const url = new URL(request.url());
    const isActive = url.searchParams.get("is_active");
    const items =
      isActive === "false"
        ? [
            {
              id: "prod-inactive-1",
              shop_id: "shop-mock",
              category_id: "cat-1",
              name: "Milk Vendor B",
              sku: "MLK-B",
              description: null,
              price: "22.00",
              low_stock_threshold: 2,
              is_active: false
            }
          ]
        : [
            {
              id: "prod-active-1",
              shop_id: "shop-mock",
              category_id: "cat-1",
              name: "Milk Vendor A",
              sku: "MLK-A",
              description: null,
              price: "20.00",
              low_stock_threshold: 2,
              is_active: true
            }
          ];

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items,
        total: items.length,
        skip: 0,
        limit: 100
      })
    });
  });

  await page.goto("/inventory");
  await expect(page.getByTestId("inventory-page")).toBeVisible();
  await expect(page.getByTestId("inventory-table")).toContainText("Milk Vendor A (MLK-A)");
  await expect(page.getByTestId("inventory-table")).not.toContainText("Milk Vendor B (MLK-B) [Inactive]");

  await page.getByTestId("inventory-show-inactive-toggle").check();
  await expect(page.getByTestId("inventory-table")).toContainText("Milk Vendor B (MLK-B) [Inactive]");
});

test("insights tabs render monthly comparison by default and data log on switch", async ({ page }) => {
  await page.route(`${API_BASE}/analytics/monthly-comparison*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        {
          month: "2026-02",
          total_revenue: 145,
          total_sales: 3
        }
      ])
    });
  });

  await page.route(`${API_BASE}/analytics/snapshots*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        {
          id: "snap-1",
          shop_id: "shop-mock",
          snapshot_type: "sale_event",
          payload: {
            sale_number: "SRIP-20260226-TEST",
            total_amount: 100
          },
          created_at: new Date().toISOString()
        }
      ])
    });
  });

  await page.goto("/analytics");
  await expect(page.getByTestId("analytics-page")).toBeVisible();
  await expect(page.getByTestId("insights-monthly-card")).toBeVisible();

  await page.getByTestId("data-log-tab").click();
  await expect(page.getByTestId("analytics-date-filter")).toBeVisible();
  await expect(page.getByTestId("analytics-snapshot-card")).toBeVisible();
});
