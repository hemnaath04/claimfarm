"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";
import { ClaimFarmLogo } from "@/components/brand/logo";
import { ThemeToggle } from "@/components/theme-toggle";
import { AuthUser, signOut, useAuthUser } from "@/lib/user-state";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const NAV: { href: string; label: string }[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/admin", label: "Adjuster" },
  { href: "/farmer", label: "Farmer intake" },
];

function initials(name: string, email: string) {
  const source = (name || email || "").trim();
  if (!source) return "··";
  const parts = source.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return source.slice(0, 2).toUpperCase();
}

function UserPill({ user }: { user: AuthUser }) {
  return (
    <div className="flex items-center gap-2.5">
      <div
        className="grid size-9 place-items-center rounded-full bg-primary text-[12px] font-bold text-primary-foreground"
        title={user.email}
        aria-hidden
      >
        {initials(user.name, user.email)}
      </div>
      <div className="hidden flex-col leading-tight lg:flex">
        <span className="text-[13px] font-medium text-foreground">
          {user.name || user.email.split("@")[0]}
        </span>
        <span className="text-[11px] text-muted-foreground">{user.email}</span>
      </div>
      <button
        onClick={signOut}
        className="ml-1 rounded-md border border-border px-2.5 py-1.5 text-[12px] text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
      >
        Sign out
      </button>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthUser();
  const [open, setOpen] = useState(false);

  // Auth gate: send anonymous visitors to sign-in. Children (which fetch
  // claims/PII) only render once a session is confirmed, so nothing
  // sensitive loads for signed-out users.
  useEffect(() => {
    if (user === false) {
      const next = encodeURIComponent(pathname || "/dashboard");
      router.replace(`/auth/sign-in?next=${next}`);
    }
  }, [user, pathname, router]);

  if (user === null || user === false) {
    return (
      <div className="grid min-h-dvh place-items-center bg-secondary/40 px-6">
        <div className="text-center">
          <ClaimFarmLogo href={null} size={34} />
          <p className="mt-6 text-sm text-muted-foreground">
            {user === null ? "Checking your session…" : "Sign in to continue."}
          </p>
          {user === false ? (
            <Link
              href="/auth/sign-in"
              className={cn(buttonVariants(), "mt-4 h-10 px-5")}
            >
              Go to sign in
            </Link>
          ) : (
            <div
              className="mx-auto mt-4 h-1 w-24 animate-pulse rounded-full bg-muted"
              aria-hidden
            />
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-dvh bg-secondary/40">
      <header className="sticky top-0 z-40 border-b border-border bg-background/90 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-[1320px] items-center gap-5 px-5 sm:px-8">
          <ClaimFarmLogo href="/dashboard" size={30} suffix="console" />

          <nav
            className="ml-2 hidden items-center gap-1 md:flex"
            aria-label="Console"
          >
            {NAV.map((item) => {
              const active =
                pathname === item.href ||
                (item.href !== "/dashboard" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`rounded-md px-3 py-2 text-sm transition-colors ${
                    active
                      ? "bg-muted font-medium text-foreground"
                      : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="ml-auto flex items-center gap-2.5">
            <Link
              href="/"
              className="hidden text-[12px] text-muted-foreground transition-colors hover:text-foreground lg:inline"
            >
              claimfarm.com →
            </Link>
            <ThemeToggle className="hidden sm:inline-grid" />
            <UserPill user={user} />
            <button
              type="button"
              onClick={() => setOpen((v) => !v)}
              aria-label={open ? "Close menu" : "Open menu"}
              aria-expanded={open}
              className="inline-grid size-9 place-items-center rounded-lg border border-border text-foreground md:hidden"
            >
              {open ? <X className="size-5" /> : <Menu className="size-5" />}
            </button>
          </div>
        </div>

        {open ? (
          <nav
            className="border-t border-border bg-background px-5 py-3 md:hidden"
            aria-label="Console mobile"
          >
            <ul className="flex flex-col">
              {NAV.map((item) => {
                const active =
                  pathname === item.href ||
                  (item.href !== "/dashboard" &&
                    pathname.startsWith(item.href));
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      onClick={() => setOpen(false)}
                      aria-current={active ? "page" : undefined}
                      className={`block rounded-md px-3 py-3 text-base ${
                        active
                          ? "bg-muted font-medium text-foreground"
                          : "text-muted-foreground"
                      }`}
                    >
                      {item.label}
                    </Link>
                  </li>
                );
              })}
              <li className="mt-2 flex items-center justify-between border-t border-border px-3 pt-3">
                <Link
                  href="/"
                  className="text-sm text-muted-foreground"
                  onClick={() => setOpen(false)}
                >
                  claimfarm.com →
                </Link>
                <ThemeToggle />
              </li>
            </ul>
          </nav>
        ) : null}
      </header>

      <main>{children}</main>
    </div>
  );
}
