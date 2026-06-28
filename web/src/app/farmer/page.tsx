import Link from "next/link";
import type { Metadata } from "next";
import { Camera, MessageCircle, MapPin, CheckCircle2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";

export const metadata: Metadata = {
  title: "For farmers · ClaimFarm",
  description: "How to file a crop insurance claim with one photo on WhatsApp or Telegram.",
};

const STEPS = [
  {
    Icon: Camera,
    title: "Take a photo",
    body: "Walk to the damaged part of the field. Take a photo with your phone — close enough to see the crop and the damage clearly.",
  },
  {
    Icon: MessageCircle,
    title: "Send it to ClaimFarm",
    body: "On WhatsApp or Telegram, send the photo to the ClaimFarm number. Add a short note in your own language describing what happened.",
  },
  {
    Icon: MapPin,
    title: "Share your location",
    body: "Tap the location button so we know which field this is. We use it to check the weather record for that day.",
  },
  {
    Icon: CheckCircle2,
    title: "Get a reply",
    body: "Within a minute, you'll get a reply in your language with your claim number. An adjuster will review and decide soon after.",
  },
];

const TRUST = [
  {
    title: "Take a selfie",
    body: "A quick selfie helps us match you to your government ID. We ask you to turn your head left, then right.",
  },
  {
    title: "Show your ID",
    body: "Driver license, passport, or national ID — any of them work. We only use it to verify your identity.",
  },
  {
    title: "Take the photo live",
    body: "We ask you to take the crop photo using your phone's camera right then, not from your gallery, so we know it's fresh.",
  },
];

const LANGUAGES = [
  "English",
  "हिन्दी",
  "বাংলা",
  "Kiswahili",
  "Español",
  "Português",
  "Français",
  "العربية",
  "中文",
  "Bahasa Indonesia",
];

export default function FarmerPage() {
  return (
    <div className="flex min-h-dvh flex-col">
      <SiteHeader />
      <main className="flex-1">
        {/* Harvest-yellow hero */}
        <section className="vl-harvest">
          <div className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
            <p className="vl-eyebrow text-forest-deep">For farmers</p>
            <h1 className="vl-display mt-3 max-w-3xl text-forest-deep">
              One photo. One claim. No paperwork.
            </h1>
            <p className="mt-6 max-w-2xl text-xl leading-8 text-forest-deep/85">
              You don&apos;t need an app. You don&apos;t need to fill out a form. You
              don&apos;t need to take a bus to the insurance office. Just send us a
              photo on WhatsApp or Telegram, and we&apos;ll file the claim for you.
            </p>

            <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
              <a
                href="https://t.me/claimfarm_demo_bot"
                target="_blank"
                rel="noreferrer"
                className="inline-flex h-12 items-center justify-center rounded-lg bg-forest px-7 text-base font-semibold text-ivory transition-colors hover:bg-forest-deep"
              >
                Open the demo bot
              </a>
              <Link
                href="/contact"
                className="inline-flex h-12 items-center justify-center rounded-lg border border-forest-deep/30 bg-transparent px-7 text-base font-semibold text-forest-deep transition-colors hover:bg-forest-deep/5"
              >
                Ask my insurer to enable this
              </Link>
            </div>
          </div>
        </section>

        {/* How it works — numbered cards */}
        <section className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
          <p className="vl-eyebrow">Step by step</p>
          <h2 className="vl-h1 mt-3">How it works</h2>
          <div className="mt-10 grid grid-cols-1 gap-5 sm:grid-cols-2">
            {STEPS.map((s, i) => {
              const Icon = s.Icon;
              return (
                <Card
                  key={s.title}
                  className="border border-border bg-card vl-shadow-card"
                >
                  <CardContent className="flex gap-5 p-6 sm:p-7">
                    <div className="shrink-0 text-2xl font-bold tabular-nums text-harvest">
                      {String(i + 1).padStart(2, "0")}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <Icon aria-hidden className="size-5 text-forest" />
                        <h3 className="text-xl font-semibold text-card-foreground">
                          {s.title}
                        </h3>
                      </div>
                      <p className="mt-2 text-base leading-7 text-muted-foreground">
                        {s.body}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </section>

        {/* Trust steps */}
        <section className="bg-muted/40">
          <div className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
            <p className="vl-eyebrow">Trust</p>
            <h2 className="vl-h1 mt-3 max-w-2xl">
              What we ask you to do — for trust
            </h2>
            <p className="mt-4 max-w-2xl text-lg leading-7 text-muted-foreground">
              We need to be sure the photo really comes from you, in your field,
              on the day you said. So we ask a few short questions when you first
              sign up. None of this leaves our system.
            </p>
            <div className="mt-10 grid grid-cols-1 gap-5 md:grid-cols-3">
              {TRUST.map((t) => (
                <Card
                  key={t.title}
                  className="border border-border bg-card vl-shadow-card"
                >
                  <CardContent className="p-6">
                    <div className="text-lg font-semibold text-card-foreground">
                      {t.title}
                    </div>
                    <p className="mt-2 text-base leading-7 text-muted-foreground">
                      {t.body}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Languages */}
        <section className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
          <p className="vl-eyebrow">Languages</p>
          <h2 className="vl-h1 mt-3">Languages we speak today</h2>
          <p className="mt-4 max-w-2xl text-lg leading-7 text-muted-foreground">
            Write to us in your own language. The bot replies in the same one.
          </p>
          <ul className="mt-8 flex flex-wrap gap-2.5">
            {LANGUAGES.map((l) => (
              <li
                key={l}
                className="rounded-full border border-border bg-secondary px-4 py-2 text-base font-medium text-foreground"
              >
                {l}
              </li>
            ))}
          </ul>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
