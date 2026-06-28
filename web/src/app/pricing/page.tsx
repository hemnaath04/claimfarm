import Link from "next/link";
import type { Metadata } from "next";
import { Check } from "lucide-react";
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
    description: "For national insurers, government schemes, and reinsurers.",
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
    <div className="flex min-h-dvh flex-col">
      <SiteHeader />
      <main className="flex-1">
        {/* HERO */}
        <section className="vl-forest">
          <div className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
            <div className="mx-auto max-w-3xl text-center vl-fade-up">
              <p className="vl-eyebrow text-harvest dark:text-harvest">Pricing</p>
              <h1 className="vl-display mt-3 text-white">
                Pay per filed claim. No surprises.
              </h1>
              <p className="mt-5 text-lg leading-relaxed text-white/80">
                Free pilot for your first 100 claims. Then $0.85 a claim on
                Growth, volume pricing on Enterprise. AI inference and storage
                are on us.
              </p>
            </div>
          </div>
        </section>

        {/* PLANS */}
        <section className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
          <div className="grid grid-cols-1 items-start gap-5 md:grid-cols-3">
            {TIERS.map((t) => (
              <Card
                key={t.name}
                className={`relative overflow-visible rounded-xl bg-card ring-0 ${
                  t.highlight
                    ? "border-2 border-forest vl-shadow-raised dark:border-success"
                    : "border border-border vl-shadow-card"
                }`}
              >
                {t.highlight ? (
                  <div className="absolute -top-3 right-6">
                    <span className="vl-harvest inline-flex items-center rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-wider">
                      Recommended
                    </span>
                  </div>
                ) : null}
                <CardContent className="p-6">
                  <div className="text-lg font-semibold text-foreground">
                    {t.name}
                  </div>
                  <div className="mt-1 text-sm text-muted-foreground">
                    {t.description}
                  </div>
                  <div className="mt-6 flex items-baseline gap-2">
                    <div className="text-4xl font-bold tabular-nums text-foreground">
                      {t.price}
                    </div>
                    {t.cadence ? (
                      <div className="text-sm text-muted-foreground">
                        {t.cadence}
                      </div>
                    ) : null}
                  </div>
                  <Button
                    render={<Link href={t.cta.href} />}
                    variant={t.highlight ? "default" : "outline"}
                    className="mt-6 h-11 w-full px-6 text-base"
                  >
                    {t.cta.label}
                  </Button>
                  <ul className="mt-6 space-y-2.5 text-sm">
                    {t.features.map((f) => (
                      <li key={f} className="flex items-start gap-2">
                        <Check
                          className="mt-0.5 size-4 shrink-0 text-forest dark:text-success"
                          aria-hidden
                        />
                        <span className="text-muted-foreground">{f}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* COMMON QUESTIONS */}
        <section className="bg-muted">
          <div className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
            <p className="vl-eyebrow">Common questions</p>
            <h2 className="vl-h1 mt-3 text-foreground">Before you sign up.</h2>
            <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-2">
              {FAQ_ROW.map(([q, a]) => (
                <Card
                  key={q}
                  className="rounded-xl border border-border bg-card ring-0 vl-shadow-card"
                >
                  <CardContent className="p-6">
                    <div className="font-semibold text-foreground">{q}</div>
                    <div className="mt-2 text-sm leading-relaxed text-muted-foreground">
                      {a}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
