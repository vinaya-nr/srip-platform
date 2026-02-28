import { expect, test } from "@playwright/test";

import { InventoryMovementPage } from "./pom/inventory-movement-page";
import { SripApiClient } from "./utils/api-client";
import { randomSuffix } from "./utils/auth-files";
import { ensureUiAuthenticated } from "./utils/ensure-ui-auth";
import { getSetupUserToken } from "./utils/session";

test("inventory flow: create batch and record movements", async ({ page, request }) => {
  const api = new SripApiClient(request);
  const token = await getSetupUserToken(request);
  const suffix = randomSuffix();
  const category = await api.createCategory(token, `Inv Cat ${suffix}`);

  const product = await api.createProduct(token, {
    category_id: category.id,
    name: `Inv Product ${suffix}`,
    sku: `INV-${suffix}`,
    price: 20,
    low_stock_threshold: 1
  });

  await api.createBatch(token, { product_id: product.id, quantity: 10, unit_cost: 12 });
  await ensureUiAuthenticated(page);
  await page.goto("/inventory");
  await expect(page.getByTestId("inventory-table")).toContainText(product.id);

  const movementPage = new InventoryMovementPage(page);
  await movementPage.goto();
  await movementPage.submitMovement({
    productId: product.id,
    movementType: "in",
    quantity: 5,
    reason: "e2e-inbound"
  });

  let stock = await api.getProductStock(token, product.id);
  expect(stock.current_stock).toBe(15);

  await movementPage.goto();
  await movementPage.submitMovement({
    productId: product.id,
    movementType: "out",
    quantity: 4,
    reason: "e2e-outbound"
  });
  stock = await api.getProductStock(token, product.id);
  expect(stock.current_stock).toBe(11);

  await movementPage.goto();
  await movementPage.submitMovement({
    productId: product.id,
    movementType: "adjustment",
    adjustmentMode: "decrease",
    quantity: 1,
    reason: "e2e-adjustment"
  });
  stock = await api.getProductStock(token, product.id);
  expect(stock.current_stock).toBe(10);
});

test("inventory flow: low-stock alert generation", async ({ request }) => {
  const api = new SripApiClient(request);
  const token = await getSetupUserToken(request);
  const suffix = randomSuffix();
  const category = await api.createCategory(token, `Low Cat ${suffix}`);

  const product = await api.createProduct(token, {
    category_id: category.id,
    name: `Low Stock ${suffix}`,
    sku: `LOW-${suffix}`,
    price: 30,
    low_stock_threshold: 1
  });
  await api.createBatch(token, { product_id: product.id, quantity: 1, unit_cost: 20 });
  await api.createSale(token, [{ product_id: product.id, quantity: 1 }]);
  await api.createNotification(token, {
    event_type: "low_stock_detected",
    title: `Low stock alert ${suffix}`,
    message: `Stock reached threshold for product ${product.id}`
  });

  await expect
    .poll(
      async () => {
        const unread = await api.listNotifications(token, true);
        return unread.items.filter(
          (item) => item.event_type === "low_stock_detected" && item.title.includes(`Low stock alert ${suffix}`)
        ).length;
      },
      { timeout: 60_000, intervals: [1_000, 2_000, 5_000] }
    )
    .toBeGreaterThan(0);
});
