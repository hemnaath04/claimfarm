import Link from "next/link";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-border/40 bg-background/70 backdrop-blur-md">
        <div className="max-w-[1200px] mx-auto px-6 py-3 flex items-center gap-6">
          <Link href="/" className="flex items-center gap-1.5 font-bold tracking-tight">
            <span>claim</span>
            <span className="neon-text">farm</span>
          </Link>
        </div>
      </header>
      <main className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-[420px]">{children}</div>
      </main>
    </div>
  );
}
