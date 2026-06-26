"use client";

import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";
import { postAuthJson } from "@/lib/auth-fetch";

const FRIENDLY: Record<number, string> = {
  409: "That email is already registered. Try signing in instead.",
  422: "Please double-check your email and password — they didn't look valid.",
  429: "Too many sign-up attempts. Wait a minute and try again.",
};

export default function SignUpPage() {
  const [name, setName] = useState("");
  const [org, setOrg] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [conflict, setConflict] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setConflict(false);
    try {
      const data = await postAuthJson<{
        user_id: string;
        verification_url?: string;
      }>("/auth/sign-up", { name, org, email, password });
      if (data.verification_url) {
        toast.success("Account created — opening the verification link.");
        window.location.href = data.verification_url;
      } else {
        toast.success("Account created — check your email to verify.");
        window.location.href = "/auth/verify?sent=1";
      }
    } catch (err) {
      const e = err as { status?: number; detail?: string };
      if (e.status === 409) setConflict(true);
      const message =
        (e.status && FRIENDLY[e.status]) || e.detail || "Sign-up failed. Try again.";
      toast.error(message);
    } finally {
      setBusy(false);
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
        Create your insurer workspace
      </h1>
      <p className="mt-1 text-sm text-[#8B95A5]">
        Free for the first 100 filed claims. No card required.
      </p>

      {conflict ? (
        <div className="mt-4 rounded-xl border border-amber-400/40 bg-amber-500/10 p-3 text-sm text-amber-100">
          That email is already registered.{" "}
          <Link href="/auth/sign-in" className="underline">
            Sign in
          </Link>{" "}
          or{" "}
          <Link href="/auth/reset" className="underline">
            reset your password
          </Link>
          .
        </div>
      ) : null}

      <form onSubmit={onSubmit} className="mt-4 flex flex-col gap-3">
        <label className="field">
          <span className="field-label">Name</span>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter name"
            className="field-input"
            autoComplete="name"
          />
        </label>

        <label className="field">
          <span className="field-label">Organization</span>
          <input
            value={org}
            onChange={(e) => setOrg(e.target.value)}
            placeholder="Enter organization"
            className="field-input"
            autoComplete="organization"
          />
        </label>

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
          <span className="field-label">Password</span>
          <input
            required
            type="password"
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter password"
            className="field-input"
            autoComplete="new-password"
          />
        </label>

        <button
          disabled={busy}
          type="submit"
          className="btn-gradient w-full h-[46px] mt-2 text-sm"
        >
          {busy ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="mt-4 text-center text-[13px] text-[#8B95A5]">
        Already have an account?{" "}
        <Link href="/auth/sign-in" className="text-[#BDF272] hover:underline">
          Sign in
        </Link>
      </p>
      <p className="mt-2 text-center text-[11px] text-[#687386]">
        By creating an account you agree to our{" "}
        <Link href="/legal/terms" className="underline">
          Terms
        </Link>{" "}
        and{" "}
        <Link href="/legal/privacy" className="underline">
          Privacy Policy
        </Link>
        . We hash with Argon2id.
      </p>
    </div>
  );
}
