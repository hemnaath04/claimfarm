"use client";

import { useCallback, useEffect, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { RefreshCw } from "lucide-react";
import { AppShell } from "@/components/app/app-shell";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import {
  StatusBadge as Pill,
  type StatusTone,
} from "@/components/ui/status-badge";
import { cn } from "@/lib/utils";
import {
  fetchClaim,
  fetchLocalizedReply,
  fetchQueue,
  postDecision,
  type ClaimDetail,
  type ClaimSummary,
  type QueueStats,
} from "@/lib/api";

const STATUS_OPTIONS = [
  { key: "pending_review", label: "Pending" },
  { key: "approved", label: "Approved" },
  { key: "rejected", label: "Rejected" },
  { key: "submitted", label: "Submitted" },
  { key: "all", label: "All" },
];

const STATUS_TONE: Record<string, StatusTone> = {
  pending_review: "warning",
  approved: "success",
  rejected: "danger",
  submitted: "info",
  paid: "success",
};

function ClaimStatus({ status }: { status: string }) {
  return (
    <Pill tone={STATUS_TONE[status] ?? "neutral"}>
      {status.replace(/_/g, " ")}
    </Pill>
  );
}

function StatBlock({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-xl border border-border bg-card px-3 py-2.5">
      <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
      <div className="mt-0.5 text-xl font-bold tabular-nums text-foreground">
        {value}
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  sub,
}: {
  label: string;
  value: React.ReactNode;
  sub?: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-secondary/60 px-3 py-2.5">
      <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 text-base font-semibold tabular-nums text-foreground">
        {value}
      </div>
      {sub ? (
        <div className="mt-0.5 text-[11px] text-muted-foreground">{sub}</div>
      ) : null}
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-xl border border-border bg-card p-5 vl-shadow-card">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h2>
      <div className="mt-3">{children}</div>
    </section>
  );
}

export default function AdjusterConsolePage() {
  const router = useRouter();
  const [statusFilter, setStatusFilter] = useState<string>("pending_review");
  const [queue, setQueue] = useState<ClaimSummary[]>([]);
  const [stats, setStats] = useState<QueueStats | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ClaimDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [localizedReply, setLocalizedReply] = useState<string>("");
  const [notes, setNotes] = useState<string>("");
  const [isPending, startTransition] = useTransition();

  // CLAIM-005: redirect to login on any 401 so unauthenticated sessions
  // don't land on a blank "queue load failed" error message.
  const handle401 = useCallback(
    (e: unknown) => {
      if (e instanceof Error && e.message === "unauthorized") {
        router.replace("/auth/sign-in?next=/admin");
        return true;
      }
      return false;
    },
    [router],
  );

  // CLAIM-004: selectedId removed from deps — queue loads must not re-fire
  // every time the user clicks a different claim.
  const loadQueue = useCallback(async () => {
    try {
      const res = await fetchQueue(statusFilter);
      setQueue(res.items);
      setStats(res.stats);
      setSelectedId((prev) => prev ?? (res.items[0]?.claim_id ?? null));
    } catch (e) {
      if (!handle401(e))
        toast.error(e instanceof Error ? e.message : "queue load failed");
    }
  }, [statusFilter, handle401]);

  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    setDetailLoading(true);
    fetchClaim(selectedId)
      .then((d) => {
        if (cancelled) return;
        setDetail(d);
        setNotes(d.claim.adjuster_notes ?? "");
      })
      .catch((e) => {
        if (cancelled) return;
        if (!handle401(e))
          toast.error(e instanceof Error ? e.message : "claim load failed");
      })
      .finally(() => !cancelled && setDetailLoading(false));

    fetchLocalizedReply(selectedId).then(
      (msg) => !cancelled && setLocalizedReply(msg)
    );
    return () => {
      cancelled = true;
    };
  }, [selectedId, handle401]);

  const onDecision = (decision: "approve" | "reject" | "request_info") => {
    if (!selectedId) return;
    startTransition(async () => {
      try {
        const res = await postDecision(selectedId, decision, notes);
        const label = {
          approve: "Approved",
          reject: "Rejected",
          request_info: "Pending review",
        }[decision];
        toast.success(`${label} · ${selectedId}`, {
          description:
            decision === "approve" &&
            (res as { insurer?: { reviewer_notes?: string } }).insurer
              ? (res as { insurer: { reviewer_notes?: string } }).insurer
                  .reviewer_notes
              : undefined,
        });
        await loadQueue();
        const fresh = await fetchClaim(selectedId);
        setDetail(fresh);
      } catch (e) {
        if (!handle401(e))
          toast.error(e instanceof Error ? e.message : "decision failed");
      }
    });
  };

  const claim = detail?.claim;

  return (
    <AppShell>
      <div className="mx-auto flex w-full max-w-[1400px] items-center justify-between gap-3 px-5 pb-3 pt-6 sm:px-8">
        <div>
          <p className="vl-eyebrow">Adjuster console</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-foreground">
            Claims needing review
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <Pill tone="success">Live</Pill>
          <Button variant="outline" size="sm" onClick={() => loadQueue()}>
            <RefreshCw className="size-3.5" aria-hidden /> Refresh
          </Button>
        </div>
      </div>

      <div className="mx-auto grid w-full max-w-[1400px] grid-cols-1 gap-6 px-5 pb-12 sm:px-8 lg:grid-cols-[340px_minmax(0,1fr)]">
        {/* LEFT: queue + stats */}
        <aside className="space-y-4">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-2">
            <StatBlock label="Total" value={stats?.total ?? "—"} />
            <StatBlock label="Pending" value={stats?.pending_review ?? "—"} />
            <StatBlock label="Approved" value={stats?.approved ?? "—"} />
            <StatBlock label="Rejected" value={stats?.rejected ?? "—"} />
          </div>

          <div
            className="flex flex-wrap gap-1.5"
            role="tablist"
            aria-label="Filter claims by status"
          >
            {STATUS_OPTIONS.map((opt) => {
              const active = statusFilter === opt.key;
              return (
                <button
                  key={opt.key}
                  role="tab"
                  aria-selected={active}
                  onClick={() => setStatusFilter(opt.key)}
                  className={cn(
                    "rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                    active
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-border bg-card text-muted-foreground hover:bg-muted"
                  )}
                >
                  {opt.label}
                </button>
              );
            })}
          </div>

          <ScrollArea className="h-[360px] lg:h-[calc(100vh-280px)]">
            <div className="space-y-2 pr-2">
              {queue.length === 0 ? (
                <div className="rounded-xl border border-dashed border-border bg-card py-10 text-center text-sm text-muted-foreground">
                  No claims for this filter.
                </div>
              ) : (
                queue.map((c) => {
                  const isSelected = c.claim_id === selectedId;
                  return (
                    <button
                      key={c.claim_id}
                      onClick={() => setSelectedId(c.claim_id)}
                      aria-pressed={isSelected}
                      className={cn(
                        "w-full rounded-xl border p-3.5 text-left transition-colors",
                        isSelected
                          ? "border-primary bg-primary/8 ring-1 ring-primary/30"
                          : "border-border bg-card hover:bg-muted/60"
                      )}
                    >
                      <div className="font-mono text-[11px] text-muted-foreground">
                        {c.claim_id}
                      </div>
                      <div className="mt-1 text-sm font-medium text-foreground">
                        {c.farmer_name} · {c.crop_type}
                      </div>
                      <div className="mt-1.5 flex items-center justify-between gap-2">
                        <span className="text-xs font-medium tabular-nums text-foreground">
                          ${c.estimated_loss_usd.toLocaleString()}
                        </span>
                        <ClaimStatus status={c.status} />
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </ScrollArea>
        </aside>

        {/* RIGHT: detail */}
        <section className="min-w-0 space-y-4">
          {detailLoading || !claim ? (
            <div className="space-y-4" aria-busy="true">
              <div className="h-24 animate-pulse rounded-xl bg-muted" />
              <div className="h-64 animate-pulse rounded-xl bg-muted" />
              <div className="h-40 animate-pulse rounded-xl bg-muted" />
            </div>
          ) : (
            <>
              {/* HEADER */}
              <div className="flex flex-wrap items-start justify-between gap-4 rounded-xl border border-border bg-card px-5 py-4 vl-shadow-card">
                <div className="min-w-0">
                  <div className="font-mono text-[11px] text-muted-foreground">
                    {claim.claim_id}
                  </div>
                  <h2 className="mt-1 text-xl font-bold text-foreground">
                    {claim.farmer.name}&apos;s {claim.crop_type} claim
                  </h2>
                  <div className="mt-1 text-sm text-muted-foreground">
                    {claim.farmer.phone} · lang {claim.farmer.language} · loss{" "}
                    <span className="font-semibold tabular-nums text-foreground">
                      ${claim.estimated_loss_usd.toLocaleString()}
                    </span>
                  </div>
                </div>
                <ClaimStatus status={claim.status} />
              </div>

              <PhotoAndVerification detail={detail} />

              {/* AI ASSESSMENT */}
              <Section title="AI damage assessment · Qwen-VL-Max">
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  <Metric label="Crop" value={claim.damage.crop_type} />
                  <Metric label="Cause" value={claim.damage.damage_cause} />
                  <Metric label="Severity" value={`${claim.damage.severity}/100`} />
                  <Metric
                    label="Affected"
                    value={`${claim.damage.affected_area_pct}%`}
                    sub={`confidence ${Math.round(claim.damage.confidence * 100)}%`}
                  />
                </div>
                {claim.damage.visible_indicators?.length ? (
                  <div className="mt-3">
                    <div className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                      Visible indicators
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {claim.damage.visible_indicators.map((v) => (
                        <span
                          key={v}
                          className="rounded-full border border-border bg-secondary px-2 py-0.5 text-[11px] text-foreground"
                        >
                          {v}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
                {claim.damage.notes ? (
                  <p className="mt-3 text-sm italic text-muted-foreground">
                    {claim.damage.notes}
                  </p>
                ) : null}
              </Section>

              {/* WEATHER */}
              <Section title="Weather corroboration · Open-Meteo + Qwen-Max">
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  <Metric
                    label="Precip (30d)"
                    value={`${claim.weather.total_precip_mm} mm`}
                  />
                  <Metric label="Days >35°C" value={claim.weather.days_above_35c} />
                  <Metric
                    label="Heavy rain"
                    value={claim.weather.days_with_heavy_rain}
                  />
                  <Metric
                    label="Dry-day run"
                    value={`${claim.weather.consecutive_dry_days}d`}
                  />
                </div>
                <div
                  className={cn(
                    "mt-3 rounded-lg border-l-4 py-3 pl-4 pr-3 text-sm",
                    claim.corroboration.corroborated
                      ? "border-success bg-success/8"
                      : "border-destructive bg-destructive/8"
                  )}
                >
                  <div className="mb-1 font-semibold text-foreground">
                    {claim.corroboration.corroborated
                      ? "Corroborated"
                      : "Not corroborated"}{" "}
                    <span className="font-normal text-muted-foreground">
                      (strength {claim.corroboration.strength.toFixed(2)})
                    </span>
                  </div>
                  <div className="text-muted-foreground">
                    {claim.corroboration.evidence}
                  </div>
                  {claim.corroboration.flags?.length ? (
                    <ul className="mt-2 list-inside list-disc text-destructive">
                      {claim.corroboration.flags.map((fl) => (
                        <li key={fl}>{fl}</li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              </Section>

              {/* FORENSICS */}
              {claim.forensics ? (
                <Section title="Photo forensics · EXIF + Qwen-VL authenticity">
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                    <Metric
                      label="Authenticity"
                      value={`${Math.round(claim.forensics.authenticity_score * 100)}%`}
                      sub={
                        claim.forensics.appears_real_phone_photo
                          ? "real phone photo"
                          : "looks synthetic"
                      }
                    />
                    <Metric
                      label="EXIF present"
                      value={claim.forensics.has_exif ? "yes" : "no"}
                      sub={claim.forensics.has_exif ? undefined : "stripped"}
                    />
                    <Metric
                      label="GPS in EXIF"
                      value={
                        claim.forensics.gps_lat !== null
                          ? `${claim.forensics.gps_lat.toFixed(3)}, ${claim.forensics.gps_lon?.toFixed(3)}`
                          : "no"
                      }
                    />
                    <Metric
                      label="Capture time"
                      value={
                        claim.forensics.capture_time
                          ? new Date(claim.forensics.capture_time).toLocaleString()
                          : "unknown"
                      }
                    />
                  </div>
                  {claim.forensics.authenticity_reasoning ? (
                    <p className="mt-3 text-sm italic text-muted-foreground">
                      {claim.forensics.authenticity_reasoning}
                    </p>
                  ) : null}
                  {claim.forensics.flags.length ? (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {claim.forensics.flags.map((fl) => (
                        <span
                          key={fl}
                          className="rounded-full border border-harvest-deep/40 bg-harvest/15 px-2 py-0.5 text-[11px] font-medium text-foreground"
                        >
                          {fl}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </Section>
              ) : null}

              {/* SIMILAR + FRAUD */}
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <Section title="Similar past claims · DashVector">
                  {detail?.similar?.length ? (
                    <div className="space-y-2">
                      {detail.similar.map((s) => (
                        <div
                          key={s.claim_id ?? Math.random()}
                          className="rounded-lg border border-border bg-secondary/60 px-3 py-2 text-sm"
                        >
                          <div className="font-mono text-[11px] text-muted-foreground">
                            {s.claim_id ?? "—"}
                          </div>
                          <div className="mt-1 text-foreground">
                            {s.crop_type} / {s.damage_cause} ·{" "}
                            <span className="tabular-nums">
                              ${(s.estimated_loss_usd ?? 0).toLocaleString()}
                            </span>{" "}
                            <span className="text-muted-foreground">
                              · sim {s.score.toFixed(2)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">
                      No comparable claims.
                    </div>
                  )}
                </Section>

                <Section title="Risk flags">
                  {detail?.fraud_flags?.length ? (
                    <div className="space-y-2">
                      {detail.fraud_flags.map((fl, i) => (
                        <div
                          key={i}
                          className={cn(
                            "rounded-lg border-l-4 px-3 py-2 text-sm",
                            fl.severity === "block"
                              ? "border-destructive bg-destructive/8 text-foreground"
                              : "border-harvest-deep bg-harvest/15 text-foreground"
                          )}
                        >
                          <div className="text-[10px] font-semibold uppercase tracking-wide">
                            {fl.severity}
                          </div>
                          <div className="mt-0.5">{fl.message}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">
                      No fraud signals.
                    </div>
                  )}
                </Section>
              </div>

              {/* LOCALIZED MESSAGE */}
              {localizedReply ? (
                <Section
                  title={`Localized farmer message preview · ${claim.farmer.language}`}
                >
                  <div className="rounded-lg border-l-4 border-primary bg-primary/8 px-4 py-3 text-sm text-foreground">
                    {localizedReply}
                  </div>
                </Section>
              ) : null}

              {/* ADJUSTER DECISION */}
              <Section title="Adjuster decision">
                <label htmlFor="adjuster-notes" className="sr-only">
                  Adjuster notes
                </label>
                <Textarea
                  id="adjuster-notes"
                  placeholder="Adjuster notes…"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                />
                <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-3">
                  <Button
                    disabled={isPending}
                    onClick={() => onDecision("approve")}
                    className="h-10"
                  >
                    Approve &amp; submit
                  </Button>
                  <Button
                    disabled={isPending}
                    variant="outline"
                    onClick={() => onDecision("request_info")}
                    className="h-10"
                  >
                    Request more info
                  </Button>
                  <Button
                    disabled={isPending}
                    variant="destructive"
                    onClick={() => onDecision("reject")}
                    className="h-10"
                  >
                    Reject
                  </Button>
                </div>
              </Section>
            </>
          )}
        </section>
      </div>
    </AppShell>
  );
}

// ---------------------------------------------------------------------------
// Photo + verification panel — the bit adjusters look at first.
// ---------------------------------------------------------------------------

const SIGNAL_TONE: Record<string, StatusTone> = {
  good: "success",
  warn: "warning",
  block: "danger",
  neutral: "neutral",
};

function PhotoAndVerification({ detail }: { detail: ClaimDetail | null }) {
  const claim = detail?.claim;
  if (!claim) return null;

  const f = claim.forensics;
  const photoSrc = claim.photo_urls?.[0]
    ? new URL(claim.photo_urls[0], API_BASE).toString()
    : null;

  const signals: Array<{
    label: string;
    status: "good" | "warn" | "block" | "neutral";
    value: string;
    detail?: string;
  }> = [];

  if (claim.corroboration) {
    signals.push({
      label: "Weather corroboration",
      status: claim.corroboration.corroborated ? "good" : "warn",
      value: claim.corroboration.corroborated ? "Corroborated" : "Mismatch",
      detail: `strength ${claim.corroboration.strength.toFixed(2)}`,
    });
  }
  if (f) {
    signals.push({
      label: "EXIF metadata",
      status: f.has_exif ? "good" : "warn",
      value: f.has_exif ? "Present" : "Stripped",
      detail: f.has_exif
        ? `${f.camera_make ?? "?"} ${f.camera_model ?? ""}`.trim()
        : "Common for downloaded/edited images",
    });
    signals.push({
      label: "GPS in EXIF",
      status:
        f.gps_lat !== null && f.gps_lon !== null
          ? "good"
          : f.has_exif
            ? "warn"
            : "neutral",
      value:
        f.gps_lat !== null && f.gps_lon !== null
          ? `${f.gps_lat.toFixed(3)}, ${f.gps_lon?.toFixed(3)}`
          : "Missing",
      detail:
        f.gps_lat !== null
          ? "Cross-check with farmer location"
          : "Can't pin photo to a place",
    });
    signals.push({
      label: "Capture time",
      status: f.capture_time ? "good" : "warn",
      value: f.capture_time
        ? new Date(f.capture_time).toLocaleString()
        : "Unknown",
      detail: f.capture_time
        ? "Compared against claim date"
        : "Can't verify when the photo was taken",
    });
    signals.push({
      label: "Qwen-VL authenticity",
      status:
        f.authenticity_score >= 0.7
          ? "good"
          : f.authenticity_score >= 0.4
            ? "warn"
            : "block",
      value: `${Math.round(f.authenticity_score * 100)}%`,
      detail: f.appears_real_phone_photo
        ? "Looks like a real phone photo"
        : "Looks like a screenshot, render, or watermarked image",
    });
  }
  const blockFlag = detail?.fraud_flags?.find((x) => x.severity === "block");
  const warnFlag = detail?.fraud_flags?.find((x) => x.severity === "warn");
  signals.push({
    label: "Near-duplicate check",
    status: blockFlag ? "block" : warnFlag ? "warn" : "good",
    value: blockFlag
      ? "Duplicate of past claim"
      : warnFlag
        ? "Similar narrative"
        : "Unique",
    detail: blockFlag?.message ?? warnFlag?.message ?? "Compared via DashVector",
  });

  return (
    <Section title="Claim photo + verification signals">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
        <div className="grid aspect-[4/3] place-items-center overflow-hidden rounded-xl border border-border bg-secondary">
          {photoSrc ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={photoSrc}
              alt={`Crop photo submitted for claim ${claim.claim_id}`}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="px-6 text-center">
              <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                No photo on file
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                This claim has no photo attached. Demo seed claims are text-only;
                live Telegram intake saves the photo and serves it here.
              </p>
            </div>
          )}
        </div>

        <ul className="space-y-2">
          {signals.map((s) => (
            <li
              key={s.label}
              className="flex items-start gap-3 rounded-lg border border-border bg-secondary/50 px-3 py-2.5"
            >
              <span className="mt-1.5 shrink-0">
                <Pill tone={SIGNAL_TONE[s.status]}>{s.value}</Pill>
              </span>
              <div className="min-w-0 flex-1">
                <div className="text-[12px] font-semibold uppercase tracking-wide text-muted-foreground">
                  {s.label}
                </div>
                {s.detail ? (
                  <div className="mt-0.5 truncate text-[12px] text-muted-foreground">
                    {s.detail}
                  </div>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      </div>
      {!f ? (
        <p className="mt-3 rounded-lg border border-harvest-deep/40 bg-harvest/15 px-3 py-2 text-[12px] text-foreground">
          Photo forensics not run on this claim — likely a demo seed or an intake
          older than the forensics pipeline. New Telegram-filed claims include
          full EXIF + Qwen-VL authenticity by default.
        </p>
      ) : null}
    </Section>
  );
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";
