import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import SettingsPage from "@/app/(protected)/settings/page";
import { getMyProfile } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { usePreferencesStore } from "@/stores/preferences-store";

vi.mock("@/lib/api", () => ({
  getMyProfile: vi.fn(async () => ({
    user: {
      id: "u1",
      email: "settings@example.com",
      shop_id: "shop-99",
      is_active: true,
      created_at: new Date().toISOString()
    },
    shop: {
      id: "shop-99",
      name: "SRIP Demo Shop",
      created_at: new Date().toISOString()
    }
  }))
}));

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <SettingsPage />
    </QueryClientProvider>
  );
}

describe("SettingsPage", () => {
  beforeEach(() => {
    useAuthStore.setState({
      accessToken: "tok",
      user: { id: "u1", email: "settings@example.com", shop_id: "shop-99" },
      bootstrapped: true
    });
    usePreferencesStore.setState({ currency: "INR" });
  });

  it("renders current user and shop name", async () => {
    renderPage();

    expect(screen.getByTestId("settings-user-email")).toHaveTextContent("settings@example.com");
    await waitFor(() => {
      expect(screen.getByTestId("settings-shop-name")).toHaveTextContent("SRIP Demo Shop");
    });
  });

  it("saves selected currency preference", async () => {
    const user = userEvent.setup();
    renderPage();

    const select = screen.getByTestId("settings-currency-select");
    await user.selectOptions(select, "USD");
    await user.click(screen.getByTestId("settings-currency-save"));

    expect(screen.getByTestId("settings-currency-message")).toHaveTextContent("Currency updated to USD.");
    expect(usePreferencesStore.getState().currency).toBe("USD");
  });

  it("shows fallback shop name when profile has no shop", async () => {
    vi.mocked(getMyProfile).mockResolvedValueOnce({
      user: {
        id: "u1",
        email: "settings@example.com",
        shop_id: "shop-99",
        is_active: true,
        created_at: new Date().toISOString()
      },
      shop: undefined as unknown as { id: string; name: string; created_at: string }
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId("settings-shop-name")).toHaveTextContent("-");
    });
  });

  it("shows fallback user email when user is not present in auth store", async () => {
    useAuthStore.setState({
      accessToken: "tok",
      user: null,
      bootstrapped: true
    });

    renderPage();

    expect(screen.getByTestId("settings-user-email")).toHaveTextContent("-");
  });
});
