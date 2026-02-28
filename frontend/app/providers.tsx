"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { QueryClientProvider } from "@tanstack/react-query";

import { queryClient } from "@/lib/query-client";
import { useAuthStore } from "@/stores/auth-store";

const PUBLIC_ROUTES = new Set(["/login", "/register"]);

export function Providers({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const bootstrap = useAuthStore((s) => s.bootstrapSession);

  useEffect(() => {
    if (!pathname || PUBLIC_ROUTES.has(pathname)) return;
    void bootstrap();
  }, [bootstrap, pathname]);

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
