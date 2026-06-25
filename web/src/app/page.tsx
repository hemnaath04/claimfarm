import Link from "next/link";
import type { Metadata } from "next";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";

export const metadata: Metadata = {
  title: "ClaimFarm · Insurance claims via one photo for 500M farmers",
  description:
    "ClaimFarm turns a smallholder farmer's WhatsApp or Telegram photo into a filed crop insurance claim in 60 seconds. Multimodal Qwen-VL damage assessment, weather corroboration, fraud detection, multilingual replies, human-in-the-loop adjuster review.",
};

const STATS = [
  { value: "500M", label: "smallholder farmers globally" },
  { value: "< 20%", label: "ever file an insurance claim" },
  { value: "10+", label: "languages supported on day one" },
  { value: "60s", label: "from photo to filed claim" },
];

const FEATURES = [
  {
    title: "Multimodal damage assessment",
    body: "Qwen-VL-Max inspects the photo: identifies crop, classifies the damage (drought, flood, hail, pest, disease, frost, wind), scores severity and affected area, and returns structured evidence.",
  },
  {
    title: "Weather corroboration",
    body: "Open-Meteo historical data is pulled for the farm's GPS and the photo's capture date; Qwen-Max judges whether the weather supports the visual verdict.",
  },
  {
    title: "Retrieval + fraud detection",
    body: "Qwen embeddings + Alibaba DashVector surface similar past claims and flag suspicious narrative reuse. Same-farmer near-duplicates are blocked at >0.93 cosine similarity.",
  },
  {
    title: "Photo forensics",
    body: "EXIF capture time, GPS, camera make, edit-software fingerprint, plus a Qwen-VL authenticity check that flags watermarks, screenshots, and AI generations.",
  },
  {
    title: "Multilingual replies",
    body: "Detects the farmer's language and replies in it. Hindi, Bengali, Swahili, Spanish, Portuguese, French, Arabic, Indonesian, Chinese, English on launch.",
  },
  {
    title: "Human-in-the-loop review",
    body: "Every claim lands in an adjuster console with the AI verdict, evidence, similar past claims, and risk flags. One click submits to the insurer.",
  },
];

const STEPS = [
  {
    n: "01",
    title: "Farmer sends a photo",
    body: "From WhatsApp or Telegram. Plus a short caption in their own language. No app to install.",
  },
  {
    n: "02",
    title: "AI assesses damage",
    body: "Qwen-VL identifies the crop and damage. Open-Meteo corroborates against the weather record.",
  },
  {
    n: "03",
    title: "Adjuster reviews",
    body: "ClaimFarm's console surfaces the AI verdict, similar past claims, and any fraud flags side-by-side.",
  },
  {
    n: "04",
    title: "Insurer receives a clean claim",
    body: "A pre-filled PDF claim, evidence-stamped, lands in the insurer's intake — ready to pay out.",
  },
];

