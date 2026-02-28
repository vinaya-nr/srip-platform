import { test } from "@playwright/test";

import { DashboardPage } from "./pom/dashboard-page";
import { ensureUiAuthenticated } from "./utils/ensure-ui-auth";

test("dashboard loads after auth and summary cards are visible", async ({ page }) => {
  await ensureUiAuthenticated(page);
  const dashboard = new DashboardPage(page);
  await dashboard.goto();
  await dashboard.expectSummaryCards();
});
