"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";

import { login } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";

export default function LoginPage() {
  const router = useRouter();
  const setSession = useAuthStore((s) => s.setSession);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setPending(true);
    setError(null);
    try {
      const res = await login({ email, password });
      setSession(res.access_token, res.user);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="login-layout" data-testid="login-page">
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
          <h1 className="login-title">Sign in</h1>
          <p className="login-subtitle">Smart Retail Intelligence Platform for modern shop operations.</p>

          <div className="card col login-card">
            <form onSubmit={onSubmit} className="col" data-testid="login-form">
              <label>Email</label>
              <input data-testid="login-email" value={email} onChange={(e) => setEmail(e.target.value)} required type="email" />
              <label>Password</label>
              <input data-testid="login-password" value={password} onChange={(e) => setPassword(e.target.value)} required type="password" />
              {error && <div className="danger" data-testid="login-error">{error}</div>}
              <button className="btn" data-testid="login-submit" disabled={pending} type="submit">
                {pending ? "Signing in..." : "Sign in"}
              </button>
            </form>
            <p className="muted">
              New shop? <Link href="/register">Create account</Link>
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