export default function LandingPage() {
  return (
    <>
      <SiteHeader />
      <main>
        {/* HERO */}
        <section className="max-w-[1280px] mx-auto px-6 pt-20 pb-16">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border border-primary/30 bg-primary/5 text-primary">
              <span className="size-1.5 rounded-full bg-primary animate-pulse" />
              Track 4 finalist · Global AI Hackathon × Qwen Cloud
            </div>
            <h1 className="mt-6 text-5xl md:text-7xl font-bold tracking-tight leading-[1.05]">
              Insurance claims for{" "}
              <span className="neon-text">smallholder farmers</span>,<br />
              filed in 60 seconds.
            </h1>
            <p className="mt-6 text-lg text-muted-foreground max-w-2xl">
              ClaimFarm turns a single WhatsApp or Telegram photo into a fully filed
              crop-insurance claim — multimodal AI damage assessment, weather
              corroboration, fraud detection, multilingual replies, human adjuster
              review. Built for the 500 million farmers locked out by paperwork.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link href="/auth/sign-up">
                <Button className="bg-primary text-primary-foreground hover:bg-primary/90 text-base h-11 px-6">
                  Start free →
                </Button>
              </Link>
              <Link href="/admin">
                <Button variant="outline" className="text-base h-11 px-6">
                  See adjuster console
                </Button>
              </Link>
              <a
                href="https://t.me/claimfarm_demo_bot"
                target="_blank"
                rel="noreferrer"
                className="text-sm text-muted-foreground hover:text-foreground ml-2"
              >
                Try the demo bot →
              </a>
            </div>
          </div>
        </section>

        {/* STATS */}
        <section className="max-w-[1280px] mx-auto px-6 mt-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {STATS.map((s) => (
              <div key={s.label} className="glass rounded-2xl px-6 py-5">
                <div className="text-3xl font-bold tabular-nums">{s.value}</div>
                <div className="text-xs text-muted-foreground mt-1 uppercase tracking-wider">
                  {s.label}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* HOW IT WORKS */}
        <section className="max-w-[1280px] mx-auto px-6 mt-32">
          <div className="text-xs font-semibold uppercase tracking-wider text-primary">
            How it works
          </div>
          <h2 className="mt-3 text-3xl md:text-4xl font-bold tracking-tight">
            Photo in. Filed claim out.
          </h2>
          <div className="mt-10 grid grid-cols-1 md:grid-cols-4 gap-4">
            {STEPS.map((step) => (
              <Card key={step.n} className="glass">
                <CardContent className="p-6">
                  <div className="text-primary text-sm font-bold mono-id">{step.n}</div>
                  <h3 className="mt-3 font-semibold text-lg">{step.title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                    {step.body}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* FEATURES */}
        <section className="max-w-[1280px] mx-auto px-6 mt-32">
          <div className="text-xs font-semibold uppercase tracking-wider text-primary">
            What's inside
          </div>
          <h2 className="mt-3 text-3xl md:text-4xl font-bold tracking-tight">
            Six AI checks before a single dollar moves.
          </h2>
          <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-4">
            {FEATURES.map((f) => (
              <Card key={f.title} className="glass">
                <CardContent className="p-6">
                  <h3 className="font-semibold">{f.title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                    {f.body}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* TECH */}
        <section className="max-w-[1280px] mx-auto px-6 mt-32">
          <div className="glass rounded-3xl p-10 md:p-14">
            <div className="text-xs font-semibold uppercase tracking-wider text-primary">
              Built on
            </div>
            <h2 className="mt-3 text-3xl md:text-4xl font-bold tracking-tight">
              Qwen Cloud + Alibaba Cloud, end to end.
            </h2>
            <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-6 text-sm">
              <div>
                <div className="text-foreground font-medium">Qwen-VL-Max</div>
                <div className="text-muted-foreground mt-1">
                  Multimodal damage assessment, photo authenticity verdict.
                </div>
              </div>
              <div>
                <div className="text-foreground font-medium">Qwen-Max</div>
                <div className="text-muted-foreground mt-1">
                  Weather corroboration, claim drafting, multilingual replies.
                </div>
              </div>
              <div>
                <div className="text-foreground font-medium">text-embedding-v3</div>
                <div className="text-muted-foreground mt-1">
                  RAG over past claims and agronomy KB; fraud similarity.
                </div>
              </div>
              <div>
                <div className="text-foreground font-medium">Alibaba DashVector</div>
                <div className="text-muted-foreground mt-1">
                  1024-dim cosine vector store for past claims + agronomy.
                </div>
              </div>
              <div>
                <div className="text-foreground font-medium">Alibaba OSS</div>
                <div className="text-muted-foreground mt-1">
                  Encrypted photo + PDF storage with signed URLs.
                </div>
              </div>
              <div>
                <div className="text-foreground font-medium">Function Compute 3.0</div>
                <div className="text-muted-foreground mt-1">
                  Serverless custom-container backend, public HTTPS trigger.
                </div>
              </div>
              <div>
                <div className="text-foreground font-medium">Open-Meteo</div>
                <div className="text-muted-foreground mt-1">
                  Historical weather archive for damage corroboration.
                </div>
              </div>
              <div>
                <div className="text-foreground font-medium">WeasyPrint</div>
                <div className="text-muted-foreground mt-1">
                  Polished PDF claim packets for insurer intake.
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="max-w-[1280px] mx-auto px-6 mt-32">
          <div className="text-center max-w-2xl mx-auto">
            <h2 className="text-3xl md:text-5xl font-bold tracking-tight">
              Stop losing claims to paperwork.
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Smallholder farmers don't need an app — they have WhatsApp. Plug
              ClaimFarm in and your insurer intake speaks photo.
            </p>
            <div className="mt-8 flex justify-center gap-3 flex-wrap">
              <Link href="/auth/sign-up">
                <Button className="bg-primary text-primary-foreground hover:bg-primary/90 text-base h-11 px-6">
                  Start free →
                </Button>
              </Link>
              <Link href="/contact">
                <Button variant="outline" className="text-base h-11 px-6">
                  Talk to us
                </Button>
              </Link>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
