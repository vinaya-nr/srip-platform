import { expect, Page } from "@playwright/test";

import { LoginPage } from "../pom/login-page";
import { loadCredentials } from "./auth-files";

export async function ensureUiAuthenticated(page: Page) {
  const credentials = loadCredentials();
  const loginPage = new LoginPage(page);

  await loginPage.goto();
  const needsLogin = await page
    .getByRole("heading", { name: "Sign in" })
    .isVisible({ timeout: 3_000 })
    .catch(() => false);

  if (needsLogin) {
    await loginPage.login(credentials.email, credentials.password);
  } else {
    await page.goto("/dashboard");
  }

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByTestId("dashboard-page")).toBeVisible();
}
