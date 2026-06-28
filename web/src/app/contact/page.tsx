import type { Metadata } from "next";
import { Mail, Send, Code2, ArrowUpRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";

export const metadata: Metadata = { title: "Contact · ClaimFarm" };

export default function ContactPage() {
  return (
    <div className="flex min-h-dvh flex-col">
      <SiteHeader />
      <main className="flex-1">
        <section className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
          <div className="grid grid-cols-1 gap-10 lg:grid-cols-2 lg:gap-16">
            {/* Left: intro + contact channels */}
            <div className="min-w-0">
              <p className="vl-eyebrow">Contact</p>
              <h1 className="vl-h1 mt-3">Let&apos;s talk.</h1>
              <p className="mt-5 max-w-prose text-lg leading-7 text-muted-foreground">
                Whether you&apos;re an insurer, an NGO, or a developer kicking the
                tires, tell us what you&apos;re trying to ship. The fastest way to
                see ClaimFarm is to message the demo bot.
              </p>

              <div className="mt-8 space-y-3">
                <a
                  href="https://t.me/claimfarm_demo_bot"
                  target="_blank"
                  rel="noreferrer"
                  className="group flex items-start gap-4 rounded-xl border border-border bg-card p-5 vl-shadow-card transition-shadow hover:vl-shadow-raised"
                >
                  <span
                    aria-hidden
                    className="mt-0.5 inline-grid size-10 shrink-0 place-items-center rounded-lg bg-forest/10 text-forest"
                  >
                    <Send className="size-5" />
                  </span>
                  <span className="min-w-0">
                    <span className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Demo bot
                    </span>
                    <span className="mt-0.5 block font-semibold text-card-foreground break-words">
                      @claimfarm_demo_bot
                    </span>
                    <span className="mt-1 inline-flex items-center gap-1 text-sm font-medium text-forest">
                      Open on Telegram
                      <ArrowUpRight aria-hidden className="size-4" />
                    </span>
                  </span>
                </a>

                <a
                  href="https://github.com/hemnaath04/claimfarm"
                  target="_blank"
                  rel="noreferrer"
                  className="group flex items-start gap-4 rounded-xl border border-border bg-card p-5 vl-shadow-card transition-shadow hover:vl-shadow-raised"
                >
                  <span
                    aria-hidden
                    className="mt-0.5 inline-grid size-10 shrink-0 place-items-center rounded-lg bg-forest/10 text-forest"
                  >
                    <Code2 className="size-5" aria-hidden />
                  </span>
                  <span className="min-w-0">
                    <span className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Source
                    </span>
                    <span className="mt-0.5 block font-semibold text-card-foreground break-words">
                      github.com/hemnaath04/claimfarm
                    </span>
                    <span className="mt-1 inline-flex items-center gap-1 text-sm font-medium text-forest">
                      View repository
                      <ArrowUpRight aria-hidden className="size-4" />
                    </span>
                  </span>
                </a>

                <div className="rounded-xl border border-border bg-card p-5 vl-shadow-card">
                  <div className="flex items-start gap-4">
                    <span
                      aria-hidden
                      className="mt-0.5 inline-grid size-10 shrink-0 place-items-center rounded-lg bg-forest/10 text-forest"
                    >
                      <Mail className="size-5" />
                    </span>
                    <div className="min-w-0">
                      <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Sales
                      </div>
                      <a
                        href="mailto:sales@claimfarm.dev"
                        className="mt-0.5 block font-medium text-card-foreground break-words hover:text-forest"
                      >
                        sales@claimfarm.dev
                      </a>
                      <div className="mt-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Support
                      </div>
                      <a
                        href="mailto:help@claimfarm.dev"
                        className="mt-0.5 block font-medium text-card-foreground break-words hover:text-forest"
                      >
                        help@claimfarm.dev
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right: form */}
            <div className="min-w-0">
              <Card className="rounded-3xl border border-border bg-card vl-shadow-card">
                <CardContent className="p-6 sm:p-8">
                  {/* Placeholder form — POSTs to /api/contact (mock) */}
                  <form action="/api/contact" method="post" className="space-y-5">
                    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                      <div className="space-y-1.5">
                        <label htmlFor="name" className="text-sm font-medium text-foreground">
                          Name
                        </label>
                        <Input
                          id="name"
                          name="name"
                          required
                          autoComplete="name"
                          placeholder="Your name"
                          className="h-11"
                        />
                      </div>
                      <div className="space-y-1.5">
                        <label htmlFor="email" className="text-sm font-medium text-foreground">
                          Email
                        </label>
                        <Input
                          id="email"
                          name="email"
                          type="email"
                          required
                          autoComplete="email"
                          placeholder="you@example.com"
                          className="h-11"
                        />
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      <label htmlFor="org" className="text-sm font-medium text-foreground">
                        Organisation
                      </label>
                      <Input
                        id="org"
                        name="org"
                        placeholder="Your insurer / NGO"
                        className="h-11"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label htmlFor="message" className="text-sm font-medium text-foreground">
                        How can we help?
                      </label>
                      <Textarea
                        id="message"
                        name="message"
                        rows={6}
                        required
                        placeholder="What are you trying to ship?"
                      />
                    </div>
                    <Button type="submit" className="h-11 w-full px-6 text-base sm:w-auto">
                      Send message
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
