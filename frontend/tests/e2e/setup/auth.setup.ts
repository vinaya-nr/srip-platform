import path from "node:path";

import { expect, test } from "@playwright/test";

import { AUTH_STATE_PATH, E2E_DEFAULT_PASSWORD } from "../utils/constants";
import { SripApiClient } from "../utils/api-client";
import { randomSuffix, saveCredentials } from "../utils/auth-files";
import { assertSafeE2EApiBaseUrl } from "../utils/safety";

test("bootstrap authenticated storage state", async ({ request }) => {
  assertSafeE2EApiBaseUrl();
  const api = new SripApiClient(request);
  const suffix = randomSuffix();
  const email = `e2e.${suffix}@example.com`;
  const password = E2E_DEFAULT_PASSWORD;
  const shopName = `E2E Shop ${suffix}`;

  await api.register(email, password, shopName);
  const login = await api.login(email, password);
  expect(login.access_token).toBeTruthy();

  saveCredentials({ email, password });
  await request.storageState({ path: path.join(process.cwd(), AUTH_STATE_PATH) });
});
