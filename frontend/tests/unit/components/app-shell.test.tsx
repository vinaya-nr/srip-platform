import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AppShell } from "@/components/app-shell";

vi.mock("next/navigation", async () => {
  const actual = await vi.importActual<typeof import("next/navigation")>("next/navigation");
  return {
    ...actual,
    usePathname: () => "/products"
  };
});

describe("AppShell", () => {
  it("renders nav links and children", () => {
    render(
      <AppShell>
        <div>Page Body</div>
      </AppShell>
    );

    expect(screen.getByTestId("nav-dashboard")).toBeInTheDocument();
    expect(screen.getByTestId("nav-products")).toBeInTheDocument();
    expect(screen.getByTestId("nav-insights")).toBeInTheDocument();
    expect(screen.getByTestId("nav-logout")).toBeInTheDocument();
    expect(screen.getByText("Page Body")).toBeInTheDocument();
  });
});
