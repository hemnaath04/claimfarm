"use client";

import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";
import { postAuthJson } from "@/lib/auth-fetch";

const FRIENDLY: Record<number, string> = {
  401: "Email or password didn't match. Try again or reset your password.",
  403: "Your account is suspended. Contact support@claimfarm.dev.",
  429: "Too many attempts. Wait a minute, then try again.",
};

export default function SignInPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [magicBusy, setMagicBusy] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await postAuthJson("/auth/sign-in", { email, password });
      toast.success("Signed in — redirecting…");
      window.location.href = "/dashboard";
    } catch (err) {
      const e = err as { status?: number; detail?: string };
      const message =
        (e.status && FRIENDLY[e.status]) || e.detail || "Sign-in failed. Try again.";
      toast.error(message);
    } finally {
      setBusy(false);
    }
  };

  const sendMagicLink = async () => {
    if (!email) {
      toast.error("Enter your email above first.");
      return;
    }
    setMagicBusy(true);
    try {
      const data = await postAuthJson<{ consume_url?: string }>("/auth/magic-link", {
        email,
      });
      if (data.consume_url) {
        toast.success("Magic link ready — opening it now.");
        window.location.href = data.consume_url;
      } else {
        toast.success("Magic link sent — check your inbox.");
      }
    } catch (err) {
      const e = err as { detail?: string };
      toast.error(e.detail ?? "Couldn't send magic link.");
    } finally {
      setMagicBusy(false);
    }
  };

  return (
    <div className="glass-card p-5">
      <div className="flex items-center gap-2.5">
        <span className="brand-mark" aria-hidden />
        <span className="text-[22px] font-bold tracking-tight text-[#F8FAFC]">
          claimfarm
        </span>
      </div>

      <h1 className="mt-4 text-[25px] font-bold leading-8 text-[#F8FAFC]">
        Welcome back
      </h1>
      <p className="mt-1 text-sm text-[#8B95A5]">
        Sign in to triage claims and manage your workspace.
      </p>

      <form onSubmit={onSubmit} className="mt-4 flex flex-col gap-3">
        <label className="field">
          <span className="field-label">Email</span>
          <input
            required
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter email"
            className="field-input"
            autoComplete="email"
          />
        </label>

        <label className="field">
          <span className="field-label flex items-center justify-between">
            <span>Password</span>
            <Link
              href="/auth/reset"
              className="normal-case tracking-normal text-[11px] text-[#BDF272] hover:underline"
            >
              Forgot?
            </Link>
          </span>
          <input
            required
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter password"
            className="field-input"
            autoComplete="current-password"
          />
        </label>

        <button
          disabled={busy}
          type="submit"
          className="btn-gradient w-full h-[46px] mt-2 text-sm"
        >
          {busy ? "Signing in…" : "Sign in"}
        </button>

        <button
          type="button"
          disabled={magicBusy}
          onClick={sendMagicLink}
          className="btn-ghost-translucent w-full h-[46px] text-sm font-semibold"
        >
          {magicBusy ? "Sending magic link…" : "Email magic link"}
        </button>
      </form>

      <p className="mt-4 text-center text-[13px] text-[#8B95A5]">
        New here?{" "}
        <Link href="/auth/sign-up" className="text-[#BDF272] hover:underline">
          Create an account
        </Link>
      </p>
    </div>
  );
}
