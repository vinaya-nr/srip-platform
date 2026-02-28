import { expect, test } from "@playwright/test";

import { LoginPage } from "./pom/login-page";
import { SripApiClient } from "./utils/api-client";
import { randomSuffix } from "./utils/auth-files";

test("notifications can be marked as read from UI action", async ({ page, request }) => {
  const api = new SripApiClient(request);
  const suffix = randomSuffix();
  const email = `notifications.ui.${suffix}@example.com`;
  const password = "Passw0rd!123";
  await api.register(email, password, `Notifications UI ${suffix}`);
  const login = await api.login(email, password);

  const notification = await api.createNotification(login.access_token, {
    event_type: "e2e_ui_notification",
    title: `UI Notification ${suffix}`,
    message: "Mark read from UI"
  });

  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login(email, password);
  await expect(page).toHaveURL(/\/dashboard$/);

  await page.goto("/notifications");
  await expect(page.getByTestId("notifications-table")).toContainText(notification.title);
  await page.getByTestId(`notifications-mark-read-${notification.id}`).click();
  await expect(page.getByTestId("notifications-message")).toContainText("Notification marked as read.");
  await expect(page.getByTestId("notifications-table")).toContainText("Read");
});
