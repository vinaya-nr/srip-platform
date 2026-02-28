import { expect, test } from "@playwright/test";

import { SripApiClient } from "./utils/api-client";
import { E2E_API_BASE_URL } from "./utils/constants";
import { LoginPage } from "./pom/login-page";
import { randomSuffix } from "./utils/auth-files";

async function loginWithFreshUser(page: import("@playwright/test").Page, request: import("@playwright/test").APIRequestContext) {
  const suffix = randomSuffix();
  const email = `products.edge.${suffix}@example.com`;
  const password = "Passw0rd!123";
  const api = new SripApiClient(request);
  await api.register(email, password, `Products Edge ${suffix}`);

  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login(email, password);
  await expect(page).toHaveURL(/\/dashboard$/);
  await page.goto("/products");
  try {
    await expect(page.getByTestId("products-page")).toBeVisible({ timeout: 5000 });
  } catch {
    const retryLogin = new LoginPage(page);
    await retryLogin.goto();
    await retryLogin.login(email, password);
    await expect(page).toHaveURL(/\/dashboard$/);
    await page.goto("/products");
    await expect(page.getByTestId("products-page")).toBeVisible({ timeout: 30000 });
  }
}

test.describe("Products edge/negative flows", () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test("shows validation error when creating product with invalid form", async ({ page, request }) => {
    await loginWithFreshUser(page, request);
    await page.getByTestId("products-add").click();
    await page.getByRole("button", { name: "Save" }).first().click();
    await expect(page.getByTestId("products-message")).toContainText("Product name is required.");
  });

  test("empty-state rendering with no products", async ({ page, request }) => {
    await loginWithFreshUser(page, request);
    await page.route(`${E2E_API_BASE_URL}/products*`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, skip: 0, limit: 20 })
      });
    });
    await page.route(`${E2E_API_BASE_URL}/categories`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([])
      });
    });

    await page.goto("/products");
    await expect(page.getByTestId("products-page")).toBeVisible();
    await expect(page.getByTestId("products-table").locator("tbody tr")).toHaveCount(0);
  });

  test("network failure on list endpoint shows error state", async ({ page, request }) => {
    await loginWithFreshUser(page, request);
    await page.route(`${E2E_API_BASE_URL}/products*`, async (route) => {
      await route.abort("failed");
    });

    await page.goto("/products");
    await expect(page.locator(".danger")).toContainText(/failed|fetch|request/i);
  });
});
