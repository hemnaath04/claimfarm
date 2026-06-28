"use client";

import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";
import { postAuthJson } from "@/lib/auth-fetch";
import { AuthField } from "@/components/auth/auth-field";
import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

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
        toast.success(
          "If an account exists for that email, a reset link is on its way."
        );
      }
    } catch (err) {
      const e = err as { detail?: string };
      toast.error(e.detail ?? "Could not send reset email. Try again.");
    } finally {
      setBusy(false);
    }
  };

  if (sent) {
    return (
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Check your inbox
        </h1>
        <p className="mt-2 text-[15px] text-muted-foreground">
          If an account exists for{" "}
          <span className="font-medium text-foreground">{email}</span>, we just
          sent it a password-reset link. It expires in 1 hour.
        </p>
        {devLink ? (
          <div className="mt-5 rounded-lg border border-primary/30 bg-primary/5 p-4 text-sm">
            <div className="mb-1.5 font-medium text-primary">
              Dev mode — email transport not configured
            </div>
            <a
              href={devLink}
              className="break-all font-mono text-[13px] text-primary underline"
            >
              {devLink}
            </a>
          </div>
        ) : null}
        <Link
          href="/auth/sign-in"
          className={cn(
            buttonVariants({ variant: "outline" }),
            "mt-6 h-11 w-full text-[15px]"
          )}
        >
          Back to sign in
        </Link>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold tracking-tight text-foreground">
        Reset your password
      </h1>
      <p className="mt-2 text-[15px] text-muted-foreground">
        We&apos;ll email you a link to set a new one.
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
        <Button
          type="submit"
          disabled={busy}
          className="mt-1 h-11 w-full text-[15px]"
        >
          {busy ? "Sending…" : "Send reset link"}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Remembered it?{" "}
        <Link
          href="/auth/sign-in"
          className="font-medium text-primary hover:underline"
        >
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
