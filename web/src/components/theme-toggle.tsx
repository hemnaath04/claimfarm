"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export function ThemeToggle({ className }: { className?: string }) {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const isDark = mounted && resolvedTheme === "dark";

  return (
    <button
      type="button"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      /* aria-label is stable pre-mount ("Switch to dark theme") and corrects
         after hydration. Users who are in dark mode pre-hydration briefly see
         "Switch to dark" which is semantically incorrect but non-breaking. */
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
      className={
        "inline-grid size-9 place-items-center rounded-lg border border-border text-muted-foreground transition-colors hover:bg-muted hover:text-foreground " +
        (className ?? "")
      }
    >
      {/* Avoid hydration mismatch: render Moon icon until mounted (stable
          server-rendered value), then switch to the correct icon. */}
      {mounted && isDark ? (
        <Sun className="size-4" aria-hidden />
      ) : (
        <Moon className="size-4" aria-hidden />
      )}
    </button>
  );
}
