"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AuthUser, signOut, useAuthUser } from "@/lib/user-state";

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
    <div className="flex items-center gap-2">
      <div
        className="h-8 w-8 rounded-full grid place-items-center text-[12px] font-bold text-[#07110D]"
        style={{
          background: "var(--brand-gradient)",
          border: "1px solid rgba(189, 242, 114, 0.45)",
        }}
        title={user.email}
      >
        {initials(user.name, user.email)}
      </div>
      <div className="hidden md:flex flex-col leading-tight">
        <span className="text-[13px] font-medium text-[#F8FAFC]">
          {user.name || user.email.split("@")[0]}
        </span>
        <span className="text-[11px] text-[#8B95A5]">{user.email}</span>
      </div>
      <button
        onClick={signOut}
        className="ml-2 text-[12px] text-[#8B95A5] hover:text-[#F8FAFC] transition border border-white/10 rounded-md px-2.5 py-1"
      >
        Sign out
      </button>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const user = useAuthUser();

  return (
    <div className="auth-canvas min-h-dvh">
      <div className="auth-canvas-violet" aria-hidden />
      <header className="relative z-10 border-b border-white/5 backdrop-blur-md bg-[rgba(5,7,10,0.55)]">
        <div className="max-w-[1280px] mx-auto px-6 h-14 flex items-center gap-6">
          <Link
            href="/dashboard"
            className="flex items-center gap-2.5 font-bold tracking-tight"
          >
            <span className="brand-mark" aria-hidden style={{ width: 28, height: 28, borderRadius: 7 }} />
            <span className="text-[18px] text-[#F8FAFC]">claimfarm</span>
            <span className="hidden sm:inline-block text-[10px] uppercase tracking-[0.18em] text-[#8B95A5] border border-white/10 rounded px-1.5 py-0.5 ml-1">
              console
            </span>
          </Link>
          <nav className="hidden md:flex items-center gap-1 ml-2">
            {NAV.map((item) => {
              const active =
                pathname === item.href ||
                (item.href !== "/dashboard" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-3 py-1.5 rounded-md text-sm transition ${
                    active
                      ? "text-[#F8FAFC] bg-white/[0.06]"
                      : "text-[#8B95A5] hover:text-[#F8FAFC] hover:bg-white/[0.03]"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="ml-auto flex items-center gap-3">
            <Link
              href="/"
              className="text-[12px] text-[#8B95A5] hover:text-[#F8FAFC] transition hidden md:inline"
            >
              claimfarm.com →
            </Link>
            {user === null ? (
              <div className="h-8 w-24 rounded-md bg-white/5 animate-pulse" aria-hidden />
            ) : user === false ? (
              <Link
                href="/auth/sign-in"
                className="btn-gradient h-9 px-4 text-[13px] inline-flex items-center"
              >
                Sign in
              </Link>
            ) : (
              <UserPill user={user} />
            )}
          </div>
        </div>
      </header>

      <main className="relative z-10">{children}</main>
    </div>
  );
}
