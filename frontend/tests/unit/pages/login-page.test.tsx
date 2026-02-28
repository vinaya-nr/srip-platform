import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import LoginPage from "@/app/(public)/login/page";
import { useAuthStore } from "@/stores/auth-store";

const replaceMock = vi.fn();
vi.mock("next/navigation", async () => {
  const actual = await vi.importActual<typeof import("next/navigation")>("next/navigation");
  return {
    ...actual,
    useRouter: () => ({ replace: replaceMock }),
    usePathname: () => "/login"
  };
});

vi.mock("@/lib/api", () => ({
  login: vi.fn()
}));

import { login } from "@/lib/api";

describe("LoginPage", () => {
  it("submits valid credentials and routes to dashboard", async () => {
    vi.mocked(login).mockResolvedValue({
      access_token: "token-x",
      token_type: "bearer",
      expires_in: 900,
      user: { id: "u1", email: "test@example.com", shop_id: "s1" }
    });

    const user = userEvent.setup();
    render(<LoginPage />);
    await user.type(screen.getByTestId("login-email"), "test@example.com");
    await user.type(screen.getByTestId("login-password"), "Passw0rd!123");
    await user.click(screen.getByTestId("login-submit"));

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/dashboard");
      expect(useAuthStore.getState().accessToken).toBe("token-x");
    });
  });

  it("shows error when login request fails", async () => {
    vi.mocked(login).mockRejectedValue(new Error("Invalid credentials"));
    const user = userEvent.setup();
    render(<LoginPage />);
    await user.type(screen.getByTestId("login-email"), "bad@example.com");
    await user.type(screen.getByTestId("login-password"), "bad");
    await user.click(screen.getByTestId("login-submit"));
    await expect(screen.findByTestId("login-error")).resolves.toHaveTextContent("Invalid credentials");
  });

  it("shows fallback error when thrown value is not an Error", async () => {
    vi.mocked(login).mockRejectedValue("bad");
    const user = userEvent.setup();
    render(<LoginPage />);
    await user.type(screen.getByTestId("login-email"), "bad@example.com");
    await user.type(screen.getByTestId("login-password"), "bad");
    await user.click(screen.getByTestId("login-submit"));
    await expect(screen.findByTestId("login-error")).resolves.toHaveTextContent("Login failed");
  });
});
