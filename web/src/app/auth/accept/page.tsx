"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { toast } from "sonner";
import { TriangleAlert } from "lucide-react";
import { AuthField } from "@/components/auth/auth-field";
import { Button, buttonVariants } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import { acceptInvite } from "@/lib/api";
import { cn } from "@/lib/utils";

function AcceptInner() {
  const params = useSearchParams();
  const token = params.get("invite");

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  // No token in the URL — the link is malformed or was opened directly.
  if (!token) {
    return (
      <div>
        <TriangleAlert className="size-10 text-destructive" aria-hidden />
        <h1 className="mt-4 text-3xl font-bold tracking-tight text-foreground">
          This invitation is invalid or has expired.
        </h1>
        <p className="mt-2 text-[15px] text-muted-foreground">
          Ask your workspace owner to send you a fresh invite link.
        </p>
        <div className="mt-4">
          <StatusBadge tone="danger">Invalid link</StatusBadge>
        </div>
        <Link
          href="/auth/sign-in"
          className={cn(buttonVariants(), "mt-6 h-11 w-full text-[15px]")}
        >
          Back to sign in
        </Link>
      </div>
    );
  }

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setFailed(false);
    try {
      await acceptInvite({
        token,
        password,
        name,
        email: email.trim() || undefined,
      });
      toast.success("Welcome aboard — redirecting…");
      window.location.href = "/admin";
    } catch {
      setFailed(true);
      toast.error("This invitation is invalid or has expired.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold tracking-tight text-foreground">
        Accept your invitation
      </h1>
      <p className="mt-2 text-[15px] text-muted-foreground">
        Set a password to join the workspace and start reviewing claims.
      </p>

      {failed ? (
        <div
          role="alert"
          className="mt-5 rounded-lg border border-destructive/40 bg-destructive/8 p-3 text-sm text-foreground"
        >
          This invitation is invalid or has expired.{" "}
          <Link href="/auth/sign-in" className="font-medium underline">
            Sign in
          </Link>{" "}
          if you already have an account.
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
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@insurer.org"
          autoComplete="email"
          hint={
            <span className="text-xs text-muted-foreground">
              Only if not pre-filled
            </span>
          }
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
          {busy ? "Joining…" : "Accept invite & continue"}
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
    </div>
  );
}

export default function AcceptInvitePage() {
  return (
    <Suspense fallback={null}>
      <AcceptInner />
    </Suspense>
  );
}
