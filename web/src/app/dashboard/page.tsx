"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { SiteHeader } from "@/components/marketing/site-header";

// NOTE: this dashboard is wired to placeholder data. When real auth lands,
// the org and user state should be fetched server-side from the FastAPI
// `/api/me` endpoint (TODO).

const ORG = {
  name: "Demo NGO",
  plan: "Pilot",
  utilization: 23, // claims this month
  cap: 100,
  apiKey: "cf_live_pl_•••••••••3a7b",
  webhookSecret: "whsec_•••••••••a91c",
};

const TEAM = [
  { name: "Hemnaath B.", email: "you@org.org", role: "Owner" },
  { name: "Adjuster One", email: "adjuster1@org.org", role: "Reviewer" },
  { name: "Adjuster Two", email: "adjuster2@org.org", role: "Reviewer" },
];

const NOTIFICATION_PREFS = [
  { key: "new_claim", label: "New claim filed", desc: "When a claim is filed via WhatsApp / Telegram" },
  { key: "fraud_flag", label: "Fraud flag raised", desc: "Block-level fraud signal on any claim" },
  { key: "weekly_summary", label: "Weekly summary", desc: "Roundup every Monday morning" },
  { key: "billing", label: "Billing receipts", desc: "Invoices and payment receipts" },
];

