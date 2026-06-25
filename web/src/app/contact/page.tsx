import type { Metadata } from "next";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";

export const metadata: Metadata = { title: "Contact · ClaimFarm" };

export default function ContactPage() {
  return (
    <>
      <SiteHeader />
      <main className="max-w-[1100px] mx-auto px-6 pt-20 pb-16">
        <div className="text-xs font-semibold uppercase tracking-wider text-primary">Contact</div>
        <h1 className="mt-3 text-4xl md:text-5xl font-bold tracking-tight">
          Let's talk.
        </h1>

        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2">
            <Card className="glass">
              <CardContent className="p-7">
                {/* Placeholder form — POSTs to /api/contact (mock) */}
                <form
                  action="/api/contact"
                  method="post"
                  className="space-y-4"
                >
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs uppercase tracking-wider text-muted-foreground">Name</label>
                      <Input name="name" placeholder="Your name" className="mt-1.5 bg-card/40" />
                    </div>
                    <div>
                      <label className="text-xs uppercase tracking-wider text-muted-foreground">Email</label>
                      <Input name="email" type="email" placeholder="you@example.com" className="mt-1.5 bg-card/40" />
                    </div>
                  </div>
                  <div>
                    <label className="text-xs uppercase tracking-wider text-muted-foreground">Organisation</label>
                    <Input name="org" placeholder="Your insurer / NGO" className="mt-1.5 bg-card/40" />
                  </div>
                  <div>
                    <label className="text-xs uppercase tracking-wider text-muted-foreground">How can we help?</label>
                    <Textarea name="message" rows={6} placeholder="What are you trying to ship?" className="mt-1.5 bg-card/40" />
                  </div>
                  <Button
                    type="submit"
                    className="bg-primary text-primary-foreground hover:bg-primary/90"
                  >
                    Send message →
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-4">
            <Card className="glass">
              <CardContent className="p-5">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">
                  Demo bot
                </div>
                <div className="mt-1 font-semibold">@claimfarm_demo_bot</div>
                <a
                  href="https://t.me/claimfarm_demo_bot"
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-block text-sm text-primary hover:underline"
                >
                  Open on Telegram →
                </a>
              </CardContent>
            </Card>

            <Card className="glass">
              <CardContent className="p-5">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">
                  Source
                </div>
                <div className="mt-1 font-semibold">github.com/hemnaath04/claimfarm</div>
                <a
                  href="https://github.com/hemnaath04/claimfarm"
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-block text-sm text-primary hover:underline"
                >
                  View repository →
                </a>
              </CardContent>
            </Card>

            <Card className="glass">
              <CardContent className="p-5">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">
                  Sales
                </div>
                <div className="mt-1 font-mono text-sm">sales@claimfarm.dev</div>
                <div className="mt-3 text-xs uppercase tracking-wider text-muted-foreground">
                  Support
                </div>
                <div className="mt-1 font-mono text-sm">help@claimfarm.dev</div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
