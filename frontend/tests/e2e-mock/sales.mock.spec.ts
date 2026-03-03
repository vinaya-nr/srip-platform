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
        access_token: "mock-sales-token",
        token_type: "bearer",
        expires_in: 900,
        user: { id: "u1", email: "sales@example.com", shop_id: "shop-mock" }
      })
    });
  });

  await page.route(`${API_BASE}/products*`, async (route) => {
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
});

test("sales history defaults to today and reset restores today filters", async ({ page }) => {
  const seenSalesUrls: string[] = [];

  await page.route(`${API_BASE}/sales*`, async (route, request) => {
    if (request.method() !== "GET") {
      await route.fallback();
      return;
    }
    seenSalesUrls.push(request.url());
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

  await page.goto("/sales");
  await expect(page.getByTestId("sales-page")).toBeVisible();

  const today = todayLocalIso();
  await expect(page.getByTestId("sales-filter-from")).toHaveValue(today);
  await expect(page.getByTestId("sales-filter-to")).toHaveValue(today);
  expect(seenSalesUrls.length).toBeGreaterThan(0);
  expect(seenSalesUrls[0]).toContain(`from_date=${today}`);
  expect(seenSalesUrls[0]).toContain(`to_date=${today}`);

  await page.getByTestId("sales-filter-from").fill("2026-02-01");
  await page.getByTestId("sales-filter-to").fill("2026-02-28");
  await expect(page.getByTestId("sales-filter-from")).toHaveValue("2026-02-01");
  await expect(page.getByTestId("sales-filter-to")).toHaveValue("2026-02-28");

  await page.getByTestId("sales-filter-reset").click();
  await expect(page.getByTestId("sales-filter-from")).toHaveValue(today);
  await expect(page.getByTestId("sales-filter-to")).toHaveValue(today);
});

test("sale detail page shows Back button and returns to sales list", async ({ page }) => {
  await page.route(`${API_BASE}/sales?*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          {
            id: "sale-1",
            shop_id: "shop-mock",
            sale_number: "SRIP-20260226-AAA111",
            total_amount: "100.00",
            created_at: "2026-02-26T09:15:00Z",
            items: []
          }
        ],
        total: 1,
        skip: 0,
        limit: 20
      })
    });
  });

  await page.route(`${API_BASE}/sales/sale-1`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "sale-1",
        shop_id: "shop-mock",
        sale_number: "SRIP-20260226-AAA111",
        total_amount: "100.00",
        created_at: "2026-02-26T09:15:00Z",
        items: [
          { product_id: "p1", product_name: "Milk", quantity: 1, unit_price: "100.00", line_total: "100.00" }
        ]
      })
    });
  });

  await page.goto("/sales");
  await expect(page.getByTestId("sales-page")).toBeVisible();
  await page.getByRole("link", { name: "View" }).first().click();

  await expect(page.getByTestId("sale-detail-page")).toBeVisible();
  await expect(page.getByTestId("sale-detail-back")).toBeVisible();
  await expect(page.getByTestId("sale-detail-items")).toContainText("Milk");
  await page.getByTestId("sale-detail-back").click();
  await expect(page).toHaveURL(/\/sales$/);
});
