"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { Copy, RefreshCw, ShieldAlert } from "lucide-react";
import { AppShell } from "@/components/app/app-shell";
import { Button } from "@/components/ui/button";
import { StatusBadge as Pill, type StatusTone } from "@/components/ui/status-badge";
import { useAuthUser } from "@/lib/user-state";
import { cn } from "@/lib/utils";
import {
  createInvite,
  listInvites,
  revokeInvite,
  type Invite,
} from "@/lib/api";

const ROLES = [
  { value: "reviewer", label: "Reviewer" },
  { value: "moderator", label: "Moderator" },
  { value: "admin", label: "Admin" },
] as const;

const STATUS_TONE: Record<string, StatusTone> = {
  active: "success",
  used: "info",
  expired: "neutral",
  revoked: "danger",
};

const inputCls =
  "h-10 w-full rounded-lg border border-border bg-card px-3 text-sm text-foreground placeholder:text-muted-foreground focus-visible:border-ring focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50";

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

function copy(text: string) {
  navigator.clipboard.writeText(text);
  toast.success("Invite link copied to clipboard");
}

export default function InvitesPage() {
  const user = useAuthUser();
  const isOwner = user && typeof user === "object" && user.role === "owner";

  const [invites, setInvites] = useState<Invite[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [email, setEmail] = useState("");
  const [role, setRole] = useState<string>("reviewer");
  const [creating, setCreating] = useState(false);
  const [lastUrl, setLastUrl] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setInvites(await listInvites());
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg === "unauthorized" ? "Sign in to manage invites." : msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Only fetch once we know the user is an owner — non-owners never hit
    // the (owner-only) endpoint and just see the access panel.
    if (isOwner) void reload();
  }, [isOwner, reload]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    try {
      const res = await createInvite({
        email: email.trim() || undefined,
        role,
      });
      setLastUrl(res.accept_url);
      setEmail("");
      setRole("reviewer");
      toast.success("Invite created — copy the link below to share it.");
      await reload();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to create invite");
    } finally {
      setCreating(false);
    }
  }

  async function handleRevoke(inviteId: string) {
    if (!confirm("Revoke this invite? The link will stop working.")) return;
    try {
      await revokeInvite(inviteId);
      toast.success("Invite revoked");
      await reload();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Revoke failed");
    }
  }

  // Still resolving the session, or signed-out — let AppShell's gate handle it.
  if (user === null) {
    return (
      <AppShell>
        <div className="mx-auto w-full max-w-[900px] px-5 py-8 sm:px-8">
          <div className="h-40 animate-pulse rounded-xl bg-muted" />
        </div>
      </AppShell>
    );
  }

  if (!isOwner) {
    return (
      <AppShell>
        <div className="mx-auto w-full max-w-[640px] px-5 py-16 sm:px-8">
          <div className="rounded-xl border border-border bg-card p-8 text-center vl-shadow-card">
            <ShieldAlert
              className="mx-auto size-9 text-muted-foreground"
              aria-hidden
            />
            <h1 className="mt-4 text-xl font-bold tracking-tight text-foreground">
              Owner access only
            </h1>
            <p className="mx-auto mt-2 max-w-sm text-sm text-muted-foreground">
              Only the workspace owner can invite teammates and manage access.
              Ask your owner to send you an invite if you need a higher role.
            </p>
            <Link
              href="/admin"
              className="mt-5 inline-flex text-sm font-medium text-primary hover:underline"
            >
              ← Back to adjuster console
            </Link>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mx-auto flex w-full max-w-[1100px] items-center justify-between gap-3 px-5 pb-3 pt-8 sm:px-8">
        <div>
          <p className="vl-eyebrow">Workspace access</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-foreground">
            Invites
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Access is invite-only. Send a link to add a teammate with a set role.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => reload()}>
          <RefreshCw className="size-3.5" aria-hidden /> Refresh
        </Button>
      </div>

      <div className="mx-auto w-full max-w-[1100px] space-y-4 px-5 pb-16 sm:px-8">
        {/* Create invite */}
        <div className="rounded-xl border border-border bg-card p-5 vl-shadow-card">
          <h2 className="text-base font-semibold text-foreground">
            Create invite
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Add an email to tie the invite to one person, or leave it blank for a
            shareable link.
          </p>
          <form
            onSubmit={handleCreate}
            className="mt-4 grid grid-cols-1 gap-2 md:grid-cols-12"
          >
            <label htmlFor="invite-email" className="sr-only">
              Email (optional)
            </label>
            <input
              id="invite-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="teammate@insurer.org (optional)"
              autoComplete="email"
              className={cn(inputCls, "md:col-span-6")}
            />
            <label htmlFor="invite-role" className="sr-only">
              Role
            </label>
            <select
              id="invite-role"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className={cn(inputCls, "md:col-span-4")}
            >
              {ROLES.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
            <Button
              type="submit"
              disabled={creating}
              className="h-10 md:col-span-2"
            >
              {creating ? "Creating…" : "Create invite"}
            </Button>
          </form>

          {lastUrl ? (
            <div className="mt-4 rounded-lg border border-primary/40 bg-primary/5 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="text-sm font-semibold text-primary">
                  Invite link ready — share it with your teammate
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copy(lastUrl)}
                >
                  <Copy className="size-3.5" aria-hidden /> Copy
                </Button>
              </div>
              <code className="mt-3 block break-all rounded-lg border border-border bg-muted px-3 py-2 font-mono text-xs text-foreground">
                {lastUrl}
              </code>
              <button
                onClick={() => setLastUrl(null)}
                className="mt-3 text-xs text-muted-foreground underline-offset-2 transition-colors hover:text-foreground hover:underline"
              >
                Dismiss
              </button>
            </div>
          ) : null}
        </div>

        {/* Invites table */}
        <div className="rounded-xl border border-border bg-card p-5 vl-shadow-card">
          <h2 className="text-base font-semibold text-foreground">
            Sent invites
          </h2>
          <div className="mt-4">
            {loading ? (
              <div className="space-y-2" aria-busy="true">
                <div className="h-12 animate-pulse rounded-lg bg-muted" />
                <div className="h-12 animate-pulse rounded-lg bg-muted" />
              </div>
            ) : error ? (
              <div className="rounded-lg border border-harvest-deep/40 bg-harvest/15 p-3 text-sm text-foreground">
                {error}
              </div>
            ) : invites.length === 0 ? (
              <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
                No invites yet. Create one above to add a teammate.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left">
                      {["Email", "Role", "Status", "Expires", ""].map((h, i) => (
                        <th
                          key={i}
                          className="whitespace-nowrap px-3 py-2 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {invites.map((inv) => (
                      <tr key={inv.invite_id}>
                        <td className="px-3 py-3 text-foreground">
                          {inv.email || (
                            <span className="text-muted-foreground">
                              link-only
                            </span>
                          )}
                        </td>
                        <td className="px-3 py-3">
                          <Pill tone="info">{inv.role}</Pill>
                        </td>
                        <td className="px-3 py-3">
                          <Pill tone={STATUS_TONE[inv.status] ?? "neutral"}>
                            {inv.status}
                          </Pill>
                        </td>
                        <td className="whitespace-nowrap px-3 py-3 text-muted-foreground">
                          {fmtDate(inv.expires_at)}
                        </td>
                        <td className="px-3 py-3 text-right">
                          {inv.status === "active" ? (
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => handleRevoke(inv.invite_id)}
                            >
                              Revoke
                            </Button>
                          ) : null}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
