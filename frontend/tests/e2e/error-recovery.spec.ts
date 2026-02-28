import { expect, test } from "@playwright/test";

import { E2E_API_BASE_URL } from "./utils/constants";
import { ensureUiAuthenticated } from "./utils/ensure-ui-auth";

test("products page recovers after transient backend error", async ({ page }) => {
  await ensureUiAuthenticated(page);
  let failRequests = true;

  await page.route(`${E2E_API_BASE_URL}/products*`, async (route) => {
    if (failRequests) {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({
          success: false,
          error: { code: "INTERNAL_SERVER_ERROR", message: "Temporary products outage." }
        })
      });
      return;
    }
    await route.continue();
  });

  await page.goto("/products");
  await expect(page.locator(".danger")).toContainText("Temporary products outage.");

  failRequests = false;
  await page.reload();
  await expect(page.getByTestId("products-page")).toBeVisible();
  await expect(page.getByTestId("products-table")).toBeVisible();
});
