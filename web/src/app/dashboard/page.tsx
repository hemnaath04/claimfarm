"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { AppShell } from "@/components/app/app-shell";
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

function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={`glass-card p-5 ${className}`}>{children}</div>;
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
      ? "text-[#BDF272]"
      : tone === "warn"
        ? "text-[#FDD68A]"
        : "text-[#8B95A5]";
  return (
    <div className="glass-card p-4">
      <div className="eyebrow-mono text-[#8B95A5]">{label}</div>
      <div className="mt-1 text-[26px] font-bold tabular-nums text-[#F8FAFC]">
        {value}
      </div>
      {hint ? <div className={`mt-1 text-[12px] ${hintColor}`}>{hint}</div> : null}
    </div>
  );
}

export default function DashboardPage() {
  const [prefs, setPrefs] = useState<Record<string, boolean>>({
    new_claim: true,
    fraud_flag: true,
    weekly_summary: true,
    billing: true,
  });

  return (
    <AppShell>
      <div className="max-w-[1280px] mx-auto px-6 pt-8 pb-16">
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div>
            <div className="eyebrow-mono">workspace</div>
            <h1 className="mt-1 text-[28px] font-bold leading-9 text-[#F8FAFC]">
              {ORG.name}
            </h1>
            <p className="mt-1 text-sm text-[#8B95A5]">
              Plan{" "}
              <span className="status-pill status-pill-ok ml-1">{ORG.plan}</span>{" "}
              · {ORG.utilization} of {ORG.cap} free claims this month
            </p>
          </div>
          <div className="flex gap-2">
            <Link
              href="/admin"
              className="btn-ghost-translucent h-10 px-4 text-sm font-semibold inline-flex items-center"
            >
              Open adjuster console →
            </Link>
          </div>
        </div>

        <Tabs defaultValue="overview" className="mt-8">
          <TabsList className="bg-transparent border border-white/10 p-1 rounded-xl">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="billing">Billing</TabsTrigger>
            <TabsTrigger value="team">Team</TabsTrigger>
            <TabsTrigger value="api">API &amp; webhooks</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4 mt-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <Stat label="Claims this month" value={ORG.utilization} hint={`of ${ORG.cap} free`} />
              <Stat label="Approved" value={17} hint="74% approval rate" tone="good" />
              <Stat label="Fraud flags" value={2} hint="8.7% of intake" tone="warn" />
              <Stat label="Avg time-to-decision" value="38s" hint="photo → adjuster" />
            </div>

            <Card>
              <h3 className="text-[15px] font-semibold text-[#F8FAFC]">
                Recent activity
              </h3>
              <ul className="mt-3 divide-y divide-white/5 text-sm">
                {[
                  ["CF-9B710A9C85", "filed via Telegram", "2 min ago", "default"],
                  ["CF-58E65714DA", "approved", "1h ago", "good"],
                  ["CF-20D756C906", "rejected (weather mismatch)", "3h ago", "err"],
                  ["", "Adjuster One signed in", "today", "default"],
                ].map(([id, msg, when, tone], i) => (
                  <li key={i} className="flex items-center justify-between py-2.5">
                    <span className="text-[#F8FAFC]">
                      {id ? <span className="font-mono text-[12px] text-[#8B95A5] mr-2">{id}</span> : null}
                      {msg}
                    </span>
                    <span className="text-[12px] text-[#8B95A5]">{when}</span>
                  </li>
                ))}
              </ul>
            </Card>
          </TabsContent>

          <TabsContent value="billing" className="space-y-4 mt-6">
            <Card>
              <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3">
                <div>
                  <div className="eyebrow-mono">current plan</div>
                  <h3 className="mt-1 text-[20px] font-bold text-[#F8FAFC]">
                    Pilot · Free
                  </h3>
                  <p className="mt-1 text-[13px] text-[#8B95A5]">
                    Up to 100 filed claims. {ORG.utilization} used,{" "}
                    {ORG.cap - ORG.utilization} remaining.
                  </p>
                </div>
                <button className="btn-gradient h-[42px] px-4 text-sm">
                  Upgrade to Growth
                </button>
              </div>
              <div className="mt-4 h-1.5 w-full rounded-full bg-white/5 overflow-hidden">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${(ORG.utilization / ORG.cap) * 100}%`,
                    background: "var(--brand-gradient)",
                  }}
                />
              </div>
            </Card>

            <Card>
              <h3 className="text-[15px] font-semibold text-[#F8FAFC]">
                Payment method
              </h3>
              <p className="mt-1 text-[13px] text-[#8B95A5]">
                No payment method on file. You won&apos;t be charged unless you upgrade.
              </p>
              <button
                disabled
                className="btn-ghost-translucent mt-3 h-10 px-4 text-sm font-semibold opacity-60 cursor-not-allowed"
              >
                Add payment method (set PAYMENTS_PROVIDER)
              </button>
            </Card>

            <Card>
              <h3 className="text-[15px] font-semibold text-[#F8FAFC]">Invoices</h3>
              <p className="mt-1 text-[13px] text-[#8B95A5]">
                No invoices yet. They&apos;ll appear here once you upgrade.
              </p>
            </Card>
          </TabsContent>

          <TabsContent value="team" className="space-y-4 mt-6">
            <Card>
              <div className="flex items-center justify-between">
                <h3 className="text-[15px] font-semibold text-[#F8FAFC]">
                  Team members
                </h3>
                <button className="btn-gradient h-10 px-4 text-sm">
                  Invite member
                </button>
              </div>
              <ul className="mt-4 divide-y divide-white/5">
                {TEAM.map((m) => (
                  <li
                    key={m.email}
                    className="flex items-center justify-between py-3"
                  >
                    <div>
                      <div className="font-medium text-[#F8FAFC]">{m.name}</div>
                      <div className="text-[12px] text-[#8B95A5]">{m.email}</div>
                    </div>
                    <span className="eyebrow-mono text-[#8B95A5]">{m.role}</span>
                  </li>
                ))}
              </ul>
            </Card>
          </TabsContent>

          <TabsContent value="api" className="space-y-4 mt-6">
            <ApiKeysPanel />

            <Card>
              <h3 className="text-[15px] font-semibold text-[#F8FAFC]">
                Webhook endpoints
              </h3>
              <p className="mt-1 text-[13px] text-[#8B95A5]">
                We&apos;ll POST signed events here when claims are filed, approved, or
                rejected.
              </p>
              <div className="mt-4 space-y-2">
                <input
                  defaultValue="https://your-insurer.example.com/intake"
                  className="field-input w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-[13px]"
                />
                <div className="flex items-center justify-between text-[12px] text-[#8B95A5]">
                  <div>
                    Signing secret:{" "}
                    <code className="font-mono">{ORG.webhookSecret}</code>
                  </div>
                  <button className="btn-ghost-translucent h-8 px-3 text-[12px] font-semibold">
                    Add another
                  </button>
                </div>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="notifications" className="space-y-4 mt-6">
            <Card>
              <h3 className="text-[15px] font-semibold text-[#F8FAFC]">
                Notification preferences
              </h3>
              <ul className="mt-4 divide-y divide-white/5">
                {NOTIFICATION_PREFS.map((n) => (
                  <li
                    key={n.key}
                    className="flex items-center justify-between py-3"
                  >
                    <div>
                      <div className="font-medium text-[#F8FAFC]">{n.label}</div>
                      <div className="text-[12px] text-[#8B95A5]">{n.desc}</div>
                    </div>
                    <Switch
                      checked={prefs[n.key]}
                      onCheckedChange={(v) =>
                        setPrefs((p) => ({ ...p, [n.key]: v }))
                      }
                    />
                  </li>
                ))}
              </ul>
            </Card>
          </TabsContent>

          <TabsContent value="settings" className="space-y-4 mt-6">
            <Card>
              <h3 className="text-[15px] font-semibold text-[#F8FAFC]">
                Workspace settings
              </h3>
              <div className="mt-4 grid gap-3">
                {[
                  ["Workspace name", ORG.name],
                  ["Default region", "ap-southeast-1 (Singapore)"],
                  ["Time zone", "UTC"],
                ].map(([label, value]) => (
                  <label key={label} className="field">
                    <span className="field-label">{label}</span>
                    <input
                      defaultValue={value}
                      className="field-input"
                    />
                  </label>
                ))}
              </div>
            </Card>

            <Card className="!border-red-400/30">
              <h3 className="text-[15px] font-semibold text-red-300">
                Danger zone
              </h3>
              <p className="mt-1 text-[13px] text-[#8B95A5]">
                Delete your workspace. All claims, members, and audit logs are
                permanently erased after the 30-day GDPR retention window.
              </p>
              <button className="btn-ghost-translucent mt-3 h-10 px-4 text-sm font-semibold border-red-400/40 text-red-200 hover:bg-red-500/10">
                Delete workspace
              </button>
            </Card>
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
    <div className="glass-card p-5">
      <div className="flex items-center justify-between">
        <h3 className="text-[15px] font-semibold text-[#F8FAFC]">API keys</h3>
        <span className="text-[12px] text-[#8B95A5]">
          Send{" "}
          <code className="font-mono text-[11px]">
            Authorization: Bearer cf_live_…
          </code>{" "}
          to the API.
        </span>
      </div>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-12 gap-2">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="What is this key for? (e.g. insurer integration)"
          className="field-input md:col-span-6 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-[13px]"
        />
        <select
          value={scope}
          onChange={(e) => setScope(e.target.value)}
          className="md:col-span-4 bg-white/5 border border-white/10 rounded-lg px-3 text-sm h-10 text-[#F8FAFC]"
        >
          {SCOPES.map((s) => (
            <option key={s.value} value={s.value} className="bg-[#0a0d12]">
              {s.label}
            </option>
          ))}
        </select>
        <button
          onClick={handleIssue}
          disabled={issuing}
          className="btn-gradient md:col-span-2 h-10 text-sm"
        >
          {issuing ? "Issuing…" : "Issue key"}
        </button>
      </div>

      {justIssued ? (
        <div className="mt-4 rounded-xl border border-[#BDF272]/40 bg-[#BDF272]/5 p-4">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-[#BDF272]">
              New key — copy now, it won&apos;t be shown again
            </div>
            <button
              onClick={() => {
                navigator.clipboard.writeText(justIssued.secret);
                toast.success("Secret copied to clipboard");
              }}
              className="btn-ghost-translucent h-8 px-3 text-[12px] font-semibold"
            >
              Copy
            </button>
          </div>
          <code className="block mt-3 font-mono text-[12px] break-all bg-black/40 px-3 py-2 rounded-lg text-[#F8FAFC]">
            {justIssued.secret}
          </code>
          <div className="mt-2 text-[11px] text-[#8B95A5]">
            key id <span className="font-mono">{justIssued.key_id}</span> · scope{" "}
            <span className="font-mono">{justIssued.scope}</span>
          </div>
          <button
            onClick={() => setJustIssued(null)}
            className="mt-3 text-[12px] text-[#8B95A5] hover:text-[#F8FAFC] transition"
          >
            I&apos;ve copied it — dismiss
          </button>
        </div>
      ) : null}

      <div className="mt-5">
        {loading ? (
          <div className="text-[13px] text-[#8B95A5]">Loading keys…</div>
        ) : error ? (
          <div className="text-[13px] text-[#FDD68A]">
            {error}{" "}
            {error.includes("Sign in") ? (
              <Link href="/auth/sign-in" className="underline text-[#BDF272]">
                Sign in →
              </Link>
            ) : null}
          </div>
        ) : keys.length === 0 ? (
          <div className="text-[13px] text-[#8B95A5]">
            No API keys yet. Issue one above to start calling the ClaimFarm API.
          </div>
        ) : (
          <ul className="divide-y divide-white/5">
            {keys.map((k) => {
              const isRevoked = k.revoked_at !== null;
              return (
                <li
                  key={k.key_id}
                  className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 py-3"
                >
                  <div>
                    <div className="font-medium flex items-center gap-2 text-[#F8FAFC]">
                      {k.name || (
                        <span className="text-[#8B95A5]">untitled</span>
                      )}
                      <span className="status-pill status-pill-ok">{k.scope}</span>
                      {isRevoked ? (
                        <span className="status-pill status-pill-err">revoked</span>
                      ) : null}
                    </div>
                    <div className="text-[11px] text-[#8B95A5] mt-0.5 font-mono">
                      {k.key_id} · created {fmtDate(k.created_at)} · last used{" "}
                      {fmtDate(k.last_used_at)}
                    </div>
                  </div>
                  {!isRevoked ? (
                    <button
                      onClick={() => handleRevoke(k.key_id)}
                      className="btn-ghost-translucent h-8 px-3 text-[12px] font-semibold border-red-400/40 text-red-200 hover:bg-red-500/10"
                    >
                      Revoke
                    </button>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
