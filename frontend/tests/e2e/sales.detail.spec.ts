import { expect, test } from "@playwright/test";

import { LoginPage } from "./pom/login-page";
import { SripApiClient } from "./utils/api-client";
import { randomSuffix } from "./utils/auth-files";

test("sale detail page renders summary and line items", async ({ page, request }) => {
  const api = new SripApiClient(request);
  const suffix = randomSuffix();
  const email = `sales.detail.${suffix}@example.com`;
  const password = "Passw0rd!123";
  await api.register(email, password, `Sales Detail ${suffix}`);
  const login = await api.login(email, password);
  const category = await api.createCategory(login.access_token, `Detail Cat ${suffix}`);

  const product = await api.createProduct(login.access_token, {
    category_id: category.id,
    name: `Detail Product ${suffix}`,
    sku: `DTL-${suffix}`,
    price: 20,
    low_stock_threshold: 1
  });
  await api.createBatch(login.access_token, { product_id: product.id, quantity: 4, unit_cost: 9 });
  const sale = (await api.createSale(login.access_token, [{ product_id: product.id, quantity: 2 }])) as { id: string };

  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login(email, password);
  await expect(page).toHaveURL(/\/dashboard$/);

  await page.goto(`/sales/${sale.id}`);
  await expect(page.getByTestId("sale-detail-page")).toBeVisible();
  await expect(page.getByTestId("sale-detail-summary")).toContainText("Sale ID:");
  await expect(page.getByTestId("sale-detail-items").locator("tbody tr")).toHaveCount(1);
});
