"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { CheckCircle2, MailCheck, TriangleAlert } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import { cn } from "@/lib/utils";

function VerifyInner() {
  const params = useSearchParams();
  const status = params.get("status");
  const error = params.get("error");

  if (status === "ok") {
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

  if (error) {
    return (
      <div>
        <TriangleAlert className="size-10 text-destructive" aria-hidden />
        <h1 className="mt-4 text-3xl font-bold tracking-tight text-foreground">
          Link no longer valid
        </h1>
        <p className="mt-2 text-[15px] text-muted-foreground">
          {error === "expired"
            ? "That verification link has expired or was already used. Sign in and we'll send a fresh one."
            : error === "unknown"
              ? "We couldn't match that link to an account. It may have been deleted."
              : "Something went wrong verifying that link."}
        </p>
        <div className="mt-4">
          <StatusBadge tone="danger">{`Error · ${error.replace("_", " ")}`}</StatusBadge>
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
