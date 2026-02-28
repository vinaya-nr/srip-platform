import { expect, test } from "@playwright/test";

import { LoginPage } from "./pom/login-page";
import { SripApiClient } from "./utils/api-client";
import { randomSuffix } from "./utils/auth-files";

test("settings displays current user information", async ({ page, request }) => {
  const api = new SripApiClient(request);
  const suffix = randomSuffix();
  const email = `settings.${suffix}@example.com`;
  const password = "Passw0rd!123";
  await api.register(email, password, `Settings Shop ${suffix}`);

  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login(email, password);
  await expect(page).toHaveURL(/\/dashboard$/);

  await page.goto("/settings");
  await expect(page.getByTestId("settings-page")).toBeVisible();
  await expect(page.getByTestId("settings-user-email")).toContainText(email);
});
