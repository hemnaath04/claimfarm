"use client";

import Link from "next/link";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";

export default function RouteError({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string };
  unstable_retry: () => void;
}) {
  useEffect(() => {
    // Production builds give us only `digest` — log it so it can be
    // cross-referenced against the server logs when triaging.
    if (typeof console !== "undefined") {
      console.error("[claimfarm] route error", {
        message: error.message,
        digest: error.digest,
      });
    }
  }, [error]);

  return (
    <div className="min-h-dvh flex flex-col">
      <SiteHeader />
      <main className="flex-1 grid place-items-center px-6 py-24">
        <div className="max-w-xl text-center">
          <p className="mono-id text-xs uppercase tracking-[0.28em] text-muted-foreground mb-6">
            error · uncaught
          </p>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
            Something <span className="neon-text">misfired</span>.
          </h1>
          <p className="text-muted-foreground mt-4 leading-relaxed">
            We tripped over an error on this page. Try again, or head home —
            either way nothing in your account is affected.
          </p>
          {error.digest ? (
            <p className="mono-id mt-4 text-xs text-muted-foreground/70">
              ref · {error.digest}
            </p>
          ) : null}
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Button
              onClick={() => unstable_retry()}
              className="bg-primary text-primary-foreground hover:bg-primary/90"
            >
              Try again
            </Button>
            <Link href="/">
              <Button variant="outline">Back to home</Button>
            </Link>
            <Link href="/contact">
              <Button variant="ghost">Tell us what broke</Button>
            </Link>
          </div>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
