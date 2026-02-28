import { expect, test } from "@playwright/test";

import { SripApiClient } from "./utils/api-client";
import { randomSuffix } from "./utils/auth-files";
import { ensureUiAuthenticated } from "./utils/ensure-ui-auth";
import { getSetupUserToken } from "./utils/session";

test("categories flow: create, list, edit, delete", async ({ page, request }) => {
  const api = new SripApiClient(request);
  const token = await getSetupUserToken(request);
  const suffix = randomSuffix();

  const created = await api.createCategory(token, `Category ${suffix}`);
  await ensureUiAuthenticated(page);
  await page.goto("/categories");
  await expect(page.getByTestId("categories-table")).toContainText(created.name);

  const updatedName = `Category Updated ${suffix}`;
  await api.updateCategory(token, created.id, updatedName);
  await page.reload();
  await expect(page.getByTestId("categories-table")).toContainText(updatedName);

  await api.deleteCategory(token, created.id);
  await page.reload();
  await expect(page.getByTestId("categories-table")).not.toContainText(updatedName);
});
