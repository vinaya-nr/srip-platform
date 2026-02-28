import { API_BASE } from "./config";
import type { ApiError } from "./types";
import { useAuthStore } from "@/stores/auth-store";

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  token?: string | null;
  body?: unknown;
};

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const makeRequest = (token: string | null | undefined) => {
    const headers: Record<string, string> = {
      "Content-Type": "application/json"
    };
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    return fetch(`${API_BASE}${path}`, {
      method: options.method ?? "GET",
      headers,
      credentials: "include",
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined
    });
  };

  let response = await makeRequest(options.token);
  if (response.status === 401 && options.token && path !== "/auth/refresh") {
    const refreshedToken = await useAuthStore.getState().refreshSession();
    if (refreshedToken) {
      response = await makeRequest(refreshedToken);
    }
  }

  if (!response.ok) {
    let payload: ApiError | undefined;
    try {
      payload = (await response.json()) as ApiError;
    } catch {
      payload = undefined;
    }
    const message = payload?.error?.message ?? `Request failed (${response.status})`;
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
