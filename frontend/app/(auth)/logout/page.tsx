"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { logout } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";

export default function LogoutPage() {
  const router = useRouter();
  const token = useAuthStore((s) => s.accessToken);
  const clear = useAuthStore((s) => s.clearSession);

  useEffect(() => {
    void (async () => {
      try {
        await logout(token);
      } finally {
        clear();
        router.replace("/login");
      }
    })();
  }, [clear, router, token]);

  return <div className="container">Signing out...</div>;
}
