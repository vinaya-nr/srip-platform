import { expect, test } from "@playwright/test";

import { SripApiClient } from "./utils/api-client";
import { LoginPage } from "./pom/login-page";
import { randomSuffix } from "./utils/auth-files";
import { E2E_API_BASE_URL } from "./utils/constants";

async function loginWithFreshUser(page: import("@playwright/test").Page, request: import("@playwright/test").APIRequestContext) {
  const suffix = randomSuffix();
  const email = `categories.edge.${suffix}@example.com`;
  const password = "Passw0rd!123";
  const api = new SripApiClient(request);
  await api.register(email, password, `Categories Edge ${suffix}`);

  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login(email, password);
  await expect(page).toHaveURL(/\/dashboard$/);
  await page.goto("/categories");
  await expect(page.getByTestId("categories-add")).toBeVisible();
}

test.describe("Categories edge/negative flows", () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test("shows validation error when creating category with empty name", async ({ page, request }) => {
    await loginWithFreshUser(page, request);
    await page.getByTestId("categories-add").click();
    await page.getByTestId("categories-save-new").click();
    await expect(page.getByTestId("categories-message")).toContainText("Category name is required.");
  });

  test("delete confirmation cancel keeps row unchanged", async ({ page, request }) => {
    const suffix = randomSuffix();
    const categoryName = `Delete-Cancel ${suffix}`;

    await loginWithFreshUser(page, request);
    await page.getByTestId("categories-add").click();
    await page.getByTestId("categories-new-name").fill(categoryName);
    await page.getByTestId("categories-save-new").click();
    await expect(page.getByTestId("categories-message")).toContainText("Category created successfully.");

    const row = page.locator('[data-testid="categories-table"] tbody tr').filter({ hasText: categoryName }).first();
    await row.getByRole("button", { name: "Delete" }).click();
    await expect(page.getByTestId("categories-delete-modal")).toBeVisible();
    await page.getByRole("button", { name: "No" }).click();
    await expect(page.getByTestId("categories-delete-modal")).toHaveCount(0);
    await expect(page.getByTestId("categories-table")).toContainText(categoryName);
  });

  test("shows backend error message on create failure", async ({ page, request }) => {
    await loginWithFreshUser(page, request);
    await page.route(`${E2E_API_BASE_URL}/categories`, async (route, request) => {
      if (request.method() === "POST") {
        await route.fulfill({
          status: 422,
          contentType: "application/json",
          body: JSON.stringify({
            success: false,
            error: { code: "VALIDATION_FAILED", message: "Injected category create failure." }
          })
        });
        return;
      }
      await route.continue();
    });

    await page.getByTestId("categories-add").click();
    await page.getByTestId("categories-new-name").fill(`Fail Case ${randomSuffix()}`);
    await page.getByTestId("categories-save-new").click();
    await expect(page.getByTestId("categories-message")).toContainText("Injected category create failure.");
  });
});
