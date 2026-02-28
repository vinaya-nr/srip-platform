"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export const SUPPORTED_CURRENCIES = ["INR", "USD", "EUR", "GBP", "AED", "JPY", "CAD", "AUD", "SGD"] as const;
export type SupportedCurrency = (typeof SUPPORTED_CURRENCIES)[number];

type PreferencesState = {
  currency: SupportedCurrency;
  setCurrency: (currency: SupportedCurrency) => void;
};

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      currency: "INR",
      setCurrency: (currency) => set({ currency })
    }),
    {
      name: "srip-preferences"
    }
  )
);

