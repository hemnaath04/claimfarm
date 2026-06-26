"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

function StatusPill({ kind, text }: { kind: "ok" | "err"; text: string }) {
  return (
    <span
      className={`status-pill ${kind === "ok" ? "status-pill-ok" : "status-pill-err"}`}
    >
      {text}
    </span>
  );
}

function VerifyInner() {
  const params = useSearchParams();
  const status = params.get("status");
  const error = params.get("error");

  return (
    <div className="glass-card p-5">
      <div className="flex items-center gap-2.5">
        <span className="brand-mark" aria-hidden />
        <span className="text-[22px] font-bold tracking-tight text-[#F8FAFC]">
          claimfarm
        </span>
      </div>

      {status === "ok" ? (
        <>
          <h1 className="mt-4 text-[25px] font-bold leading-8 text-[#F8FAFC]">
            You&apos;re verified
          </h1>
          <p className="mt-1 text-sm text-[#8B95A5]">
            Your account is fully activated. You can now file claims and invite
            adjusters to your workspace.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <StatusPill kind="ok" text="status=ok · verified" />
          </div>
          <Link
            href="/dashboard"
            className="btn-gradient w-full h-[46px] mt-4 text-sm inline-flex items-center justify-center"
          >
            Go to dashboard
          </Link>
          <Link
            href="/admin"
            className="btn-ghost-translucent w-full h-[46px] mt-3 text-sm font-semibold inline-flex items-center justify-center"
          >
            Open adjuster console
          </Link>
        </>
      ) : error ? (
        <>
          <h1 className="mt-4 text-[25px] font-bold leading-8 text-[#F8FAFC]">
            Link no longer valid
          </h1>
          <p className="mt-1 text-sm text-[#8B95A5]">
            {error === "expired"
              ? "That verification link has expired or was already used. Sign in and we'll send a fresh one."
              : error === "unknown"
                ? "We couldn't match that link to an account. It may have been deleted."
                : "Something went wrong verifying that link."}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <StatusPill kind="err" text={`error · ${error.replace("_", " ")}`} />
          </div>
          <Link
            href="/auth/sign-in"
            className="btn-gradient w-full h-[46px] mt-4 text-sm inline-flex items-center justify-center"
          >
            Back to sign in
          </Link>
        </>
      ) : (
        <>
          <h1 className="mt-4 text-[25px] font-bold leading-8 text-[#F8FAFC]">
            Check your inbox
          </h1>
          <p className="mt-1 text-sm text-[#8B95A5]">
            We just sent you a verification link. Click it to activate your
            account.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <StatusPill kind="ok" text="status=ok · verified" />
            <StatusPill kind="err" text="error · link expired" />
          </div>
          <p className="mt-4 text-[12px] text-[#687386]">
            Didn&apos;t get it? Check spam, or{" "}
            <Link href="/auth/sign-up" className="text-[#BDF272] hover:underline">
              resend
            </Link>
            . Link expires in 24 hours.
          </p>
        </>
      )}
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
