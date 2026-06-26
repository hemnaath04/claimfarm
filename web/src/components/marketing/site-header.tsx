"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthUser } from "@/lib/user-state";

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
  const user = useAuthUser();

  return (
    <header className="border-b border-border/40 bg-background/70 backdrop-blur-md sticky top-0 z-30">
      <div className="max-w-[1280px] mx-auto px-6 py-3 flex items-center gap-6">
        <Link
          href="/"
          className="flex items-center gap-2 font-bold tracking-tight"
        >
          <span
            className="brand-mark"
            aria-hidden
            style={{ width: 24, height: 24, borderRadius: 6 }}
          />
          <span className="text-[16px]">claimfarm</span>
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
          {user === null ? (
            <div className="h-9 w-24 rounded-md bg-white/5 animate-pulse" aria-hidden />
          ) : user ? (
            <>
              <span className="hidden md:inline text-[12px] text-[#8B95A5]">
                {user.email}
              </span>
              <Link
                href="/dashboard"
                className="btn-gradient h-9 px-4 text-[13px] inline-flex items-center"
              >
                Open dashboard
              </Link>
            </>
          ) : (
            <>
              <Link
                href="/auth/sign-in"
                className="text-sm text-muted-foreground hover:text-foreground px-3 py-1.5"
              >
                Sign in
              </Link>
              <Link
                href="/auth/sign-up"
                className="btn-gradient h-9 px-4 text-[13px] inline-flex items-center"
              >
                Start free
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
