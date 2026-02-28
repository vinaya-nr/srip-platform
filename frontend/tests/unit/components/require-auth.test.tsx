import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { RequireAuth } from "@/components/require-auth";
import { useAuthStore } from "@/stores/auth-store";

const replaceMock = vi.fn();
vi.mock("next/navigation", async () => {
  const actual = await vi.importActual<typeof import("next/navigation")>("next/navigation");
  return {
    ...actual,
    useRouter: () => ({ replace: replaceMock }),
    usePathname: () => "/dashboard"
  };
});

describe("RequireAuth", () => {
  it("shows restoring state before bootstrap", () => {
    useAuthStore.setState({ accessToken: null, user: null, bootstrapped: false });
    render(
      <RequireAuth>
        <div>Secret</div>
      </RequireAuth>
    );
    expect(screen.getByText("Restoring session...")).toBeInTheDocument();
  });

  it("renders children when token exists", () => {
    useAuthStore.setState({
      accessToken: "token",
      user: { id: "u", email: "a@b.com", shop_id: "s" },
      bootstrapped: true
    });
    render(
      <RequireAuth>
        <div>Secret</div>
      </RequireAuth>
    );
    expect(screen.getByText("Secret")).toBeInTheDocument();
  });

  it("redirects when bootstrapped without token", async () => {
    useAuthStore.setState({ accessToken: null, user: null, bootstrapped: true });
    render(
      <RequireAuth>
        <div>Secret</div>
      </RequireAuth>
    );
    expect(replaceMock).toHaveBeenCalledWith("/login");
  });
});
