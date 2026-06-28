"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { Copy, KeyRound, Trash2 } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Button, buttonVariants } from "@/components/ui/button";
import { StatusBadge, type StatusTone } from "@/components/ui/status-badge";
import { AppShell } from "@/components/app/app-shell";
import { cn } from "@/lib/utils";
import {
  ApiKeySummary,
  IssuedApiKey,
  issueApiKey,
  listApiKeys,
  revokeApiKey,
} from "@/lib/api";

const ORG = {
  name: "Demo NGO",
  plan: "Pilot",
  utilization: 23,
  cap: 100,
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

function Panel({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-card p-5 vl-shadow-card",
        className
      )}
    >
      {children}
    </div>
  );
}

function Stat({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: string | number;
  hint?: string;
  tone?: "default" | "good" | "warn";
}) {
  const hintColor =
    tone === "good"
      ? "text-success"
      : tone === "warn"
        ? "text-harvest-deep"
        : "text-muted-foreground";
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
      <div className="mt-1.5 text-3xl font-bold tabular-nums text-foreground">
        {value}
      </div>
      {hint ? <div className={`mt-1 text-xs ${hintColor}`}>{hint}</div> : null}
    </div>
  );
}

const inputCls =
  "h-10 w-full rounded-lg border border-border bg-card px-3 text-sm text-foreground placeholder:text-muted-foreground focus-visible:border-ring focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50";

