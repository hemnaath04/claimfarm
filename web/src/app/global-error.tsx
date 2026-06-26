"use client";

import { useEffect } from "react";
import "./globals.css";

// global-error.tsx fires when the root layout itself throws; the regular
// error boundary is skipped, so this file must own its own <html>/<body>
// and any styles it needs. Keep it visually self-contained.
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
          backgroundColor: "#000",
          color: "#f5f5f5",
          fontFamily:
            "Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
        }}
      >
        <title>ClaimFarm · System error</title>
        <main style={{ maxWidth: "36rem", textAlign: "center" }}>
          <p
            style={{
              fontFamily:
                '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace',
              fontSize: "0.7rem",
              letterSpacing: "0.28em",
              textTransform: "uppercase",
              color: "rgba(245,245,245,0.55)",
              marginBottom: "1.5rem",
            }}
          >
            error · fatal
          </p>
          <h1
            style={{
              fontSize: "2.5rem",
              fontWeight: 700,
              margin: 0,
              lineHeight: 1.1,
            }}
          >
            ClaimFarm <span style={{ color: "#ccff00" }}>fell over</span>.
          </h1>
          <p
            style={{
              marginTop: "1rem",
              color: "rgba(245,245,245,0.65)",
              lineHeight: 1.6,
            }}
          >
            The site itself errored out. You can try again, or come back in a
            moment — we&apos;ve been notified.
          </p>
          {error.digest ? (
            <p
              style={{
                marginTop: "1rem",
                fontSize: "0.75rem",
                color: "rgba(245,245,245,0.45)",
                fontFamily:
                  '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace',
              }}
            >
              ref · {error.digest}
            </p>
          ) : null}
          <div
            style={{
              marginTop: "2rem",
              display: "flex",
              justifyContent: "center",
              gap: "0.75rem",
              flexWrap: "wrap",
            }}
          >
            <button
              type="button"
              onClick={() => unstable_retry()}
              style={{
                background: "#ccff00",
                color: "#000",
                fontWeight: 600,
                border: "none",
                padding: "0.625rem 1.25rem",
                borderRadius: "0.5rem",
                cursor: "pointer",
              }}
            >
              Try again
            </button>
            <a
              href="/"
              style={{
                color: "#f5f5f5",
                border: "1px solid rgba(245,245,245,0.2)",
                padding: "0.625rem 1.25rem",
                borderRadius: "0.5rem",
                textDecoration: "none",
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
