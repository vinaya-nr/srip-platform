import { afterEach, describe, expect, it, vi } from "vitest";

import { useAuthStore } from "@/stores/auth-store";

const fetchMock = vi.fn();
vi.stubGlobal("fetch", fetchMock);

describe("auth store", () => {
  afterEach(() => {
    useAuthStore.getState().clearSession();
    useAuthStore.setState({ bootstrapped: false, user: null, accessToken: null });
    fetchMock.mockReset();
  });

  it("sets and clears session", () => {
    useAuthStore.getState().setSession("token-1", { id: "u1", email: "u@example.com", shop_id: "s1" });
    expect(useAuthStore.getState().accessToken).toBe("token-1");
    expect(useAuthStore.getState().user?.email).toBe("u@example.com");

    useAuthStore.getState().clearSession();
    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
  });

  it("bootstraps session on refresh success", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        access_token: "fresh-token",
        token_type: "bearer",
        expires_in: 900,
        user: { id: "u2", email: "fresh@example.com", shop_id: "shop2" }
      })
    });

    await useAuthStore.getState().bootstrapSession();
    expect(useAuthStore.getState().bootstrapped).toBe(true);
    expect(useAuthStore.getState().accessToken).toBe("fresh-token");
  });

  it("clears session when refresh fails", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({})
    });

    await useAuthStore.getState().bootstrapSession();
    expect(useAuthStore.getState().bootstrapped).toBe(true);
    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
  });

  it("clears session when refresh throws network error", async () => {
    fetchMock.mockRejectedValue(new Error("network down"));
    await useAuthStore.getState().bootstrapSession();
    expect(useAuthStore.getState().bootstrapped).toBe(true);
    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
  });
});
