import Link from "next/link";
import { ClaimFarmLogo } from "@/components/brand/logo";

const COLUMNS = [
  {
    title: "Product",
    links: [
      { href: "/", label: "Overview" },
      { href: "/pricing", label: "Pricing" },
      { href: "/farmer", label: "For farmers" },
      { href: "/admin", label: "Adjuster console" },
    ],
  },
  {
    title: "Company",
    links: [
      { href: "/about", label: "About" },
      { href: "/blog", label: "Blog" },
      { href: "/faq", label: "FAQ" },
      { href: "/contact", label: "Contact" },
    ],
  },
  {
    title: "Legal",
    links: [
      { href: "/legal/terms", label: "Terms" },
      { href: "/legal/privacy", label: "Privacy" },
    ],
  },
];

export function SiteFooter() {
  return (
    <footer className="mt-24 border-t border-border bg-secondary/60">
      <div className="mx-auto grid max-w-[1200px] grid-cols-2 gap-8 px-5 py-14 sm:px-8 md:grid-cols-5">
        <div className="col-span-2">
          <ClaimFarmLogo size={30} href="/" />
          <p className="mt-4 max-w-sm text-sm leading-6 text-muted-foreground">
            Photo-first crop insurance for the next 500 million smallholder
            farmers. One photo, one filed claim, in any language.
          </p>
        </div>
        {COLUMNS.map((col) => (
          <nav key={col.title} aria-label={col.title}>
            <div className="mb-3 text-sm font-semibold text-foreground">
              {col.title}
            </div>
            <ul className="space-y-2.5">
              {col.links.map((l) => (
                <li key={l.href}>
                  <Link
                    href={l.href}
                    className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                  >
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        ))}
        <div className="col-span-2 md:col-span-1">
          <div className="mb-3 text-sm font-semibold text-foreground">
            Open source
          </div>
          <ul className="space-y-2.5">
            <li>
              <a
                href="https://github.com/hemnaath04/claimfarm"
                target="_blank"
                rel="noreferrer"
                className="text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                GitHub repository
              </a>
            </li>
          </ul>
        </div>
      </div>
      <div className="border-t border-border">
        <div className="mx-auto flex max-w-[1200px] flex-col gap-2 px-5 py-6 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <div>© 2026 ClaimFarm · MIT licensed</div>
          <div>Built on Qwen Cloud + Alibaba Cloud</div>
        </div>
      </div>
    </footer>
  );
}
