import { E2E_API_BASE_URL } from "./constants";

function isLocalHost(hostname: string) {
  return hostname === "localhost" || hostname === "127.0.0.1";
}

export function assertSafeE2EApiBaseUrl() {
  if (process.env.ALLOW_E2E_NONLOCAL_API === "true") {
    return;
  }

  const parsed = new URL(E2E_API_BASE_URL);
  if (!isLocalHost(parsed.hostname)) {
    throw new Error(
      `Unsafe E2E API target: ${E2E_API_BASE_URL}. Set E2E_API_BASE_URL to localhost/127.0.0.1, or explicitly set ALLOW_E2E_NONLOCAL_API=true.`
    );
  }
}

