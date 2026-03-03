"use client";

import { create } from "zustand";

import { API_BASE } from "@/lib/config";
import type { TokenResponse, User } from "@/lib/types";

let inFlightRefresh: Promise<string | null> | null = null;

type AuthState = {
  accessToken: string | null;
  user: User | null;
  bootstrapped: boolean;
  setSession: (token: string, user: User) => void;
  clearSession: () => void;
  refreshSession: () => Promise<string | null>;
  bootstrapSession: () => Promise<void>;
};

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  bootstrapped: false,
  setSession: (token, user) => set({ accessToken: token, user }),
  clearSession: () => set({ accessToken: null, user: null }),
  refreshSession: async () => {
    if (inFlightRefresh) {
      return inFlightRefresh;
    }

    inFlightRefresh = (async () => {
      try {
        const response = await fetch(`${API_BASE}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include"
        });
        if (!response.ok) {
          set({ accessToken: null, user: null });
          return null;
        }
        const result = (await response.json()) as TokenResponse;
        set({ accessToken: result.access_token, user: result.user });
        return result.access_token;
      } catch {
        set({ accessToken: null, user: null });
        return null;
      } finally {
        inFlightRefresh = null;
      }
    })();

    return inFlightRefresh;
  },
  bootstrapSession: async () => {
    const token = await useAuthStore.getState().refreshSession();
    set((prev) => ({
      accessToken: token ?? null,
      user: token ? prev.user : null,
      bootstrapped: true
    }));
  }
}));
