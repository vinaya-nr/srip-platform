import { expect, test } from "@playwright/test";

import { SripApiClient } from "./utils/api-client";
import { randomSuffix } from "./utils/auth-files";
import { LoginPage } from "./pom/login-page";

async function loginFreshAndGetToken(page: import("@playwright/test").Page, request: import("@playwright/test").APIRequestContext) {
  const suffix = randomSuffix();
  const email = `sales.ui.edge.${suffix}@example.com`;
  const password = "Passw0rd!123";
  const api = new SripApiClient(request);
  await api.register(email, password, `Sales UI Edge ${suffix}`);
  const login = await api.login(email, password);

  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login(email, password);
  await expect(page).toHaveURL(/\/dashboard$/);
  return { token: login.access_token, api };
}

test.describe("Sales UI negative/edge flows", () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test("checkout is disabled with empty cart", async ({ page, request }) => {
    await loginFreshAndGetToken(page, request);
    await page.goto("/sales");
    await expect(page.getByTestId("sales-checkout")).toBeDisabled();
  });

  test("prevents checkout when requested quantity exceeds stock (UI flow)", async ({ page, request }) => {
    const { token, api } = await loginFreshAndGetToken(page, request);
    const suffix = randomSuffix();
    const category = await api.createCategory(token, `UI Sales Cat ${suffix}`);

    const product = await api.createProduct(token, {
      category_id: category.id,
      name: `UI Sales Guard ${suffix}`,
      sku: `UIS-${suffix}`,
      price: 12,
      low_stock_threshold: 1
    });
    await api.createBatch(token, { product_id: product.id, quantity: 1, unit_cost: 6 });

    await page.goto("/sales");
    await page.getByTestId("sales-product-select").selectOption(product.id);
    await page.getByTestId("sales-add-product").click();

    const row = page.locator('[data-testid="sales-cart-table"] tbody tr').filter({ hasText: product.name }).first();
    await row.locator('input[type="number"]').fill("5");
    await page.getByTestId("sales-checkout").click();

    await expect(page.locator(".danger")).toContainText(/Insufficient stock|available/i);
  });
});
