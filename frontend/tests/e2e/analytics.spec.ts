import { expect, test } from "@playwright/test";

import { SripApiClient } from "./utils/api-client";
import { randomSuffix } from "./utils/auth-files";
import { ensureUiAuthenticated } from "./utils/ensure-ui-auth";
import { getSetupUserToken } from "./utils/session";

test("insights flow: page loads and data-log snapshots render", async ({ page, request }) => {
  const api = new SripApiClient(request);
  const token = await getSetupUserToken(request);
  const suffix = randomSuffix();

  await api.createSnapshot(token, {
    snapshot_type: "sale_event",
    payload: {
      sale_number: `E2E-SALE-${suffix}`,
      total_amount: "22.00",
      items: [{ product_id: `p-${suffix}`, quantity: 1 }]
    }
  });

  await expect
    .poll(
      async () => {
        const snapshots = await api.listSnapshots(token);
        return snapshots.some(
          (snapshot) =>
            snapshot.snapshot_type === "sale_event" &&
            String(snapshot.payload?.sale_number ?? "").includes(`E2E-SALE-${suffix}`)
        );
      },
      { timeout: 60_000, intervals: [1_000, 2_000, 5_000] }
    )
    .toBeTruthy();

  await ensureUiAuthenticated(page);
  await page.goto("/analytics");
  const redirectedToLogin = await page
    .getByRole("heading", { name: "Sign in" })
    .isVisible({ timeout: 2_000 })
    .catch(() => false);
  if (redirectedToLogin) {
    await ensureUiAuthenticated(page);
    await page.goto("/analytics");
  }
  await expect(page).toHaveURL(/\/analytics$/);
  await expect(page.getByTestId("analytics-page")).toBeVisible();
  await expect(page.getByTestId("insights-monthly-card")).toBeVisible();
  await page.getByTestId("data-log-tab").click();
  await expect(page.getByTestId("analytics-snapshot-card").first()).toBeVisible();
});
