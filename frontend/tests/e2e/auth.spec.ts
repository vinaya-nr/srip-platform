import { expect, test } from "@playwright/test";

import { LoginPage } from "./pom/login-page";
import { SripApiClient } from "./utils/api-client";
import { E2E_DEFAULT_PASSWORD } from "./utils/constants";
import { randomSuffix } from "./utils/auth-files";

test.describe("Auth flows", () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test("login success flow", async ({ page, request }) => {
    const suffix = randomSuffix();
    const email = `auth.success.${suffix}@example.com`;
    const password = E2E_DEFAULT_PASSWORD;
    const api = new SripApiClient(request);
    await api.register(email, password, `Auth Shop ${suffix}`);

    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login(email, password);

    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.getByTestId("dashboard-page")).toBeVisible();
  });

  test("login failure with invalid credentials", async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login("invalid@example.com", "InvalidPass123!");
    await loginPage.expectError();
    await expect(page).toHaveURL(/\/login$/);
  });

  test("session refresh handling on reload", async ({ page, request }) => {
    const suffix = randomSuffix();
    const email = `auth.refresh.${suffix}@example.com`;
    const password = E2E_DEFAULT_PASSWORD;
    const api = new SripApiClient(request);
    await api.register(email, password, `Refresh Shop ${suffix}`);

    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login(email, password);
    await expect(page).toHaveURL(/\/dashboard$/);

    await page.reload();
    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.getByTestId("dashboard-page")).toBeVisible();
  });

  test("logout flow", async ({ page, request }) => {
    const suffix = randomSuffix();
    const email = `auth.logout.${suffix}@example.com`;
    const password = E2E_DEFAULT_PASSWORD;
    const api = new SripApiClient(request);
    await api.register(email, password, `Logout Shop ${suffix}`);

    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login(email, password);
    await expect(page).toHaveURL(/\/dashboard$/);

    await page.getByTestId("nav-logout").click();
    await expect(page).toHaveURL(/\/login$/);

    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login$/);
  });
});
