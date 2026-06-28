"use client";

import Link from "next/link";
import { useEffect } from "react";
import { ClaimFarmLogo } from "@/components/brand/logo";
import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

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

  const ref = error.digest
    ? `Ref · ${error.digest.toUpperCase()}`
    : "Ref · uncaught";

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <div className="px-5 py-5 sm:px-8">
        <ClaimFarmLogo href="/" size={30} />
      </div>
      <main className="flex flex-1 items-center justify-center px-5 pb-20 sm:px-8">
        <div className="w-full max-w-[620px] rounded-2xl border border-border bg-card p-8 vl-shadow-card">
          <p className="vl-eyebrow">{ref}</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-foreground">
            Something misfired
          </h1>
          <p className="mt-2 text-[15px] text-muted-foreground">
            Retry the failed action or share the reference with support —
            nothing in your account is affected.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-2.5">
            <Button onClick={() => unstable_retry()} className="h-11 px-5">
              Retry
            </Button>
            <Link
              href="/"
              className={cn(
                buttonVariants({ variant: "outline" }),
                "h-11 px-5"
              )}
            >
              Back to home
            </Link>
            <Link
              href="/contact"
              className="px-3 py-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              Tell us what broke →
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
