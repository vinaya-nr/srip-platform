import { expect, test } from "@playwright/test";

const API_BASE = process.env.E2E_API_BASE_URL ?? "http://localhost:8000/api/v1";

test("products CRUD/search/filter works with mocked API (no DB writes)", async ({ page }) => {
  const categories = [
    { id: "cat-1", name: "General", created_at: new Date().toISOString() },
    { id: "cat-2", name: "Fresh", created_at: new Date().toISOString() }
  ];
  const products: Array<{
    id: string;
    category_id: string | null;
    name: string;
    sku: string;
    description: string | null;
    price: string;
    low_stock_threshold: number;
    is_active: boolean;
  }> = [
    {
      id: "p1",
      category_id: "cat-1",
      name: "Rice",
      sku: "SKU-RICE",
      description: null,
      price: "80",
      low_stock_threshold: 2,
      is_active: true
    }
  ];

  await page.route(`${API_BASE}/auth/refresh`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "token-prod",
        token_type: "bearer",
        expires_in: 900,
        user: { id: "u1", email: "prod@example.com", shop_id: "shop-mock" }
      })
    });
  });

  await page.route(`${API_BASE}/categories*`, async (route, request) => {
    if (request.method() !== "GET") {
      await route.fallback();
      return;
    }
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(categories) });
  });

  await page.route(`${API_BASE}/products*`, async (route, request) => {
    const method = request.method();
    const url = new URL(request.url());
    const pathParts = url.pathname.split("/");
    const maybeId = pathParts[pathParts.length - 1];

    if (method === "GET") {
      const search = (url.searchParams.get("search") ?? "").toLowerCase();
      const categoryId = url.searchParams.get("category_id");
      const skip = Number(url.searchParams.get("skip") ?? "0");
      const limit = Number(url.searchParams.get("limit") ?? "20");

      let items = [...products];
      if (search) {
        items = items.filter((p) => p.name.toLowerCase().includes(search) || p.sku.toLowerCase().includes(search));
      }
      if (categoryId) {
        items = items.filter((p) => p.category_id === categoryId);
      }
      const paged = items.slice(skip, skip + limit);
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: paged, total: items.length, skip, limit })
      });
      return;
    }

    if (method === "POST") {
      const payload = request.postDataJSON() as {
        category_id?: string | null;
        name: string;
        sku: string;
        description?: string | null;
        price: number;
        low_stock_threshold?: number;
      };
      const created = {
        id: `p${products.length + 1}`,
        category_id: payload.category_id ?? null,
        name: payload.name,
        sku: payload.sku,
        description: payload.description ?? null,
        price: String(payload.price),
        low_stock_threshold: payload.low_stock_threshold ?? 1,
        is_active: true
      };
      products.unshift(created);
      await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify(created) });
      return;
    }

    if (method === "PATCH") {
      const payload = request.postDataJSON() as Record<string, unknown>;
      const idx = products.findIndex((x) => x.id === maybeId);
      products[idx] = {
        ...products[idx],
        category_id: (payload.category_id as string | null | undefined) ?? products[idx].category_id,
        name: (payload.name as string | undefined) ?? products[idx].name,
        sku: (payload.sku as string | undefined) ?? products[idx].sku,
        description: (payload.description as string | null | undefined) ?? products[idx].description,
        price: payload.price !== undefined ? String(payload.price) : products[idx].price,
        low_stock_threshold:
          (payload.low_stock_threshold as number | undefined) ?? products[idx].low_stock_threshold,
        is_active: (payload.is_active as boolean | undefined) ?? products[idx].is_active
      };
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(products[idx]) });
      return;
    }

    if (method === "DELETE") {
      const idx = products.findIndex((x) => x.id === maybeId);
      if (idx >= 0) products.splice(idx, 1);
      await route.fulfill({ status: 204, body: "" });
      return;
    }

    await route.fallback();
  });

  await page.goto("/products");
  await expect(page.getByTestId("products-page")).toBeVisible();
  await expect(page.getByTestId("products-table")).toContainText("Rice");

  await page.getByTestId("products-add").click();
  const newRow = page.getByTestId("products-new-row");
  await newRow.locator("input").nth(0).fill("Apple");
  await newRow.locator("input").nth(1).fill("SKU-APPLE");
  await newRow.locator("select").nth(0).selectOption("cat-2");
  await newRow.locator("input").nth(2).fill("50");
  await newRow.locator("input").nth(3).fill("1");
  await newRow.getByRole("button", { name: "Save" }).click();
  await expect(page.getByTestId("products-table")).toContainText("Apple");

  await page.getByTestId("products-search-input").fill("Apple");
  await page.getByTestId("products-search-button").click();
  await expect(page.getByTestId("products-table")).toContainText("Apple");

  await page.getByTestId("products-category-filter").selectOption("cat-2");
  await expect(page.getByTestId("products-table")).toContainText("Apple");
});
