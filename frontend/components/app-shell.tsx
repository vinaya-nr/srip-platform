"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/products", label: "Products" },
  { href: "/categories", label: "Categories" },
  { href: "/inventory", label: "Inventory" },
  { href: "/sales", label: "Sales" },
  { href: "/analytics", label: "Insights" },
  { href: "/notifications", label: "Notifications" },
  { href: "/settings", label: "Settings" }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();

  return (
    <div className="row" style={{ minHeight: "100vh", alignItems: "stretch", gap: 0 }}>
      <aside className="card" style={{ width: 230, borderRadius: 0 }}>
        <h3 style={{ fontSize: 28, margin: "4px 0 12px", fontWeight: 800 }}>SRIP</h3>
        <div className="col">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              data-testid={`nav-${item.label.toLowerCase()}`}
              className="card"
              style={{
                padding: "8px 10px",
                background: path?.startsWith(item.href) ? "#e8f0fe" : "#fff"
              }}
            >
              {item.label}
            </Link>
          ))}
          <Link href="/logout" data-testid="nav-logout" className="card" style={{ marginTop: 10, padding: "8px 10px" }}>
            Logout
          </Link>
        </div>
      </aside>
      <main style={{ flex: 1 }}>{children}</main>
    </div>
  );
}
