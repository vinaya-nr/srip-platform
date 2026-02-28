import { expect, test } from "@playwright/test";

import { SripApiClient } from "./utils/api-client";
import { randomSuffix } from "./utils/auth-files";
import { E2E_API_BASE_URL } from "./utils/constants";
import { getSetupUserToken } from "./utils/session";

test("sales flow: create sale and validate stock deduction", async ({ request }) => {
  const api = new SripApiClient(request);
  const token = await getSetupUserToken(request);
  const suffix = randomSuffix();
  const category = await api.createCategory(token, `Sales Cat ${suffix}`);

  const product = await api.createProduct(token, {
    category_id: category.id,
    name: `Sales Product ${suffix}`,
    sku: `SAL-${suffix}`,
    price: 15,
    low_stock_threshold: 1
  });
  await api.createBatch(token, { product_id: product.id, quantity: 10, unit_cost: 8 });

  await api.createSale(token, [{ product_id: product.id, quantity: 3 }]);
  const stock = await api.getProductStock(token, product.id);
  expect(stock.current_stock).toBe(7);
});

test("sales flow: prevent sale when stock is insufficient", async ({ request }) => {
  const api = new SripApiClient(request);
  const token = await getSetupUserToken(request);
  const suffix = randomSuffix();
  const category = await api.createCategory(token, `Guard Cat ${suffix}`);

  const product = await api.createProduct(token, {
    category_id: category.id,
    name: `Sales Guard ${suffix}`,
    sku: `SFG-${suffix}`,
    price: 11,
    low_stock_threshold: 1
  });
  await api.createBatch(token, { product_id: product.id, quantity: 1, unit_cost: 5 });

  const response = await request.post(`${E2E_API_BASE_URL}/sales`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { items: [{ product_id: product.id, quantity: 5 }] }
  });
  expect(response.status()).toBe(422);
});
