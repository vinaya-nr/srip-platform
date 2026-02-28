"use client";

import { useAuthStore } from "@/stores/auth-store";

export function useRequiredToken() {
  return useAuthStore((s) => s.accessToken);
}
