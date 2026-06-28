"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { CheckCircle2, Loader2, MailCheck, TriangleAlert } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import { cn } from "@/lib/utils";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "";

type State = "idle" | "loading" | "ok" | "expired" | "unknown";

function VerifyInner() {
  const params = useSearchParams();
  const token = params.get("token"); // email verification
  const magic = params.get("magic"); // passwordless sign-in
  // Back-compat with any old links that carried ?status / ?error directly.
  const initial: State =
    params.get("status") === "ok"
      ? "ok"
      : params.get("error")
        ? "expired"
        : token || magic
          ? "loading"
          : "idle";
  const [state, setState] = useState<State>(initial);

  useEffect(() => {
    let cancelled = false;
    if (token) {
      fetch(`${API_BASE}/auth/verify?token=${encodeURIComponent(token)}`, {
        cache: "no-store",
      })
        .then((r) => r.json())
        .then((d: { status?: string }) => {
          if (cancelled) return;
          setState(
            d.status === "ok"
              ? "ok"
              : d.status === "unknown"
                ? "unknown"
                : "expired"
          );
        })
        .catch(() => !cancelled && setState("expired"));
    } else if (magic) {
      // Consume the magic link (sets the session cookie on the API domain),
      // then land on the dashboard.
      fetch(
        `${API_BASE}/auth/magic-link/consume?token=${encodeURIComponent(magic)}&redirect=false`,
        { method: "GET", credentials: "include", cache: "no-store" }
      )
        .then((r) => (r.ok ? r.json() : Promise.reject()))
        .then(() => {
          window.location.href = "/dashboard";
        })
        .catch(() => !cancelled && setState("expired"));
    }
    return () => {
      cancelled = true;
    };
  }, [token, magic]);

  if (state === "loading") {
    return (
      <div className="text-center">
        <Loader2 className="mx-auto size-8 animate-spin text-primary" aria-hidden />
        <h1 className="mt-4 text-2xl font-bold tracking-tight text-foreground">
          {magic ? "Signing you in…" : "Verifying your email…"}
        </h1>
        <p className="mt-2 text-[15px] text-muted-foreground">One moment.</p>
      </div>
    );
  }

  if (state === "ok") {
    return (
      <div>
        <CheckCircle2 className="size-10 text-success" aria-hidden />
        <h1 className="mt-4 text-3xl font-bold tracking-tight text-foreground">
          You&apos;re verified
        </h1>
        <p className="mt-2 text-[15px] text-muted-foreground">
          Your account is fully activated. You can now file claims and invite
          adjusters to your workspace.
        </p>
        <div className="mt-4">
          <StatusBadge tone="success">Verified</StatusBadge>
        </div>
        <Link
          href="/dashboard"
          className={cn(buttonVariants(), "mt-6 h-11 w-full text-[15px]")}
        >
          Go to dashboard
        </Link>
        <Link
          href="/admin"
          className={cn(
            buttonVariants({ variant: "outline" }),
            "mt-3 h-11 w-full text-[15px]"
          )}
        >
          Open adjuster console
        </Link>
      </div>
    );
  }

  if (state === "expired" || state === "unknown") {
    return (
      <div>
        <TriangleAlert className="size-10 text-destructive" aria-hidden />
        <h1 className="mt-4 text-3xl font-bold tracking-tight text-foreground">
          Link no longer valid
        </h1>
        <p className="mt-2 text-[15px] text-muted-foreground">
          {state === "unknown"
            ? "We couldn't match that link to an account. It may have been deleted."
            : "That link has expired or was already used. Sign in and we'll send a fresh one."}
        </p>
        <div className="mt-4">
          <StatusBadge tone="danger">Link expired</StatusBadge>
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

  // idle — landed here without a token (e.g. right after sign-up)
  return (
    <div>
      <MailCheck className="size-10 text-primary" aria-hidden />
      <h1 className="mt-4 text-3xl font-bold tracking-tight text-foreground">
        Check your inbox
      </h1>
      <p className="mt-2 text-[15px] text-muted-foreground">
        We just sent you a verification link. Click it to activate your account.
      </p>
      <p className="mt-5 text-sm text-muted-foreground">
        Didn&apos;t get it? Check spam, or{" "}
        <Link
          href="/auth/sign-up"
          className="font-medium text-primary hover:underline"
        >
          resend
        </Link>
        . Link expires in 24 hours.
      </p>
    </div>
  );
}

export default function VerifyPage() {
  return (
    <Suspense fallback={null}>
      <VerifyInner />
    </Suspense>
  );
}
