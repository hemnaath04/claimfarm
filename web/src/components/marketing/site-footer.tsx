import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-border/40 mt-24 py-12 text-sm text-muted-foreground">
      <div className="max-w-[1280px] mx-auto px-6 grid grid-cols-2 md:grid-cols-5 gap-8">
        <div className="col-span-2">
          <Link href="/" className="font-bold tracking-tight inline-flex items-center gap-1.5">
            <span className="text-foreground">claim</span>
            <span className="neon-text">farm</span>
          </Link>
          <p className="mt-3 max-w-sm">
            Crop insurance for the next 500 million smallholder farmers. One
            WhatsApp photo, one filed claim, in any language.
          </p>
        </div>
        <div>
          <div className="text-foreground font-medium mb-3">Product</div>
          <ul className="space-y-2">
            <li><Link href="/" className="hover:text-foreground">Overview</Link></li>
            <li><Link href="/pricing" className="hover:text-foreground">Pricing</Link></li>
            <li><Link href="/farmer" className="hover:text-foreground">For farmers</Link></li>
            <li><Link href="/admin" className="hover:text-foreground">Adjuster console</Link></li>
          </ul>
        </div>
        <div>
          <div className="text-foreground font-medium mb-3">Company</div>
          <ul className="space-y-2">
            <li><Link href="/about" className="hover:text-foreground">About</Link></li>
            <li><Link href="/blog" className="hover:text-foreground">Blog</Link></li>
            <li><Link href="/faq" className="hover:text-foreground">FAQ</Link></li>
            <li><Link href="/contact" className="hover:text-foreground">Contact</Link></li>
          </ul>
        </div>
        <div>
          <div className="text-foreground font-medium mb-3">Legal</div>
          <ul className="space-y-2">
            <li><Link href="/legal/terms" className="hover:text-foreground">Terms</Link></li>
            <li><Link href="/legal/privacy" className="hover:text-foreground">Privacy</Link></li>
            <li><a href="https://github.com/hemnaath04/claimfarm" className="hover:text-foreground" target="_blank" rel="noreferrer">Open source</a></li>
          </ul>
        </div>
      </div>
      <div className="max-w-[1280px] mx-auto px-6 mt-10 pt-6 border-t border-border/30 flex items-center justify-between text-xs">
        <div>© 2026 ClaimFarm · MIT licensed</div>
        <div>Built on Qwen Cloud + Alibaba Cloud</div>
      </div>
    </footer>
  );
}
