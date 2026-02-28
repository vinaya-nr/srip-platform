import { expect, test } from "@playwright/test";

import { SripApiClient } from "./utils/api-client";
import { randomSuffix } from "./utils/auth-files";

test.describe("Register flows", () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test("register success redirects to login", async ({ page }) => {
    const suffix = randomSuffix();
    await page.goto("/register");
    await page.getByTestId("register-shop-name").fill(`Register Shop ${suffix}`);
    await page.getByTestId("register-email").fill(`register.success.${suffix}@example.com`);
    await page.getByTestId("register-password").fill("Passw0rd!123");
    await page.getByTestId("register-submit").click();
    await expect(page).toHaveURL(/\/login$/);
  });

  test("register duplicate email shows error", async ({ page, request }) => {
    const api = new SripApiClient(request);
    const suffix = randomSuffix();
    const email = `register.dup.${suffix}@example.com`;
    const password = "Passw0rd!123";
    await api.register(email, password, `Dup Shop ${suffix}`);

    await page.goto("/register");
    await page.getByTestId("register-shop-name").fill(`Dup Shop ${suffix}`);
    await page.getByTestId("register-email").fill(email);
    await page.getByTestId("register-password").fill(password);
    await page.getByTestId("register-submit").click();
    await expect(page.getByTestId("register-error")).toBeVisible();
  });
});
