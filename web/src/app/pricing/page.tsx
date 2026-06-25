import Link from "next/link";
import type { Metadata } from "next";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";

export const metadata: Metadata = {
  title: "Pricing · ClaimFarm",
  description:
    "Per-claim pricing built for small micro-insurers, NGOs and pilots in emerging markets. Free during your first 100 claims.",
};

type Tier = {
  name: string;
  price: string;
  cadence?: string;
  description: string;
  features: string[];
  cta: { label: string; href: string };
  highlight?: boolean;
};

const TIERS: Tier[] = [
  {
    name: "Pilot",
    price: "Free",
    cadence: "up to 100 claims",
    description: "For NGOs and micro-insurers piloting the channel.",
    features: [
      "Up to 100 filed claims",
      "WhatsApp + Telegram intake",
      "Multimodal damage assessment",
      "Adjuster console for 1 reviewer",
      "Community support",
    ],
    cta: { label: "Start free", href: "/auth/sign-up" },
  },
  {
    name: "Growth",
    price: "$0.85",
    cadence: "per filed claim",
    description: "For active programs running 100–10,000 claims a month.",
    features: [
      "Everything in Pilot",
      "Unlimited reviewers + RBAC",
      "Identity verification (KYC) included",
      "Custom branding on farmer messages",
      "Signed-URL PDF delivery to insurer",
      "Weekly anomaly + fraud report",
      "Email support, 24h SLA",
    ],
    cta: { label: "Choose Growth", href: "/auth/sign-up?plan=growth" },
    highlight: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    description:
      "For national insurers, government schemes, and reinsurers.",
    features: [
      "Everything in Growth",
      "Volume pricing under $0.40/claim",
      "Private model fine-tuning (Qwen-VL)",
      "Tablestore + dedicated DashVector cluster",
      "VPC / on-prem deployment",
      "Custom integrations (policy systems, payment rails)",
      "24×7 support + named CSM",
    ],
    cta: { label: "Talk to sales", href: "/contact" },
  },
];

const FAQ_ROW = [
  ["Is there a setup fee?", "No. The Pilot tier is free for your first 100 filed claims, no card required."],
  ["What does 'filed claim' mean?", "A claim that has been assessed, reviewed, and forwarded to your insurer intake. Drafts and rejected pre-checks are not counted."],
  ["Do unused credits roll over?", "Yes on Growth and Enterprise; Pilot is a one-shot trial."],
  ["What if a farmer's photo can't be processed?", "You're not billed. We only charge for completed assessments where the adjuster receives a packet."],
];

export default function PricingPage() {
  return (
    <>
      <SiteHeader />
      <main className="max-w-[1280px] mx-auto px-6 pt-20 pb-16">
        <div className="text-center max-w-3xl mx-auto">
          <div className="text-xs font-semibold uppercase tracking-wider text-primary">
            Pricing
          </div>
          <h1 className="mt-3 text-4xl md:text-6xl font-bold tracking-tight">
            Pay per filed claim. <span className="neon-text">No surprises.</span>
          </h1>
          <p className="mt-5 text-lg text-muted-foreground">
            Free pilot for your first 100 claims. Then $0.85 a claim on Growth,
            volume pricing on Enterprise. AI inference and storage are on us.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 md:grid-cols-3 gap-4">
          {TIERS.map((t) => (
            <Card
              key={t.name}
              className={`glass relative ${
                t.highlight ? "ring-2 ring-primary/60 shadow-[0_0_60px_rgba(204,255,0,0.15)]" : ""
              }`}
            >
              {t.highlight ? (
                <div className="absolute -top-3 right-6 px-3 py-1 rounded-full bg-primary text-primary-foreground text-[10px] uppercase tracking-wider font-bold">
                  Most popular
                </div>
              ) : null}
              <CardContent className="p-7">
                <div className="text-lg font-semibold">{t.name}</div>
                <div className="mt-1 text-sm text-muted-foreground">{t.description}</div>
                <div className="mt-6 flex items-baseline gap-2">
                  <div className="text-4xl font-bold tabular-nums">{t.price}</div>
                  {t.cadence ? (
                    <div className="text-sm text-muted-foreground">{t.cadence}</div>
                  ) : null}
                </div>
                <Link href={t.cta.href}>
                  <Button
                    className={`mt-6 w-full ${
                      t.highlight
                        ? "bg-primary text-primary-foreground hover:bg-primary/90"
                        : ""
                    }`}
                    variant={t.highlight ? "default" : "outline"}
                  >
                    {t.cta.label}
                  </Button>
                </Link>
                <ul className="mt-6 space-y-2.5 text-sm">
                  {t.features.map((f) => (
                    <li key={f} className="flex items-start gap-2">
                      <span className="text-primary mt-0.5">✓</span>
                      <span className="text-muted-foreground">{f}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>

        <section className="mt-24">
          <h2 className="text-2xl font-bold">Common questions</h2>
          <div className="mt-6 space-y-3">
            {FAQ_ROW.map(([q, a]) => (
              <Card key={q} className="glass">
                <CardContent className="p-6">
                  <div className="font-medium">{q}</div>
                  <div className="mt-2 text-sm text-muted-foreground">{a}</div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
