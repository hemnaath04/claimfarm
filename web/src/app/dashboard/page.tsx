"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { SiteHeader } from "@/components/marketing/site-header";
import {
  ApiKeySummary,
  IssuedApiKey,
  issueApiKey,
  listApiKeys,
  revokeApiKey,
} from "@/lib/api";

// NOTE: this dashboard is wired to placeholder data. When real auth lands,
// the org and user state should be fetched server-side from the FastAPI
// `/api/me` endpoint (TODO).

const ORG = {
  name: "Demo NGO",
  plan: "Pilot",
  utilization: 23, // claims this month
  cap: 100,
  webhookSecret: "whsec_•••••••••a91c",
};

const SCOPES = [
  { value: "claims:read", label: "Read claims" },
  { value: "claims:write", label: "Read + file claims" },
  { value: "admin", label: "Full admin" },
] as const;

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function ApiKeysPanel() {
  const [keys, setKeys] = useState<ApiKeySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [scope, setScope] = useState<string>("claims:read");
  const [issuing, setIssuing] = useState(false);
  const [justIssued, setJustIssued] = useState<IssuedApiKey | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setKeys(await listApiKeys());
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg === "unauthorized" ? "Sign in to manage API keys." : msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function handleIssue() {
    setIssuing(true);
    try {
      const issued = await issueApiKey(name.trim() || "untitled", scope);
      setJustIssued(issued);
      setName("");
      setScope("claims:read");
      toast.success("Key issued. Copy the secret now — it won't be shown again.");
      await reload();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to issue key");
    } finally {
      setIssuing(false);
    }
  }

  async function handleRevoke(keyId: string) {
    if (!confirm(`Revoke ${keyId}? Any integration using this key will break.`)) return;
    try {
      await revokeApiKey(keyId);
      toast.success("Key revoked");
      await reload();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Revoke failed");
    }
  }

  return (
    <Card className="glass">
      <CardContent className="p-6">
        <div className="flex items-baseline justify-between">
          <h3 className="font-semibold">API keys</h3>
          <span className="text-xs text-muted-foreground">
            Send <code className="font-mono">Authorization: Bearer cf_live_…</code> to the API.
          </span>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-12 gap-2">
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="What is this key for? (e.g. insurer integration)"
            className="bg-card/40 md:col-span-6"
          />
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value)}
            className="md:col-span-4 bg-card/40 border border-border/60 rounded-md px-3 text-sm h-9"
          >
            {SCOPES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
          <Button
            onClick={handleIssue}
            disabled={issuing}
            className="md:col-span-2 bg-primary text-primary-foreground hover:bg-primary/90"
          >
            {issuing ? "Issuing…" : "Issue key"}
          </Button>
        </div>

        {justIssued ? (
          <div className="mt-4 rounded-md border border-primary/40 bg-primary/5 p-4">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold">
                New key — copy now, it won&apos;t be shown again
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  navigator.clipboard.writeText(justIssued.secret);
                  toast.success("Secret copied to clipboard");
                }}
              >
                Copy
              </Button>
            </div>
            <code className="block mt-3 font-mono text-xs break-all bg-background/60 px-3 py-2 rounded-md">
              {justIssued.secret}
            </code>
            <div className="mt-2 text-xs text-muted-foreground">
              key id <span className="mono-id">{justIssued.key_id}</span> · scope{" "}
              <span className="mono-id">{justIssued.scope}</span>
            </div>
            <Button
              size="sm"
              variant="ghost"
              className="mt-3"
              onClick={() => setJustIssued(null)}
            >
              I&apos;ve copied it — dismiss
            </Button>
          </div>
        ) : null}

        <div className="mt-6">
          {loading ? (
            <div className="text-sm text-muted-foreground">Loading keys…</div>
          ) : error ? (
            <div className="text-sm text-amber-200">{error}</div>
          ) : keys.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              No API keys yet. Issue one above to start calling the ClaimFarm API.
            </div>
          ) : (
            <ul className="divide-y divide-border/40">
              {keys.map((k) => {
                const isRevoked = k.revoked_at !== null;
                return (
                  <li
                    key={k.key_id}
                    className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 py-3"
                  >
                    <div>
                      <div className="font-medium flex items-center gap-2">
                        {k.name || <span className="text-muted-foreground">untitled</span>}
                        <Badge variant="outline" className="text-xs">
                          {k.scope}
                        </Badge>
                        {isRevoked ? (
                          <Badge className="bg-red-500/10 border-red-500/40 text-red-200 text-xs">
                            revoked
                          </Badge>
                        ) : null}
                      </div>
                      <div className="text-xs text-muted-foreground mt-0.5 mono-id">
                        {k.key_id} · created {fmtDate(k.created_at)} · last used{" "}
                        {fmtDate(k.last_used_at)}
                      </div>
                    </div>
                    {!isRevoked ? (
                      <Button
                        size="sm"
                        variant="outline"
                        className="border-red-400/40 text-red-200 hover:bg-red-500/10"
                        onClick={() => handleRevoke(k.key_id)}
                      >
                        Revoke
                      </Button>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

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
            <ApiKeysPanel />

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
