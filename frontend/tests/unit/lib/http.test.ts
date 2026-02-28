import { afterEach, describe, expect, it, vi } from "vitest";

const { refreshSessionMock } = vi.hoisted(() => ({
  refreshSessionMock: vi.fn()
}));

vi.mock("@/stores/auth-store", () => ({
  useAuthStore: {
    getState: () => ({
      refreshSession: refreshSessionMock
    })
  }
}));

import { apiRequest } from "@/lib/http";

const fetchMock = vi.fn();
vi.stubGlobal("fetch", fetchMock);

describe("apiRequest", () => {
  afterEach(() => {
    fetchMock.mockReset();
    refreshSessionMock.mockReset();
  });

  it("sends auth header and parses success payload", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ok: true })
    });

    const result = await apiRequest<{ ok: boolean }>("/health", { token: "abc123" });
    expect(result.ok).toBe(true);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/health"),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer abc123" })
      })
    );
  });

  it("returns undefined for 204 responses", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      status: 204
    });

    const result = await apiRequest<void>("/logout", { method: "POST" });
    expect(result).toBeUndefined();
  });

  it("throws backend error message when present", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({ error: { message: "Validation failed." } })
    });

    await expect(apiRequest("/categories")).rejects.toThrow("Validation failed.");
  });

  it("falls back to status message when error payload is not JSON", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => {
        throw new Error("non-json");
      }
    });

    await expect(apiRequest("/categories")).rejects.toThrow("Request failed (500)");
  });

  it("refreshes token and retries once on 401 for authenticated requests", async () => {
    fetchMock
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ error: { message: "Invalid token." } })
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ ok: true })
      });
    refreshSessionMock.mockResolvedValue("fresh-token");

    const result = await apiRequest<{ ok: boolean }>("/products", { token: "expired-token" });
    expect(result.ok).toBe(true);
    expect(refreshSessionMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      expect.stringContaining("/products"),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer fresh-token" })
      })
    );
  });

  it("does not retry when refresh returns null", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ error: { message: "Invalid token." } })
    });
    refreshSessionMock.mockResolvedValue(null);

    await expect(apiRequest("/products", { token: "expired-token" })).rejects.toThrow("Invalid token.");
    expect(refreshSessionMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("does not attempt refresh for /auth/refresh path", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ error: { message: "Refresh missing." } })
    });

    await expect(apiRequest("/auth/refresh", { token: "expired-token" })).rejects.toThrow("Refresh missing.");
    expect(refreshSessionMock).not.toHaveBeenCalled();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
