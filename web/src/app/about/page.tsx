import type { Metadata } from "next";
import { Users, Smartphone, Eye, ShieldCheck } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";

export const metadata: Metadata = {
  title: "About · ClaimFarm",
  description:
    "ClaimFarm exists because 500 million smallholder farmers are locked out of crop insurance by paperwork. We build AI-first claims infrastructure so a single photo is enough.",
};

const PRINCIPLES = [
  {
    icon: Users,
    title: "Humans in the loop, always",
    body: "Every approval has a human adjuster signing off. The model surfaces evidence; the human owns the decision.",
  },
  {
    icon: Smartphone,
    title: "Build for the worst phone",
    body: "WhatsApp / Telegram first. We assume 2G, low literacy, no app installs.",
  },
  {
    icon: Eye,
    title: "Show your work",
    body: "Every AI verdict comes with structured evidence (visible indicators, weather signals, retrieval context). No black boxes.",
  },
  {
    icon: ShieldCheck,
    title: "Privacy by default",
    body: "Personal photos and IDs are encrypted at rest. Signed URLs only. GDPR-ready data deletion.",
  },
];

export default function AboutPage() {
  return (
    <div className="flex min-h-dvh flex-col">
      <SiteHeader />
      <main className="flex-1">
        {/* HERO */}
        <section className="vl-forest">
          <div className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
            <div className="max-w-3xl vl-fade-up">
              <p className="vl-eyebrow text-harvest dark:text-harvest">About</p>
              <h1 className="vl-display mt-3 text-white">
                We&apos;re building an insurance backbone for the world&apos;s
                smallholder farmers.
              </h1>
            </div>
          </div>
        </section>

        {/* STORY */}
        <section className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
          <div className="max-w-[820px] space-y-6 text-lg leading-relaxed text-muted-foreground">
            <p>
              There are roughly 500 million smallholder farmers worldwide. Most
              of them are locked out of the crop-insurance system that already
              exists — not because they don&apos;t qualify, but because the
              paperwork is in the wrong language, demands evidence they can&apos;t
              structure, and assumes literacy in domains they were never trained
              for. Less than 20% of eligible farmers ever file a claim after a
              loss.
            </p>
            <p>
              The agent stack we needed to fix this just arrived. Multimodal
              vision models that can identify crops and assess damage from a
              phone photo. Multilingual reasoning models that can talk to a
              farmer in Bengali or Swahili and reply in the same language. Vector
              stores that ground decisions in the agronomy literature and surface
              fraud patterns. ClaimFarm is what happens when you wire those
              pieces together with a human adjuster in the loop.
            </p>
            <p>
              Our north star: a farmer in rural India loses a third of her wheat
              to late-season hail, sends one photo over WhatsApp, and 24 hours
              later money lands in her bank account. No forms. No language
              barrier. No $10 lost on a bus ride to the insurance office.
            </p>
          </div>
        </section>

        {/* PRINCIPLES */}
        <section className="bg-muted">
          <div className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
            <p className="vl-eyebrow">Principles</p>
            <h2 className="vl-h1 mt-3 text-foreground">How we build.</h2>
            <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-2">
              {PRINCIPLES.map((p) => {
                const Icon = p.icon;
                return (
                  <Card
                    key={p.title}
                    className="rounded-xl border border-border bg-card ring-0 vl-shadow-card"
                  >
                    <CardContent className="p-6">
                      <span className="inline-grid size-10 place-items-center rounded-lg bg-forest/10 text-forest dark:bg-success/15 dark:text-success">
                        <Icon className="size-5" aria-hidden />
                      </span>
                      <div className="mt-4 font-semibold text-foreground">
                        {p.title}
                      </div>
                      <div className="mt-2 text-sm leading-relaxed text-muted-foreground">
                        {p.body}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
