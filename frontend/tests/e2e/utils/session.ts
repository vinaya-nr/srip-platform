import { APIRequestContext } from "@playwright/test";

import { SripApiClient } from "./api-client";
import { loadCredentials } from "./auth-files";

export async function getSetupUserToken(request: APIRequestContext): Promise<string> {
  const credentials = loadCredentials();
  const api = new SripApiClient(request);
  const login = await api.login(credentials.email, credentials.password);
  return login.access_token;
}
