import Link from "next/link";
import type { Metadata } from "next";
import { ClaimFarmLogo } from "@/components/brand/logo";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export const metadata: Metadata = {
  title: "Page not found",
  description: "The page you're looking for doesn't exist on ClaimFarm.",
};

const SIGNPOSTS = [
  { href: "/", label: "Home" },
  { href: "/pricing", label: "Pricing" },
  { href: "/farmer", label: "For farmers" },
  { href: "/admin", label: "Adjuster console" },
  { href: "/dashboard", label: "Your dashboard" },
];

export default function NotFound() {
  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <div className="px-5 py-5 sm:px-8">
        <ClaimFarmLogo href="/" size={30} />
      </div>
      <main className="flex flex-1 items-center justify-center px-5 pb-20 sm:px-8">
        <div className="w-full max-w-[620px] rounded-2xl border border-border bg-card p-8 vl-shadow-card">
          <p className="vl-eyebrow">Error · 404</p>
          <div className="mt-2 text-6xl font-bold tracking-tight text-primary sm:text-7xl">
            404
          </div>
          <h1 className="mt-2 text-2xl font-bold text-foreground">
            This claim row was never filed.
          </h1>
          <p className="mt-2 text-[15px] text-muted-foreground">
            The page you tried to reach doesn&apos;t exist — the URL may have
            been mistyped, or the link is from an older version of the site.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-2.5">
            <Link href="/" className={cn(buttonVariants(), "h-11 px-5")}>
              Take me home
            </Link>
            <Link
              href="/contact"
              className={cn(
                buttonVariants({ variant: "outline" }),
                "h-11 px-5"
              )}
            >
              Report a broken link
            </Link>
          </div>

          <nav
            aria-label="Helpful links"
            className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-border pt-5 text-sm"
          >
            {SIGNPOSTS.map((s) => (
              <Link
                key={s.href}
                href={s.href}
                className="text-muted-foreground transition-colors hover:text-foreground"
              >
                {s.label}
              </Link>
            ))}
          </nav>
        </div>
      </main>
    </div>
  );
}
