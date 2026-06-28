"use client";

import { useEffect } from "react";
import "./globals.css";

// global-error.tsx fires when the root layout itself throws; the regular
// error boundary is skipped, so this file must own its own <html>/<body>.
// Inline styles only — Verdant Ledger ivory + forest, no Tailwind reliance.
export default function GlobalError({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string };
  unstable_retry: () => void;
}) {
  useEffect(() => {
    if (typeof console !== "undefined") {
      console.error("[claimfarm] global error", {
        message: error.message,
        digest: error.digest,
      });
    }
  }, [error]);

  return (
    <html lang="en">
      <body
        style={{
          minHeight: "100dvh",
          margin: 0,
          display: "grid",
          placeItems: "center",
          padding: "4rem 1.5rem",
          backgroundColor: "#fffcf5",
          color: "#191b18",
          fontFamily:
            "Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
        }}
      >
        <title>ClaimFarm · System error</title>
        <main
          style={{
            maxWidth: "34rem",
            width: "100%",
            background: "#ffffff",
            border: "1px solid #e4e0d8",
            borderRadius: "1rem",
            padding: "2rem",
            boxShadow: "0 8px 24px 0 rgba(11,47,34,0.08)",
          }}
        >
          <p
            style={{
              fontSize: "0.75rem",
              fontWeight: 600,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "#195b40",
              margin: 0,
            }}
          >
            Error · fatal
          </p>
          <h1
            style={{
              fontSize: "1.875rem",
              fontWeight: 700,
              margin: "0.75rem 0 0",
              lineHeight: 1.1,
              letterSpacing: "-0.02em",
            }}
          >
            ClaimFarm hit a snag
          </h1>
          <p style={{ marginTop: "0.5rem", color: "#69675f", lineHeight: 1.6 }}>
            The site itself errored out. You can try again, or come back in a
            moment — we&apos;ve been notified.
          </p>
          {error.digest ? (
            <p
              style={{
                marginTop: "0.75rem",
                fontSize: "0.75rem",
                color: "#9a9482",
                fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
              }}
            >
              ref · {error.digest}
            </p>
          ) : null}
          <div
            style={{
              marginTop: "1.5rem",
              display: "flex",
              gap: "0.75rem",
              flexWrap: "wrap",
            }}
          >
            <button
              type="button"
              onClick={() => unstable_retry()}
              style={{
                background: "#195b40",
                color: "#ffffff",
                fontWeight: 600,
                border: "none",
                padding: "0.7rem 1.25rem",
                borderRadius: "0.625rem",
                cursor: "pointer",
                minHeight: "44px",
              }}
            >
              Try again
            </button>
            <a
              href="/"
              style={{
                color: "#191b18",
                border: "1px solid #e4e0d8",
                padding: "0.7rem 1.25rem",
                borderRadius: "0.625rem",
                textDecoration: "none",
                display: "inline-flex",
                alignItems: "center",
                minHeight: "44px",
              }}
            >
              Go home
            </a>
          </div>
        </main>
      </body>
    </html>
  );
}
