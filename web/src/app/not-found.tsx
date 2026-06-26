import Link from "next/link";
import type { Metadata } from "next";

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
];

export default function NotFound() {
  return (
    <div className="auth-canvas min-h-dvh flex items-center justify-center px-6 py-12">
      <div className="auth-canvas-violet" aria-hidden />
      <main className="relative z-10 w-full max-w-[620px]">
        <div className="glass-card glass-card-violet p-5">
          <div className="flex items-center gap-2.5">
            <span className="brand-mark" aria-hidden />
            <span className="text-[22px] font-bold tracking-tight text-[#F8FAFC]">
              claimfarm
            </span>
          </div>

          <div className="eyebrow-mono mt-4 text-[#C7B8FF]">ERROR · 404</div>
          <div className="mt-1 text-[72px] leading-[92px] font-bold text-[#C7B8FF]">
            404
          </div>
          <h2 className="mt-1 text-[22px] font-bold leading-7 text-[#F8FAFC]">
            This claim row was never filed.
          </h2>
          <p className="mt-2 text-[14px] text-[#8B95A5]">
            The page you tried to reach doesn&apos;t exist — the URL may have been
            mistyped, or the link is from an older version of the site.
          </p>

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <Link
              href="/"
              className="btn-gradient h-[46px] px-5 text-sm inline-flex items-center"
            >
              Take me home
            </Link>
            <Link
              href="/contact"
              className="btn-ghost-translucent h-[46px] px-5 text-sm font-semibold inline-flex items-center"
            >
              Report a broken link
            </Link>
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 text-[13px] border-t border-white/5 pt-4">
            {SIGNPOSTS.map((s) => (
              <Link
                key={s.href}
                href={s.href}
                className="text-[#8B95A5] hover:text-[#F8FAFC] transition"
              >
                {s.label}
              </Link>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
