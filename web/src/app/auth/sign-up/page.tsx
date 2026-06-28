"use client";

import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";
import { postAuthJson } from "@/lib/auth-fetch";
import { AuthField } from "@/components/auth/auth-field";
import { Button } from "@/components/ui/button";

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
        (e.status && FRIENDLY[e.status]) ||
        e.detail ||
        "Sign-up failed. Try again.";
      toast.error(message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold tracking-tight text-foreground">
        Create your insurer workspace
      </h1>
      <p className="mt-2 text-[15px] text-muted-foreground">
        Free for the first 100 filed claims. No card required.
      </p>

      {conflict ? (
        <div
          role="alert"
          className="mt-5 rounded-lg border border-harvest-deep/40 bg-harvest/15 p-3 text-sm text-foreground"
        >
          That email is already registered.{" "}
          <Link href="/auth/sign-in" className="font-medium underline">
            Sign in
          </Link>{" "}
          or{" "}
          <Link href="/auth/reset" className="font-medium underline">
            reset your password
          </Link>
          .
        </div>
      ) : null}

      <form onSubmit={onSubmit} className="mt-7 flex flex-col gap-4">
        <AuthField
          label="Name"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Your full name"
          autoComplete="name"
        />
        <AuthField
          label="Organisation"
          value={org}
          onChange={(e) => setOrg(e.target.value)}
          placeholder="Insurer, NGO, or co-op"
          autoComplete="organization"
        />
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
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="At least 8 characters"
          autoComplete="new-password"
        />

        <Button
          type="submit"
          disabled={busy}
          className="mt-1 h-11 w-full text-[15px]"
        >
          {busy ? "Creating workspace…" : "Create free workspace"}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link
          href="/auth/sign-in"
          className="font-medium text-primary hover:underline"
        >
          Sign in
        </Link>
      </p>
      <p className="mt-3 text-center text-xs text-muted-foreground">
        By creating an account you agree to our{" "}
        <Link href="/legal/terms" className="underline">
          Terms
        </Link>{" "}
        and{" "}
        <Link href="/legal/privacy" className="underline">
          Privacy Policy
        </Link>
        . Passwords are hashed with Argon2id.
      </p>
    </div>
  );
}
