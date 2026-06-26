import Link from "next/link";
import type { Metadata } from "next";
import { Button } from "@/components/ui/button";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";

export const metadata: Metadata = {
  title: "404 · Page not found · ClaimFarm",
  description: "The page you're looking for doesn't exist on ClaimFarm.",
};

const SIGNPOSTS = [
  { href: "/", label: "Home" },
  { href: "/pricing", label: "Pricing" },
  { href: "/farmer", label: "For farmers" },
  { href: "/admin", label: "Adjuster console" },
  { href: "/dashboard", label: "Your dashboard" },
  { href: "/faq", label: "FAQ" },
];

export default function NotFound() {
  return (
    <div className="min-h-dvh flex flex-col">
      <SiteHeader />
      <main className="flex-1 grid place-items-center px-6 py-24">
        <div className="max-w-xl text-center">
          <p className="mono-id text-xs uppercase tracking-[0.28em] text-muted-foreground mb-6">
            error · 404
          </p>
          <h1 className="text-6xl md:text-8xl font-bold tracking-tight">
            <span className="neon-text">404</span>
          </h1>
          <h2 className="text-2xl md:text-3xl font-semibold mt-6">
            This row was never filed.
          </h2>
          <p className="text-muted-foreground mt-3 leading-relaxed">
            The page you tried to reach doesn&apos;t exist — maybe the URL was
            mistyped, or the link is from an older version of the site.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link href="/">
              <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
                Take me home
              </Button>
            </Link>
            <Link href="/contact">
              <Button variant="outline">Report a broken link</Button>
            </Link>
          </div>
          <div className="mt-12 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-sm">
            {SIGNPOSTS.map((s) => (
              <Link
                key={s.href}
                href={s.href}
                className="text-muted-foreground hover:text-foreground transition"
              >
                {s.label}
              </Link>
            ))}
          </div>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
