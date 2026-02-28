"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getMyProfile } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { SUPPORTED_CURRENCIES, type SupportedCurrency, usePreferencesStore } from "@/stores/preferences-store";

const CURRENCY_LABELS: Record<SupportedCurrency, string> = {
  INR: "INR - Indian Rupee",
  USD: "USD - US Dollar",
  EUR: "EUR - Euro",
  GBP: "GBP - British Pound",
  AED: "AED - UAE Dirham",
  JPY: "JPY - Japanese Yen",
  CAD: "CAD - Canadian Dollar",
  AUD: "AUD - Australian Dollar",
  SGD: "SGD - Singapore Dollar"
};

export default function SettingsPage() {
  const token = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const selectedCurrency = usePreferencesStore((s) => s.currency);
  const setCurrency = usePreferencesStore((s) => s.setCurrency);
  const [pendingCurrency, setPendingCurrency] = useState<SupportedCurrency>(selectedCurrency);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    setPendingCurrency(selectedCurrency);
  }, [selectedCurrency]);

  const profileQuery = useQuery({
    queryKey: ["users", "me"],
    queryFn: () => getMyProfile(token as string),
    enabled: Boolean(token)
  });

  const shopName = profileQuery.data?.shop?.name ?? "-";

  return (
    <main className="container col" data-testid="settings-page">
      <h1>Settings</h1>
      <div className="card col">
        <div data-testid="settings-user-email"><strong>User:</strong> {user?.email ?? "-"}</div>
        <div data-testid="settings-shop-name"><strong>Shop Name:</strong> {shopName}</div>
        <p className="muted">
          Shop profile update and password change are planned for Phase 2 when corresponding backend endpoints are enabled.
        </p>
      </div>

      <div className="card col" data-testid="settings-regional-preferences">
        <h2 style={{ margin: 0 }}>Regional Preferences</h2>
        <label className="col" style={{ gap: 6, maxWidth: 320 }}>
          <span><strong>Currency</strong></span>
          <select
            data-testid="settings-currency-select"
            value={pendingCurrency}
            onChange={(e) => {
              setPendingCurrency(e.target.value as SupportedCurrency);
              setSaveMessage(null);
            }}
          >
            {SUPPORTED_CURRENCIES.map((currency) => (
              <option key={currency} value={currency}>
                {CURRENCY_LABELS[currency]}
              </option>
            ))}
          </select>
        </label>
        <div className="row" style={{ alignItems: "center" }}>
          <button
            className="btn"
            data-testid="settings-currency-save"
            type="button"
            onClick={() => {
              setCurrency(pendingCurrency);
              setSaveMessage(`Currency updated to ${pendingCurrency}.`);
            }}
          >
            Save Currency
          </button>
          {saveMessage && (
            <span className="success" data-testid="settings-currency-message">
              {saveMessage}
            </span>
          )}
        </div>
      </div>
    </main>
  );
}
