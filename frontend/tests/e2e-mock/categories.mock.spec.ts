import { expect, test } from "@playwright/test";

const API_BASE = process.env.E2E_API_BASE_URL ?? "http://localhost:8000/api/v1";

test("categories CRUD works with mocked API (no DB writes)", async ({ page }) => {
  const now = new Date().toISOString();
  const categories: Array<{ id: string; name: string; created_at: string }> = [
    { id: "c1", name: "Beverages", created_at: now }
  ];

  await page.route(`${API_BASE}/auth/refresh`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "token-cat",
        token_type: "bearer",
        expires_in: 900,
        user: { id: "u1", email: "cat@example.com", shop_id: "shop-mock" }
      })
    });
  });

  await page.route(`${API_BASE}/categories*`, async (route, request) => {
    const method = request.method();
    const url = new URL(request.url());
    const pathParts = url.pathname.split("/");
    const maybeId = pathParts[pathParts.length - 1];

    if (method === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(categories)
      });
      return;
    }

    if (method === "POST") {
      const payload = request.postDataJSON() as { name: string };
      const created = { id: `c${categories.length + 1}`, name: payload.name, created_at: new Date().toISOString() };
      categories.unshift(created);
      await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify(created) });
      return;
    }

    if (method === "PATCH") {
      const payload = request.postDataJSON() as { name: string };
      const idx = categories.findIndex((x) => x.id === maybeId);
      categories[idx] = { ...categories[idx], name: payload.name };
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(categories[idx]) });
      return;
    }

    if (method === "DELETE") {
      const idx = categories.findIndex((x) => x.id === maybeId);
      if (idx >= 0) categories.splice(idx, 1);
      await route.fulfill({ status: 204, body: "" });
      return;
    }

    await route.fallback();
  });

  await page.goto("/categories");
  await expect(page.getByTestId("categories-page")).toBeVisible();
  await expect(page.getByTestId("categories-table")).toContainText("Beverages");

  await page.getByTestId("categories-add").click();
  await page.getByTestId("categories-new-name").fill("Snacks");
  await page.getByTestId("categories-save-new").click();
  await expect(page.getByTestId("categories-table")).toContainText("Snacks");

  await page.getByTestId("categories-delete-c2").click();
  await expect(page.getByTestId("categories-delete-modal")).toBeVisible();
  await page.getByRole("button", { name: "No" }).click();
  await expect(page.getByTestId("categories-table")).toContainText("Snacks");
});
