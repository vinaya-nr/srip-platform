import { expect, test } from "@playwright/test";

import { LoginPage } from "./pom/login-page";
import { SripApiClient } from "./utils/api-client";
import { randomSuffix } from "./utils/auth-files";

test.describe("Inventory batch inline UI", () => {
  test("shows validation error for empty batch form", async ({ page, request }) => {
    const api = new SripApiClient(request);
    const suffix = randomSuffix();
    const email = `inventory.batch.val.${suffix}@example.com`;
    const password = "Passw0rd!123";
    await api.register(email, password, `Inventory Batch ${suffix}`);

    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login(email, password);
    await expect(page).toHaveURL(/\/dashboard$/);

    await page.goto("/inventory");
    await page.getByTestId("inventory-add-batch").click();
    await page.getByTestId("inventory-batch-save").click();
    await expect(page.getByTestId("inventory-message")).toContainText("Product is required.");
  });

  test("creates batch from inline row and shows success", async ({ page, request }) => {
    const api = new SripApiClient(request);
    const suffix = randomSuffix();
    const email = `inventory.batch.ok.${suffix}@example.com`;
    const password = "Passw0rd!123";
    await api.register(email, password, `Inventory Batch ${suffix}`);
    const login = await api.login(email, password);
    const category = await api.createCategory(login.access_token, `Batch Cat ${suffix}`);
    const product = await api.createProduct(login.access_token, {
      category_id: category.id,
      name: `Batch Product ${suffix}`,
      sku: `BCH-${suffix}`,
      price: 10,
      low_stock_threshold: 1
    });

    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login(email, password);
    await expect(page).toHaveURL(/\/dashboard$/);

    await page.goto("/inventory");
    await page.getByTestId("inventory-add-batch").click();
    await page.getByTestId("inventory-batch-product").selectOption(product.id);
    await page.getByTestId("inventory-batch-quantity").fill("5");
    await page.getByTestId("inventory-batch-unit-cost").fill("4.50");
    await page.getByTestId("inventory-batch-expiry").fill("2030-12-31");
    await page.getByTestId("inventory-batch-save").click();

    await expect(page.getByTestId("inventory-message")).toContainText("Batch created successfully.");
    await expect(page.getByTestId("inventory-table")).toContainText(product.id);
  });

  test("edits batch metadata inline and shows success", async ({ page, request }) => {
    const api = new SripApiClient(request);
    const suffix = randomSuffix();
    const email = `inventory.batch.edit.${suffix}@example.com`;
    const password = "Passw0rd!123";
    await api.register(email, password, `Inventory Batch ${suffix}`);
    const login = await api.login(email, password);
    const category = await api.createCategory(login.access_token, `Batch Cat ${suffix}`);
    const product = await api.createProduct(login.access_token, {
      category_id: category.id,
      name: `Batch Product ${suffix}`,
      sku: `BCH-${suffix}`,
      price: 10,
      low_stock_threshold: 1
    });
    await api.createBatch(login.access_token, {
      product_id: product.id,
      quantity: 5,
      unit_cost: 4.5,
      expiry_date: "2030-12-31"
    });

    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login(email, password);
    await expect(page).toHaveURL(/\/dashboard$/);

    await page.goto("/inventory");
    await page.getByTestId("inventory-edit").first().click();
    await page.getByTestId("inventory-edit-unit-cost").fill("9.25");
    await page.getByTestId("inventory-edit-expiry").fill("2031-01-15");
    await page.getByTestId("inventory-edit-save").click();

    await expect(page.getByTestId("inventory-message")).toContainText("Batch updated successfully.");
    await expect(page.getByTestId("inventory-table")).toContainText("9.25");
    await expect(page.getByTestId("inventory-table")).toContainText("2031-01-15");
  });
});
