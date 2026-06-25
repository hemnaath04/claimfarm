import type { Metadata } from "next";
import { Card, CardContent } from "@/components/ui/card";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";

export const metadata: Metadata = {
  title: "About · ClaimFarm",
  description: "Why ClaimFarm exists and the team building it.",
};

export default function AboutPage() {
  return (
    <>
      <SiteHeader />
      <main className="max-w-[820px] mx-auto px-6 pt-20 pb-16">
        <div className="text-xs font-semibold uppercase tracking-wider text-primary">About</div>
        <h1 className="mt-3 text-4xl md:text-5xl font-bold tracking-tight">
          We're building an insurance backbone for the world's smallholder farmers.
        </h1>
        <div className="mt-8 prose prose-invert max-w-none text-muted-foreground leading-relaxed">
          <p>
            There are roughly 500 million smallholder farmers worldwide. Most of
            them are locked out of the crop-insurance system that already exists —
            not because they don't qualify, but because the paperwork is in the
            wrong language, demands evidence they can't structure, and assumes
            literacy in domains they were never trained for. Less than 20% of
            eligible farmers ever file a claim after a loss.
          </p>
          <p>
            The agent stack we needed to fix this just arrived. Multimodal vision
            models that can identify crops and assess damage from a phone photo.
            Multilingual reasoning models that can talk to a farmer in Bengali or
            Swahili and reply in the same language. Vector stores that ground
            decisions in the agronomy literature and surface fraud patterns.
            ClaimFarm is what happens when you wire those pieces together with a
            human adjuster in the loop.
          </p>
          <p>
            Our north star: a farmer in rural India loses a third of her wheat to
            late-season hail, sends one photo over WhatsApp, and 24 hours later
            money lands in her bank account. No forms. No language barrier. No
            $10 lost on a bus ride to the insurance office.
          </p>
        </div>

        <section className="mt-16">
          <h2 className="text-xl font-bold">Principles</h2>
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-3">
            {[
              ["Humans in the loop, always", "Every approval has a human adjuster signing off. The model surfaces evidence; the human owns the decision."],
              ["Build for the worst phone", "WhatsApp / Telegram first. We assume 2G, low literacy, no app installs."],
              ["Show your work", "Every AI verdict comes with structured evidence (visible indicators, weather signals, retrieval context). No black boxes."],
              ["Privacy by default", "Personal photos and IDs are encrypted at rest. Signed URLs only. GDPR-ready data deletion."],
            ].map(([h, p]) => (
              <Card key={h} className="glass">
                <CardContent className="p-5">
                  <div className="font-semibold">{h}</div>
                  <div className="mt-2 text-sm text-muted-foreground">{p}</div>
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
