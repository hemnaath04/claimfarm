import Link from "next/link";
import type { Metadata } from "next";
import {
  Camera,
  CloudSun,
  Search,
  ScanLine,
  Languages,
  UserCheck,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";
import { Reveal } from "@/components/motion/reveal";

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
    icon: ScanLine,
    title: "Multimodal damage assessment",
    body: "Qwen-VL-Max inspects the photo: identifies crop, classifies the damage (drought, flood, hail, pest, disease, frost, wind), scores severity and affected area, and returns structured evidence.",
  },
  {
    icon: CloudSun,
    title: "Weather corroboration",
    body: "Open-Meteo historical data is pulled for the farm's GPS and the photo's capture date; Qwen-Max judges whether the weather supports the visual verdict.",
  },
  {
    icon: Search,
    title: "Retrieval + fraud detection",
    body: "Qwen embeddings + Alibaba DashVector surface similar past claims and flag suspicious narrative reuse. Same-farmer near-duplicates are blocked at >0.93 cosine similarity.",
  },
  {
    icon: Camera,
    title: "Photo forensics",
    body: "EXIF capture time, GPS, camera make, edit-software fingerprint, plus a Qwen-VL authenticity check that flags watermarks, screenshots, and AI generations.",
  },
  {
    icon: Languages,
    title: "Multilingual replies",
    body: "Detects the farmer's language and replies in it. Hindi, Bengali, Swahili, Spanish, Portuguese, French, Arabic, Indonesian, Chinese, English on launch.",
  },
  {
    icon: UserCheck,
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

const TECH = [
  {
    name: "Qwen-VL-Max",
    body: "Multimodal damage assessment, photo authenticity verdict.",
  },
  {
    name: "Qwen-Max",
    body: "Weather corroboration, claim drafting, multilingual replies.",
  },
  {
    name: "text-embedding-v3",
    body: "RAG over past claims and agronomy KB; fraud similarity.",
  },
  {
    name: "Alibaba DashVector",
    body: "1024-dim cosine vector store for past claims + agronomy.",
  },
  {
    name: "Alibaba OSS",
    body: "Encrypted photo + PDF storage with signed URLs.",
  },
  {
    name: "Function Compute 3.0",
    body: "Serverless custom-container backend, public HTTPS trigger.",
  },
  {
    name: "Open-Meteo",
    body: "Historical weather archive for damage corroboration.",
  },
  {
    name: "WeasyPrint",
    body: "Polished PDF claim packets for insurer intake.",
  },
];

export default function LandingPage() {
  return (
    <div className="flex min-h-dvh flex-col">
      <SiteHeader />
      <main className="flex-1">
        {/* HERO */}
        <section className="vl-forest">
          <div className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
            <div className="max-w-3xl">
              <span
                className="vl-rise inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-medium text-white/90"
                style={{ animationDelay: "0ms" }}
              >
                <span className="size-1.5 rounded-full bg-harvest" aria-hidden />
                Track 4 finalist · Global AI Hackathon × Qwen Cloud
              </span>
              <h1
                className="vl-display vl-rise mt-6 text-white"
                style={{ animationDelay: "90ms" }}
              >
                Insurance claims for smallholder farmers, filed in 60 seconds.
              </h1>
              <p
                className="vl-rise mt-6 max-w-2xl text-lg leading-relaxed text-white/80"
                style={{ animationDelay: "180ms" }}
              >
                ClaimFarm turns a single WhatsApp or Telegram photo into a fully
                filed crop-insurance claim — multimodal AI damage assessment,
                weather corroboration, fraud detection, multilingual replies,
                human adjuster review. Built for the 500 million farmers locked
                out by paperwork.
              </p>
              <div
                className="vl-rise mt-8 flex flex-wrap items-center gap-3"
                style={{ animationDelay: "270ms" }}
              >
                <Button
                  render={<Link href="/auth/sign-up" />}
                  className="h-11 px-6 text-base"
                >
                  Start free <ArrowRight className="size-5" aria-hidden />
                </Button>
                <Button
                  render={<Link href="/admin" />}
                  variant="outline"
                  className="h-11 border-white/30 bg-transparent px-6 text-base text-white hover:bg-white/10 hover:text-white"
                >
                  See adjuster console
                </Button>
                <a
                  href="https://t.me/claimfarm_demo_bot"
                  target="_blank"
                  rel="noreferrer"
                  className="ml-1 inline-flex items-center gap-1 text-sm text-white/70 transition-colors hover:text-white"
                >
                  Try the demo bot <ArrowRight className="size-4" aria-hidden />
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* STATS */}
        <section className="border-b border-border bg-secondary">
          <div className="mx-auto max-w-[1200px] px-5 py-12 sm:px-8">
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              {STATS.map((s, i) => (
                <Reveal
                  key={s.label}
                  delay={i * 70}
                  className="rounded-xl border border-border bg-card p-6 vl-shadow-card vl-lift"
                >
                  <div className="text-3xl font-bold tabular-nums text-foreground">
                    {s.value}
                  </div>
                  <div className="mt-2 text-xs uppercase tracking-wider text-muted-foreground">
                    {s.label}
                  </div>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        {/* HOW IT WORKS */}
        <section className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
          <Reveal>
            <p className="vl-eyebrow">How it works</p>
            <h2 className="vl-h1 mt-3 text-foreground">
              Photo in. Filed claim out.
            </h2>
          </Reveal>
          <div className="mt-10 grid grid-cols-1 gap-4 md:grid-cols-4">
            {STEPS.map((step, i) => (
              <Reveal key={step.n} delay={i * 70}>
                <Card className="h-full rounded-xl border border-border bg-card ring-0 vl-shadow-card vl-lift">
                  <CardContent className="p-6">
                    <div className="text-sm font-bold tabular-nums text-forest dark:text-success">
                      {step.n}
                    </div>
                    <h3 className="mt-3 text-lg font-semibold text-foreground">
                      {step.title}
                    </h3>
                    <p className="mt-2 leading-relaxed text-muted-foreground">
                      {step.body}
                    </p>
                  </CardContent>
                </Card>
              </Reveal>
            ))}
          </div>
        </section>

        {/* FEATURES */}
        <section className="bg-muted">
          <div className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
            <Reveal>
              <p className="vl-eyebrow">What&apos;s inside</p>
              <h2 className="vl-h1 mt-3 text-foreground">
                Six AI checks before a single dollar moves.
              </h2>
            </Reveal>
            <div className="mt-10 grid grid-cols-1 gap-4 md:grid-cols-3">
              {FEATURES.map((f, i) => {
                const Icon = f.icon;
                return (
                  <Reveal key={f.title} delay={(i % 3) * 70}>
                    <Card className="h-full rounded-xl border border-border bg-card ring-0 vl-shadow-card vl-lift">
                      <CardContent className="p-6">
                        <span className="inline-grid size-10 place-items-center rounded-lg bg-forest/10 text-forest dark:bg-success/15 dark:text-success">
                          <Icon className="size-5" aria-hidden />
                        </span>
                        <h3 className="mt-4 text-lg font-semibold text-foreground">
                          {f.title}
                        </h3>
                        <p className="mt-2 leading-relaxed text-muted-foreground">
                          {f.body}
                        </p>
                      </CardContent>
                    </Card>
                  </Reveal>
                );
              })}
            </div>
          </div>
        </section>

        {/* TECH */}
        <section className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
          <Reveal className="rounded-3xl border border-border bg-card p-8 sm:p-12 vl-shadow-raised">
            <p className="vl-eyebrow">Built on</p>
            <h2 className="vl-h1 mt-3 text-foreground">
              Qwen Cloud + Alibaba Cloud, end to end.
            </h2>
            <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-4">
              {TECH.map((t) => (
                <div key={t.name} className="min-w-0">
                  <div className="font-medium text-foreground">{t.name}</div>
                  <div className="mt-1 text-sm text-muted-foreground">{t.body}</div>
                </div>
              ))}
            </div>
          </Reveal>
        </section>

        {/* CTA */}
        <section className="vl-forest">
          <div className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
            <Reveal className="mx-auto max-w-2xl text-center">
              <h2 className="vl-h1 text-white">
                Stop losing claims to paperwork.
              </h2>
              <p className="mt-4 text-lg leading-relaxed text-white/80">
                Smallholder farmers don&apos;t need an app — they have WhatsApp.
                Plug ClaimFarm in and your insurer intake speaks photo.
              </p>
              <div className="mt-8 flex flex-wrap justify-center gap-3">
                <Button
                  render={<Link href="/auth/sign-up" />}
                  className="h-11 px-6 text-base"
                >
                  Start free <ArrowRight className="size-5" aria-hidden />
                </Button>
                <Button
                  render={<Link href="/contact" />}
                  variant="outline"
                  className="h-11 border-white/30 bg-transparent px-6 text-base text-white hover:bg-white/10 hover:text-white"
                >
                  Talk to us
                </Button>
              </div>
            </Reveal>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