export default function DashboardPage() {
  const [prefs, setPrefs] = useState<Record<string, boolean>>({
    new_claim: true,
    fraud_flag: true,
    weekly_summary: true,
    billing: true,
  });

  return (
    <AppShell>
      <div className="mx-auto max-w-[1320px] px-5 pb-16 pt-8 sm:px-8">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="vl-eyebrow">Workspace</p>
            <h1 className="mt-1.5 text-3xl font-bold tracking-tight text-foreground">
              Good morning, {ORG.name}
            </h1>
            <p className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted-foreground">
              <StatusBadge tone="success">{ORG.plan}</StatusBadge>
              <span>
                {ORG.utilization} of {ORG.cap} free claims this month
              </span>
            </p>
          </div>
          <Link
            href="/admin"
            className={cn(buttonVariants({ variant: "outline" }), "h-10 px-4")}
          >
            Open adjuster console →
          </Link>
        </div>

        <Tabs defaultValue="overview" className="mt-8">
          <TabsList className="flex w-full flex-wrap gap-1 rounded-xl border border-border bg-card p-1">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="billing">Billing</TabsTrigger>
            <TabsTrigger value="team">Team</TabsTrigger>
            <TabsTrigger value="api">API &amp; webhooks</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6 space-y-4">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Stat label="Claims this month" value={ORG.utilization} hint={`of ${ORG.cap} free`} />
              <Stat label="Approved" value={17} hint="74% approval rate" tone="good" />
              <Stat label="Fraud flags" value={2} hint="8.7% of intake" tone="warn" />
              <Stat label="Avg. decision" value="38s" hint="photo → adjuster" />
            </div>

            <Panel>
              <h2 className="text-base font-semibold text-foreground">
                Recent activity
              </h2>
              <ul className="mt-3 divide-y divide-border text-sm">
                {(
                  [
                    ["CF-9B710A9C85", "filed via Telegram", "2 min ago"],
                    ["CF-58E65714DA", "approved", "1h ago"],
                    ["CF-20D756C906", "rejected (weather mismatch)", "3h ago"],
                    ["", "Adjuster One signed in", "today"],
                  ] as const
                ).map(([id, msg, when], i) => (
                  <li
                    key={i}
                    className="flex items-center justify-between gap-3 py-3"
                  >
                    <span className="min-w-0 text-foreground">
                      {id ? (
                        <span className="mr-2 font-mono text-xs text-muted-foreground">
                          {id}
                        </span>
                      ) : null}
                      {msg}
                    </span>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {when}
                    </span>
                  </li>
                ))}
              </ul>
            </Panel>
          </TabsContent>

          <TabsContent value="billing" className="mt-6 space-y-4">
            <Panel>
              <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
                <div>
                  <p className="vl-eyebrow">Current plan</p>
                  <h2 className="mt-1.5 text-xl font-bold text-foreground">
                    Pilot · Free
                  </h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Up to 100 filed claims. {ORG.utilization} used,{" "}
                    {ORG.cap - ORG.utilization} remaining.
                  </p>
                </div>
                <Button className="h-10 px-4">Upgrade to Growth</Button>
              </div>
              <div
                className="mt-4 h-2 w-full overflow-hidden rounded-full bg-muted"
                role="progressbar"
                aria-valuenow={ORG.utilization}
                aria-valuemin={0}
                aria-valuemax={ORG.cap}
                aria-label="Free claims used this month"
              >
                <div
                  className="h-full rounded-full bg-primary"
                  style={{ width: `${(ORG.utilization / ORG.cap) * 100}%` }}
                />
              </div>
            </Panel>

            <Panel>
              <h2 className="text-base font-semibold text-foreground">
                Payment method
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                No payment method on file. You won&apos;t be charged unless you
                upgrade.
              </p>
              <Button variant="outline" disabled className="mt-3 h-10 px-4">
                Add payment method (set PAYMENTS_PROVIDER)
              </Button>
            </Panel>

            <Panel>
              <h2 className="text-base font-semibold text-foreground">Invoices</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                No invoices yet. They&apos;ll appear here once you upgrade.
              </p>
            </Panel>
          </TabsContent>

          <TabsContent value="team" className="mt-6 space-y-4">
            <Panel>
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-base font-semibold text-foreground">
                  Team members
                </h2>
                <Button className="h-10 px-4">Invite member</Button>
              </div>
              <ul className="mt-4 divide-y divide-border">
                {TEAM.map((m) => (
                  <li
                    key={m.email}
                    className="flex items-center justify-between gap-3 py-3"
                  >
                    <div className="min-w-0">
                      <div className="truncate font-medium text-foreground">
                        {m.name}
                      </div>
                      <div className="truncate text-xs text-muted-foreground">
                        {m.email}
                      </div>
                    </div>
                    <span className="shrink-0 text-xs font-medium text-muted-foreground">
                      {m.role}
                    </span>
                  </li>
                ))}
              </ul>
            </Panel>
          </TabsContent>

          <TabsContent value="api" className="mt-6 space-y-4">
            <ApiKeysPanel />

            <Panel>
              <h2 className="text-base font-semibold text-foreground">
                Webhook endpoints
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                We&apos;ll POST signed events here when claims are filed,
                approved, or rejected.
              </p>
              <div className="mt-4 space-y-2">
                <label htmlFor="webhook-url" className="sr-only">
                  Webhook URL
                </label>
                <input
                  id="webhook-url"
                  defaultValue="https://your-insurer.example.com/intake"
                  className={inputCls}
                />
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
                  <div>
                    Signing secret:{" "}
                    <code className="font-mono">{ORG.webhookSecret}</code>
                  </div>
                  <Button variant="outline" size="sm">
                    Add another
                  </Button>
                </div>
              </div>
            </Panel>
          </TabsContent>

          <TabsContent value="notifications" className="mt-6 space-y-4">
            <Panel>
              <h2 className="text-base font-semibold text-foreground">
                Notification preferences
              </h2>
              <ul className="mt-4 divide-y divide-border">
                {NOTIFICATION_PREFS.map((n) => (
                  <li
                    key={n.key}
                    className="flex items-center justify-between gap-4 py-3"
                  >
                    <div className="min-w-0">
                      <div className="font-medium text-foreground">{n.label}</div>
                      <div className="text-xs text-muted-foreground">
                        {n.desc}
                      </div>
                    </div>
                    <Switch
                      checked={prefs[n.key]}
                      onCheckedChange={(v) =>
                        setPrefs((p) => ({ ...p, [n.key]: v }))
                      }
                      aria-label={n.label}
                    />
                  </li>
                ))}
              </ul>
            </Panel>
          </TabsContent>

          <TabsContent value="settings" className="mt-6 space-y-4">
            <Panel>
              <h2 className="text-base font-semibold text-foreground">
                Workspace settings
              </h2>
              <div className="mt-4 grid gap-4">
                {[
                  ["Workspace name", ORG.name],
                  ["Default region", "ap-southeast-1 (Singapore)"],
                  ["Time zone", "UTC"],
                ].map(([label, value]) => (
                  <div key={label} className="flex flex-col gap-1.5">
                    <label className="text-sm font-medium text-foreground">
                      {label}
                    </label>
                    <input defaultValue={value} className={inputCls} />
                  </div>
                ))}
              </div>
            </Panel>

            <Panel className="border-destructive/40">
              <h2 className="text-base font-semibold text-destructive">
                Danger zone
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Delete your workspace. All claims, members, and audit logs are
                permanently erased after the 30-day GDPR retention window.
              </p>
              <Button variant="destructive" className="mt-3 h-10 px-4">
                Delete workspace
              </Button>
            </Panel>
          </TabsContent>
        </Tabs>
      </div>
    </AppShell>
  );
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
    if (!confirm(`Revoke ${keyId}? Any integration using this key will break.`))
      return;
    try {
      await revokeApiKey(keyId);
      toast.success("Key revoked");
      await reload();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Revoke failed");
    }
  }

  return (
    <Panel>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-base font-semibold text-foreground">
          <KeyRound className="size-4 text-muted-foreground" aria-hidden />
          API keys
        </h2>
        <span className="text-xs text-muted-foreground">
          Send{" "}
          <code className="font-mono text-[11px]">
            Authorization: Bearer cf_live_…
          </code>{" "}
          to the API.
        </span>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-2 md:grid-cols-12">
        <label htmlFor="key-name" className="sr-only">
          Key name
        </label>
        <input
          id="key-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="What is this key for? (e.g. insurer integration)"
          className={cn(inputCls, "md:col-span-6")}
        />
        <label htmlFor="key-scope" className="sr-only">
          Key scope
        </label>
        <select
          id="key-scope"
          value={scope}
          onChange={(e) => setScope(e.target.value)}
          className={cn(inputCls, "md:col-span-4")}
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
          className="h-10 md:col-span-2"
        >
          {issuing ? "Issuing…" : "Issue key"}
        </Button>
      </div>

      {justIssued ? (
        <div className="mt-4 rounded-lg border border-primary/40 bg-primary/5 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="text-sm font-semibold text-primary">
              New key — copy now, it won&apos;t be shown again
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                navigator.clipboard.writeText(justIssued.secret);
                toast.success("Secret copied to clipboard");
              }}
            >
              <Copy className="size-3.5" aria-hidden /> Copy
            </Button>
          </div>
          <code className="mt-3 block break-all rounded-lg border border-border bg-muted px-3 py-2 font-mono text-xs text-foreground">
            {justIssued.secret}
          </code>
          <div className="mt-2 text-[11px] text-muted-foreground">
            key id <span className="font-mono">{justIssued.key_id}</span> · scope{" "}
            <span className="font-mono">{justIssued.scope}</span>
          </div>
          <button
            onClick={() => setJustIssued(null)}
            className="mt-3 text-xs text-muted-foreground underline-offset-2 transition-colors hover:text-foreground hover:underline"
          >
            I&apos;ve copied it — dismiss
          </button>
        </div>
      ) : null}

      <div className="mt-5">
        {loading ? (
          <div className="space-y-2" aria-busy="true">
            <div className="h-12 animate-pulse rounded-lg bg-muted" />
            <div className="h-12 animate-pulse rounded-lg bg-muted" />
          </div>
        ) : error ? (
          <div className="rounded-lg border border-harvest-deep/40 bg-harvest/15 p-3 text-sm text-foreground">
            {error}{" "}
            {error.includes("Sign in") ? (
              <Link
                href="/auth/sign-in"
                className="font-medium text-primary underline"
              >
                Sign in →
              </Link>
            ) : null}
          </div>
        ) : keys.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
            No API keys yet. Issue one above to start calling the ClaimFarm API.
          </div>
        ) : (
          <ul className="divide-y divide-border">
            {keys.map((k) => {
              const isRevoked = k.revoked_at !== null;
              return (
                <li
                  key={k.key_id}
                  className="flex flex-col gap-2 py-3 md:flex-row md:items-center md:justify-between"
                >
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2 font-medium text-foreground">
                      {k.name || (
                        <span className="text-muted-foreground">untitled</span>
                      )}
                      <StatusBadge tone="info">{k.scope}</StatusBadge>
                      {isRevoked ? (
                        <StatusBadge tone="danger">revoked</StatusBadge>
                      ) : null}
                    </div>
                    <div className="mt-0.5 break-all font-mono text-[11px] text-muted-foreground">
                      {k.key_id} · created {fmtDate(k.created_at)} · last used{" "}
                      {fmtDate(k.last_used_at)}
                    </div>
                  </div>
                  {!isRevoked ? (
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleRevoke(k.key_id)}
                      className="shrink-0"
                    >
                      <Trash2 className="size-3.5" aria-hidden /> Revoke
                    </Button>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </Panel>
  );
}
