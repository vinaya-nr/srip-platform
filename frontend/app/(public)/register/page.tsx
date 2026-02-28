"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";

import { register } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [shopName, setShopName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setPending(true);
    setError(null);
    try {
      await register({ email, password, shop_name: shopName });
      router.replace("/login");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="login-layout" data-testid="register-page">
      <section className="login-panel">
        <div className="login-logo-wrap">
          <Image
            src="/assets/srip_logo.png"
            alt="SRIP logo"
            width={320}
            height={140}
            className="login-logo-image"
            priority
          />
        </div>

        <div className="login-panel-content">
          <h1 className="login-title">Create account</h1>
          <p className="login-subtitle">Set up your shop to start tracking sales, inventory, and insights.</p>

          <div className="card col login-card">
            <form onSubmit={onSubmit} className="col" data-testid="register-form">
              <label>Shop name</label>
              <input data-testid="register-shop-name" value={shopName} onChange={(e) => setShopName(e.target.value)} required />
              <label>Email</label>
              <input data-testid="register-email" value={email} onChange={(e) => setEmail(e.target.value)} required type="email" />
              <label>Password</label>
              <input data-testid="register-password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} type="password" />
              {error && <div className="danger" data-testid="register-error">{error}</div>}
              <button className="btn" data-testid="register-submit" disabled={pending} type="submit">
                {pending ? "Creating..." : "Create account"}
              </button>
            </form>
            <p className="muted">
              Already have an account? <Link href="/login">Sign in</Link>
            </p>
          </div>
        </div>
      </section>

      <aside className="login-visual" aria-hidden="true">
        <div className="login-visual-card">
          <Image
            src="/assets/srip_right_img.png"
            alt="SRIP retail analytics visual"
            width={1200}
            height={900}
            className="login-visual-image"
            priority
          />
        </div>
      </aside>
    </main>
  );
}
