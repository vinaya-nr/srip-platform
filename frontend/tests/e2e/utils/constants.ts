export const E2E_API_BASE_URL = process.env.E2E_API_BASE_URL ?? "http://localhost:8000/api/v1";
export const E2E_FRONTEND_BASE_URL = process.env.E2E_FRONTEND_URL ?? "http://localhost:3000";
export const E2E_DEFAULT_PASSWORD = process.env.E2E_PASSWORD ?? "Passw0rd!123";

export const AUTH_STATE_PATH = "tests/.auth/user.json";
export const CREDENTIALS_PATH = "tests/.auth/credentials.json";