export default function DashboardPage() {
  const [prefs, setPrefs] = useState<Record<string, boolean>>({
    new_claim: true,
    fraud_flag: true,
    weekly_summary: true,
    billing: true,
  });

  return (
    <>
      <SiteHeader />
      <main className="max-w-[1280px] mx-auto px-6 pt-10 pb-16">
        <div className="flex items-baseline justify-between">
          <div>
            <h1 className="text-2xl font-bold">{ORG.name}</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Plan <Badge variant="outline" className="ml-1">{ORG.plan}</Badge> · {ORG.utilization} of {ORG.cap} free claims used this month
            </p>
          </div>
          <Button variant="outline" onClick={() => (window.location.href = "/admin")}>
            Open adjuster console →
          </Button>
        </div>

        <Tabs defaultValue="overview" className="mt-8">
          <TabsList className="bg-transparent border border-border/60 p-1">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="billing">Billing</TabsTrigger>
            <TabsTrigger value="team">Team</TabsTrigger>
            <TabsTrigger value="api">API & webhooks</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4 mt-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <Card className="glass"><CardContent className="p-5">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Claims this month</div>
                <div className="text-2xl font-bold mt-1 tabular-nums">{ORG.utilization}</div>
                <div className="text-xs text-muted-foreground mt-1">of {ORG.cap} free</div>
              </CardContent></Card>
              <Card className="glass"><CardContent className="p-5">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Approved</div>
                <div className="text-2xl font-bold mt-1 tabular-nums">17</div>
                <div className="text-xs text-emerald-300 mt-1">74% approval rate</div>
              </CardContent></Card>
              <Card className="glass"><CardContent className="p-5">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Fraud flags</div>
                <div className="text-2xl font-bold mt-1 tabular-nums">2</div>
                <div className="text-xs text-amber-300 mt-1">8.7% of intake</div>
              </CardContent></Card>
              <Card className="glass"><CardContent className="p-5">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Avg time-to-decision</div>
                <div className="text-2xl font-bold mt-1 tabular-nums">38s</div>
                <div className="text-xs text-muted-foreground mt-1">photo → adjuster</div>
              </CardContent></Card>
            </div>

            <Card className="glass">
              <CardContent className="p-6">
                <h3 className="font-semibold">Recent activity</h3>
                <ul className="mt-4 space-y-2.5 text-sm">
                  <li className="flex items-center justify-between border-b border-border/40 pb-2.5">
                    <span><span className="mono-id mr-2">CF-9B710A9C85</span> filed via Telegram</span>
                    <span className="text-muted-foreground text-xs">2 min ago</span>
                  </li>
                  <li className="flex items-center justify-between border-b border-border/40 pb-2.5">
                    <span><span className="mono-id mr-2">CF-58E65714DA</span> approved</span>
                    <span className="text-muted-foreground text-xs">1h ago</span>
                  </li>
                  <li className="flex items-center justify-between border-b border-border/40 pb-2.5">
                    <span><span className="mono-id mr-2">CF-20D756C906</span> rejected (weather mismatch)</span>
                    <span className="text-muted-foreground text-xs">3h ago</span>
                  </li>
                  <li className="flex items-center justify-between">
                    <span>Adjuster One signed in</span>
                    <span className="text-muted-foreground text-xs">today</span>
                  </li>
                </ul>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="billing" className="space-y-4 mt-6">
            <Card className="glass">
              <CardContent className="p-6">
                <h3 className="font-semibold">Current plan</h3>
                <div className="mt-4 flex items-center justify-between">
                  <div>
                    <div className="text-2xl font-bold">Pilot · Free</div>
                    <div className="text-sm text-muted-foreground mt-1">
                      Up to 100 filed claims. {ORG.utilization} used, {ORG.cap - ORG.utilization} remaining.
                    </div>
                  </div>
                  <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
                    Upgrade to Growth
                  </Button>
                </div>
                <div className="mt-6 h-2 w-full rounded-full bg-muted/40 overflow-hidden">
                  <div
                    className="h-full bg-primary"
                    style={{ width: `${(ORG.utilization / ORG.cap) * 100}%` }}
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="glass">
              <CardContent className="p-6">
                <h3 className="font-semibold">Payment method</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  No payment method on file. You won&apos;t be charged unless you upgrade.
                </p>
                <Button variant="outline" className="mt-4" disabled>
                  Add payment method (provider portal — wire when `PAYMENTS_PROVIDER` is set)
                </Button>
              </CardContent>
            </Card>

            <Card className="glass">
              <CardContent className="p-6">
                <h3 className="font-semibold">Invoices</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  No invoices yet. They&apos;ll appear here once you upgrade.
                </p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="team" className="space-y-4 mt-6">
            <Card className="glass">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">Team members</h3>
                  <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
                    Invite member
                  </Button>
                </div>
                <ul className="mt-4 divide-y divide-border/40">
                  {TEAM.map((m) => (
                    <li key={m.email} className="flex items-center justify-between py-3">
                      <div>
                        <div className="font-medium">{m.name}</div>
                        <div className="text-xs text-muted-foreground">{m.email}</div>
                      </div>
                      <Badge variant="outline" className="text-xs">{m.role}</Badge>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="api" className="space-y-4 mt-6">
            <Card className="glass">
              <CardContent className="p-6">
                <h3 className="font-semibold">API key</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Use this key in the <code className="font-mono text-xs bg-muted/40 px-1.5 py-0.5 rounded">Authorization: Bearer</code> header when calling the ClaimFarm API.
                </p>
                <div className="mt-4 flex items-center gap-2">
                  <code className="flex-1 font-mono text-xs bg-muted/30 px-3 py-2 rounded-md">{ORG.apiKey}</code>
                  <Button variant="outline" onClick={() => toast.message("Reveal full key (TODO)")}>
                    Reveal
                  </Button>
                  <Button variant="outline" onClick={() => toast.success("New key generated (TODO)")}>
                    Rotate
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card className="glass">
              <CardContent className="p-6">
                <h3 className="font-semibold">Webhook endpoints</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  We&apos;ll POST signed events to these URLs when claims are filed,
                  approved, or rejected.
                </p>
                <div className="mt-4 space-y-2">
                  <Input defaultValue="https://your-insurer.example.com/intake" className="bg-card/40" />
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <div>
                      Signing secret:{" "}
                      <code className="font-mono">{ORG.webhookSecret}</code>
                    </div>
                    <Button size="sm" variant="outline">Add another</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="notifications" className="space-y-4 mt-6">
            <Card className="glass">
              <CardContent className="p-6">
                <h3 className="font-semibold">Notification preferences</h3>
                <ul className="mt-4 divide-y divide-border/40">
                  {NOTIFICATION_PREFS.map((n) => (
                    <li key={n.key} className="flex items-center justify-between py-3">
                      <div>
                        <div className="font-medium">{n.label}</div>
                        <div className="text-xs text-muted-foreground">{n.desc}</div>
                      </div>
                      <Switch
                        checked={prefs[n.key]}
                        onCheckedChange={(v) => setPrefs((p) => ({ ...p, [n.key]: v }))}
                      />
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="settings" className="space-y-4 mt-6">
            <Card className="glass">
              <CardContent className="p-6">
                <h3 className="font-semibold">Organisation settings</h3>
                <div className="mt-4 space-y-4">
                  <div>
                    <label className="text-xs uppercase tracking-wider text-muted-foreground">Organisation name</label>
                    <Input defaultValue={ORG.name} className="mt-1.5 bg-card/40 max-w-md" />
                  </div>
                  <div>
                    <label className="text-xs uppercase tracking-wider text-muted-foreground">Default region</label>
                    <Input defaultValue="ap-southeast-1 (Singapore)" className="mt-1.5 bg-card/40 max-w-md" />
                  </div>
                  <div>
                    <label className="text-xs uppercase tracking-wider text-muted-foreground">Time zone</label>
                    <Input defaultValue="UTC" className="mt-1.5 bg-card/40 max-w-md" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-red-500/30">
              <CardContent className="p-6">
                <h3 className="font-semibold text-red-300">Danger zone</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Delete your organisation. All claims, members and audit logs will be
                  permanently erased after the 30-day GDPR retention window.
                </p>
                <Button variant="outline" className="mt-4 border-red-400/40 text-red-200 hover:bg-red-500/10">
                  Delete organisation
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </>
  );
}
