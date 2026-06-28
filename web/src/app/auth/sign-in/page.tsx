"use client";

import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";
import { postAuthJson } from "@/lib/auth-fetch";
import { AuthField } from "@/components/auth/auth-field";
import { Button } from "@/components/ui/button";

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
        (e.status && FRIENDLY[e.status]) ||
        e.detail ||
        "Sign-in failed. Try again.";
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
      const data = await postAuthJson<{ consume_url?: string }>(
        "/auth/magic-link",
        { email }
      );
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
    <div>
      <h1 className="text-3xl font-bold tracking-tight text-foreground">
        Welcome back
      </h1>
      <p className="mt-2 text-[15px] text-muted-foreground">
        Sign in to triage claims and manage your workspace.
      </p>

      <form onSubmit={onSubmit} className="mt-7 flex flex-col gap-4">
        <AuthField
          label="Email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@insurer.org"
          autoComplete="email"
        />
        <AuthField
          label="Password"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          autoComplete="current-password"
          hint={
            <Link
              href="/auth/reset"
              className="text-xs font-medium text-primary hover:underline"
            >
              Forgot?
            </Link>
          }
        />

        <Button
          type="submit"
          disabled={busy}
          className="mt-1 h-11 w-full text-[15px]"
        >
          {busy ? "Signing in…" : "Sign in"}
        </Button>

        <Button
          type="button"
          variant="outline"
          disabled={magicBusy}
          onClick={sendMagicLink}
          className="h-11 w-full text-[15px]"
        >
          {magicBusy ? "Sending magic link…" : "Email me a magic link"}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        New here?{" "}
        <Link
          href="/auth/sign-up"
          className="font-medium text-primary hover:underline"
        >
          Create an account
        </Link>
      </p>
    </div>
  );
}
