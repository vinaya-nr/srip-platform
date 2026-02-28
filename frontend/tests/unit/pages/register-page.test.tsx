import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import RegisterPage from "@/app/(public)/register/page";

const replaceMock = vi.fn();
vi.mock("next/navigation", async () => {
  const actual = await vi.importActual<typeof import("next/navigation")>("next/navigation");
  return {
    ...actual,
    useRouter: () => ({ replace: replaceMock }),
    usePathname: () => "/register"
  };
});

vi.mock("@/lib/api", () => ({
  register: vi.fn()
}));

import { register } from "@/lib/api";

describe("RegisterPage", () => {
  it("submits form and routes to login", async () => {
    vi.mocked(register).mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<RegisterPage />);

    await user.type(screen.getByTestId("register-shop-name"), "Shop 1");
    await user.type(screen.getByTestId("register-email"), "new@example.com");
    await user.type(screen.getByTestId("register-password"), "Passw0rd!123");
    await user.click(screen.getByTestId("register-submit"));

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/login");
    });
  });

  it("shows error when registration fails", async () => {
    vi.mocked(register).mockRejectedValue(new Error("User already exists"));
    const user = userEvent.setup();
    render(<RegisterPage />);

    await user.type(screen.getByTestId("register-shop-name"), "Shop 2");
    await user.type(screen.getByTestId("register-email"), "dup@example.com");
    await user.type(screen.getByTestId("register-password"), "Passw0rd!123");
    await user.click(screen.getByTestId("register-submit"));

    await expect(screen.findByTestId("register-error")).resolves.toHaveTextContent("User already exists");
  });

  it("shows fallback error when thrown value is not an Error", async () => {
    vi.mocked(register).mockRejectedValue("bad");
    const user = userEvent.setup();
    render(<RegisterPage />);

    await user.type(screen.getByTestId("register-shop-name"), "Shop 3");
    await user.type(screen.getByTestId("register-email"), "bad@example.com");
    await user.type(screen.getByTestId("register-password"), "Passw0rd!123");
    await user.click(screen.getByTestId("register-submit"));

    await expect(screen.findByTestId("register-error")).resolves.toHaveTextContent("Registration failed");
  });
});
