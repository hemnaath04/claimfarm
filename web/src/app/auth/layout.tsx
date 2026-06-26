import Link from "next/link";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="auth-canvas min-h-dvh flex items-center justify-center px-6 py-12">
      {/* third gradient blob — the ::before / ::after handle the other two */}
      <div className="auth-canvas-violet" aria-hidden />
      <main className="relative z-10 w-full max-w-[420px]">{children}</main>
      <Link
        href="/"
        className="absolute top-6 left-6 z-10 text-xs text-white/40 hover:text-white/70 transition"
      >
        ← Back to claimfarm.com
      </Link>
    </div>
  );
}
