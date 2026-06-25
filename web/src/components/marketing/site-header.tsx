"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";

const NAV = [
  { href: "/", label: "Home" },
  { href: "/pricing", label: "Pricing" },
  { href: "/about", label: "About" },
  { href: "/faq", label: "FAQ" },
  { href: "/blog", label: "Blog" },
  { href: "/contact", label: "Contact" },
];

export function SiteHeader() {
  const pathname = usePathname();
  return (
    <header className="border-b border-border/40 bg-background/70 backdrop-blur-md sticky top-0 z-30">
      <div className="max-w-[1280px] mx-auto px-6 py-3 flex items-center gap-6">
        <Link href="/" className="flex items-center gap-1.5 font-bold tracking-tight">
          <span>claim</span>
          <span className="neon-text">farm</span>
        </Link>
        <nav className="hidden md:flex items-center gap-1 ml-4">
          {NAV.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`px-3 py-1.5 rounded-md text-sm transition ${
                  active
                    ? "text-foreground bg-muted/50"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/30"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <Link
            href="/auth/sign-in"
            className="text-sm text-muted-foreground hover:text-foreground px-3 py-1.5"
          >
            Sign in
          </Link>
          <Link href="/auth/sign-up">
            <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
              Start free
            </Button>
          </Link>
        </div>
      </div>
    </header>
  );
}
