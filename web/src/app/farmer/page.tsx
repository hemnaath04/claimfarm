import Link from "next/link";
import type { Metadata } from "next";
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
    icon: "📷",
    title: "Take a photo",
    body: "Walk to the damaged part of the field. Take a photo with your phone — close enough to see the crop and the damage clearly.",
  },
  {
    icon: "💬",
    title: "Send it to ClaimFarm",
    body: "On WhatsApp or Telegram, send the photo to the ClaimFarm number. Add a short note in your own language describing what happened.",
  },
  {
    icon: "📍",
    title: "Share your location",
    body: "Tap the location button so we know which field this is. We use it to check the weather record for that day.",
  },
  {
    icon: "✅",
    title: "Get a reply",
    body: "Within a minute, you'll get a reply in your language with your claim number. An adjuster will review and decide soon after.",
  },
];

export default function FarmerPage() {
  return (
    <>
      <SiteHeader />
      <main className="max-w-[1100px] mx-auto px-6 pt-20 pb-16">
        <div className="text-xs font-semibold uppercase tracking-wider text-primary">
          For farmers
        </div>
        <h1 className="mt-3 text-4xl md:text-6xl font-bold tracking-tight">
          One photo. <span className="neon-text">One claim.</span>
        </h1>
        <p className="mt-5 text-lg text-muted-foreground max-w-2xl">
          You don&apos;t need an app. You don&apos;t need to fill out a form. You
          don&apos;t need to take a bus to the insurance office. Just send us a
          photo on WhatsApp or Telegram, and we&apos;ll file the claim for you.
        </p>

        <div className="mt-10 flex flex-wrap gap-3">
          <a
            href="https://t.me/claimfarm_demo_bot"
            target="_blank"
            rel="noreferrer"
          >
            <Button className="bg-primary text-primary-foreground hover:bg-primary/90 text-base h-11 px-6">
              Try the Telegram bot →
            </Button>
          </a>
          <Link href="/contact">
            <Button variant="outline" className="text-base h-11 px-6">
              Ask my insurer to enable this
            </Button>
          </Link>
        </div>

        <section className="mt-20">
          <h2 className="text-2xl font-bold">How it works</h2>
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
            {STEPS.map((s, i) => (
              <Card key={i} className="glass">
                <CardContent className="p-6 flex gap-4">
                  <div className="text-3xl shrink-0">{s.icon}</div>
                  <div>
                    <h3 className="font-semibold">{s.title}</h3>
                    <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
                      {s.body}
                    </p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <section className="mt-20">
          <h2 className="text-2xl font-bold">What we ask you to do — for trust</h2>
          <p className="mt-2 text-muted-foreground">
            We need to be sure the photo really comes from you, in your field,
            on the day you said. So we ask a few short questions when you first
            sign up. None of this leaves our system.
          </p>
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
            <Card className="glass">
              <CardContent className="p-5">
                <div className="text-foreground font-medium">Take a selfie</div>
                <div className="mt-1 text-muted-foreground">
                  A quick selfie helps us match you to your government ID. We
                  ask you to turn your head left, then right.
                </div>
              </CardContent>
            </Card>
            <Card className="glass">
              <CardContent className="p-5">
                <div className="text-foreground font-medium">Show your ID</div>
                <div className="mt-1 text-muted-foreground">
                  Driver license, passport, or national ID — any of them work.
                  We only use it to verify your identity.
                </div>
              </CardContent>
            </Card>
            <Card className="glass">
              <CardContent className="p-5">
                <div className="text-foreground font-medium">Take the photo live</div>
                <div className="mt-1 text-muted-foreground">
                  We ask you to take the crop photo using your phone&apos;s
                  camera right then, not from your gallery, so we know it&apos;s
                  fresh.
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="mt-20">
          <h2 className="text-2xl font-bold">Languages we speak today</h2>
          <p className="mt-2 text-muted-foreground">
            Write to us in your own language. The bot replies in the same one.
          </p>
          <div className="mt-6 flex flex-wrap gap-2 text-sm">
            {[
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
            ].map((l) => (
              <span
                key={l}
                className="px-3 py-1.5 rounded-full border border-border/60 bg-muted/30"
              >
                {l}
              </span>
            ))}
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
