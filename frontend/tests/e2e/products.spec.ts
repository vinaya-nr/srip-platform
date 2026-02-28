import { expect, test } from "@playwright/test";

import { SripApiClient } from "./utils/api-client";
import { randomSuffix } from "./utils/auth-files";
import { ensureUiAuthenticated } from "./utils/ensure-ui-auth";
import { getSetupUserToken } from "./utils/session";

test("products flow: create, list, search, filter, update, delete", async ({ page, request }) => {
  const api = new SripApiClient(request);
  const token = await getSetupUserToken(request);
  const suffix = randomSuffix();

  const category = await api.createCategory(token, `Products Cat ${suffix}`);
  const product = await api.createProduct(token, {
    category_id: category.id,
    name: `E2E Product ${suffix}`,
    sku: `SKU-${suffix}`,
    price: 125,
    low_stock_threshold: 2
  });

  await ensureUiAuthenticated(page);
  await page.goto("/products");
  await expect(page.getByTestId("products-table")).toContainText(product.name);

  const searched = await api.listProducts(token, { search: suffix });
  expect(searched.items.some((item) => item.id === product.id)).toBeTruthy();

  const filtered = await api.listProducts(token, { categoryId: category.id });
  expect(filtered.items.some((item) => item.id === product.id)).toBeTruthy();
  expect(filtered.items.every((item) => item.category_id === category.id)).toBeTruthy();

  const updatedName = `E2E Product Updated ${suffix}`;
  await api.updateProduct(token, product.id, { name: updatedName, price: 150 });
  await page.reload();
  await expect(page.getByTestId("products-table")).toContainText(updatedName);

  await api.deleteProduct(token, product.id);
  await page.reload();
  await expect(page.getByTestId("products-table")).not.toContainText(updatedName);
});
