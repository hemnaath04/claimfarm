"use client";

import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";
import { postAuthJson } from "@/lib/auth-fetch";

export default function ResetPage() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [devLink, setDevLink] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      const data = await postAuthJson<{ reset_url?: string }>("/auth/reset", {
        email,
      });
      setSent(true);
      if (data.reset_url) {
        setDevLink(data.reset_url);
        toast.success("Reset link ready below (email transport not configured).");
      } else {
        toast.success("If an account exists for that email, a reset link is on its way.");
      }
    } catch (err) {
      const e = err as { detail?: string };
      toast.error(e.detail ?? "Could not send reset email. Try again.");
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

      {sent ? (
        <>
          <h1 className="mt-4 text-[25px] font-bold leading-8 text-[#F8FAFC]">
            Check your inbox
          </h1>
          <p className="mt-1 text-sm text-[#8B95A5]">
            If an account exists for{" "}
            <span className="text-[#F8FAFC]">{email}</span>, we just sent it a
            password-reset link. It expires in 1 hour.
          </p>
          {devLink ? (
            <div className="mt-4 rounded-xl border border-[#BDF272]/30 bg-[#BDF272]/5 p-3 text-[13px]">
              <div className="mb-1 font-medium text-[#BDF272]">
                Dev mode — email transport not configured
              </div>
              <a
                href={devLink}
                className="font-mono text-[12px] text-[#BDF272] underline break-all"
              >
                {devLink}
              </a>
            </div>
          ) : null}
          <Link
            href="/auth/sign-in"
            className="btn-ghost-translucent w-full h-[46px] mt-4 text-sm font-semibold inline-flex items-center justify-center"
          >
            Back to sign in
          </Link>
        </>
      ) : (
        <>
          <h1 className="mt-4 text-[25px] font-bold leading-8 text-[#F8FAFC]">
            Reset your password
          </h1>
          <p className="mt-1 text-sm text-[#8B95A5]">
            We&apos;ll email you a link to set a new one.
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
            <button
              disabled={busy}
              type="submit"
              className="btn-gradient w-full h-[46px] mt-2 text-sm"
            >
              {busy ? "Sending…" : "Send reset link"}
            </button>
          </form>

          <p className="mt-4 text-center text-[13px] text-[#8B95A5]">
            Remembered it?{" "}
            <Link href="/auth/sign-in" className="text-[#BDF272] hover:underline">
              Back to sign in
            </Link>
          </p>
        </>
      )}
    </div>
  );
}
