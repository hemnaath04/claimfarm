"use client";

import Link from "next/link";
import { useEffect } from "react";

export default function RouteError({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string };
  unstable_retry: () => void;
}) {
  useEffect(() => {
    if (typeof console !== "undefined") {
      console.error("[claimfarm] route error", {
        message: error.message,
        digest: error.digest,
      });
    }
  }, [error]);

  const ref = error.digest ? `REF · ${error.digest.toUpperCase()}` : "REF · UNCAUGHT";

  return (
    <div className="auth-canvas min-h-dvh flex items-center justify-center px-6 py-12">
      <div className="auth-canvas-violet" aria-hidden />
      <main className="relative z-10 w-full max-w-[620px]">
        <div className="glass-card p-5">
          <div className="flex items-center gap-2.5">
            <span className="brand-mark" aria-hidden />
            <span className="text-[22px] font-bold tracking-tight text-[#F8FAFC]">
              claimfarm
            </span>
          </div>

          <div className="eyebrow-mono mt-4 text-[#9CA3AF]">{ref}</div>
          <h1 className="mt-1 text-[34px] font-bold leading-[44px] text-[#F8FAFC]">
            Something misfired
          </h1>
          <p className="mt-2 text-[16px] leading-5 text-[#AEB8C6]">
            Retry the failed action or share the digest with support — nothing in
            your account is affected.
          </p>

          <div className="mt-5 flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => unstable_retry()}
              className="btn-gradient h-[46px] px-5 text-sm inline-flex items-center"
            >
              Retry
            </button>
            <Link
              href="/"
              className="btn-ghost-translucent h-[46px] px-5 text-sm font-semibold inline-flex items-center"
            >
              Back to home
            </Link>
            <Link
              href="/contact"
              className="text-sm text-[#8B95A5] hover:text-[#F8FAFC] transition px-3 py-2"
            >
              Tell us what broke →
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
