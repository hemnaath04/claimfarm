"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ClaimFarmLogo } from "@/components/brand/logo";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isSignUp = pathname?.startsWith("/auth/sign-up");

  return (
    <div className="grid min-h-dvh lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
      {/* Brand panel — forest for most, harvest for sign-up. Hidden on mobile. */}
      <aside
        className={`relative hidden flex-col justify-between p-12 lg:flex ${
          isSignUp ? "vl-harvest" : "vl-forest"
        }`}
      >
        <ClaimFarmLogo href="/" tone={isSignUp ? "ink" : "light"} size={34} />
        <div className="max-w-md">
          <p
            className={`text-3xl font-bold leading-tight tracking-tight ${
              isSignUp ? "text-forest-deep" : "text-white"
            }`}
          >
            {isSignUp
              ? "Your first 100 filed claims are free."
              : "Every claim starts with evidence. Every decision stays human."}
          </p>
          <p
            className={`mt-4 text-base leading-7 ${
              isSignUp ? "text-forest-deep/80" : "text-white/80"
            }`}
          >
            {isSignUp
              ? "Set up your insurer workspace in under a minute — no card, no contract, no risk."
              : "Photo-first crop insurance, reviewed by people. Triage faster without losing the human in the loop."}
          </p>
        </div>
        <p
          className={`text-sm ${
            isSignUp ? "text-forest-deep/70" : "text-white/60"
          }`}
        >
          Built on Qwen Cloud + Alibaba Cloud
        </p>
      </aside>

      {/* Form column */}
      <div className="relative flex flex-col bg-background">
        <div className="flex items-center justify-between px-5 py-5 sm:px-8">
          <Link
            href="/"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            ← Back to claimfarm.com
          </Link>
          <span className="lg:hidden">
            <ClaimFarmLogo href="/" size={26} />
          </span>
        </div>
        <main className="flex flex-1 items-center justify-center px-5 pb-16 sm:px-8">
          <div className="w-full max-w-[440px]">{children}</div>
        </main>
      </div>
    </div>
  );
}
