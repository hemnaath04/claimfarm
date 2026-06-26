"use client";

import { useCallback, useEffect, useState, useTransition } from "react";
import { toast } from "sonner";
import { AppShell } from "@/components/app/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
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

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending_review: "bg-amber-500/10 text-amber-300 border border-amber-400/20",
    approved: "bg-emerald-500/10 text-emerald-300 border border-emerald-400/30",
    rejected: "bg-red-500/10 text-red-300 border border-red-400/30",
    submitted: "bg-sky-500/10 text-sky-300 border border-sky-400/25",
    paid: "bg-lime-500/10 text-lime-300 border border-lime-400/30",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
        styles[status] ?? styles.pending_review
      }`}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}

function StatBlock({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="glass rounded-xl px-3 py-2.5">
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="text-xl font-semibold mt-0.5 tabular-nums">{value}</div>
    </div>
  );
}

function Metric({ label, value, sub }: { label: string; value: React.ReactNode; sub?: string }) {
  return (
    <div className="rounded-lg border border-border/50 bg-card/40 px-3 py-2.5">
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="text-base font-medium mt-1 tabular-nums">{value}</div>
      {sub ? <div className="text-[11px] text-muted-foreground mt-0.5">{sub}</div> : null}
    </div>
  );
}

export default function DashboardPage() {
  const [statusFilter, setStatusFilter] = useState<string>("pending_review");
  const [queue, setQueue] = useState<ClaimSummary[]>([]);
  const [stats, setStats] = useState<QueueStats | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ClaimDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [localizedReply, setLocalizedReply] = useState<string>("");
  const [notes, setNotes] = useState<string>("");
  const [isPending, startTransition] = useTransition();

  const loadQueue = useCallback(async () => {
    try {
      const res = await fetchQueue(statusFilter);
      setQueue(res.items);
      setStats(res.stats);
      if (!selectedId && res.items.length > 0) setSelectedId(res.items[0].claim_id);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "queue load failed");
    }
  }, [statusFilter, selectedId]);

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
        if (!cancelled) toast.error(e instanceof Error ? e.message : "claim load failed");
      })
      .finally(() => !cancelled && setDetailLoading(false));

    fetchLocalizedReply(selectedId).then((msg) => !cancelled && setLocalizedReply(msg));
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  const onDecision = (decision: "approve" | "reject" | "request_info") => {
    if (!selectedId) return;
    startTransition(async () => {
      try {
        const res = await postDecision(selectedId, decision, notes);
        const label = { approve: "Approved", reject: "Rejected", request_info: "Pending review" }[
          decision
        ];
        toast.success(`${label} · ${selectedId}`, {
          description:
            decision === "approve" && (res as { insurer?: { reviewer_notes?: string } }).insurer
              ? (res as { insurer: { reviewer_notes?: string } }).insurer.reviewer_notes
              : undefined,
        });
        await loadQueue();
        const fresh = await fetchClaim(selectedId);
        setDetail(fresh);
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "decision failed");
      }
    });
  };

  const claim = detail?.claim;

  return (
    <AppShell>
      <div className="max-w-[1400px] w-full mx-auto px-6 pt-6 pb-3 flex items-center justify-between">
        <div>
          <div className="eyebrow-mono">adjuster console</div>
          <h1 className="mt-1 text-[22px] font-bold text-[#F8FAFC]">
            Triage queue
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant="outline"
            className="border-emerald-400/30 text-emerald-300"
          >
            ● Live
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => loadQueue()}
            className="border-white/10 text-[#F8FAFC] hover:bg-white/5"
          >
            Refresh
          </Button>
        </div>
      </div>

      <div className="max-w-[1400px] w-full mx-auto px-6 pb-12 grid grid-cols-[340px_1fr] gap-6">
        {/* LEFT: queue + stats */}
        <aside className="space-y-4">
          <div className="grid grid-cols-2 gap-2">
            <StatBlock label="Total" value={stats?.total ?? "—"} />
            <StatBlock label="Pending" value={stats?.pending_review ?? "—"} />
            <StatBlock label="Approved" value={stats?.approved ?? "—"} />
            <StatBlock label="Rejected" value={stats?.rejected ?? "—"} />
          </div>

          <div className="flex flex-wrap gap-1.5">
            {STATUS_OPTIONS.map((opt) => (
              <button
                key={opt.key}
                onClick={() => setStatusFilter(opt.key)}
                className={`px-3 py-1.5 rounded-full text-[11px] font-medium border transition ${
                  statusFilter === opt.key
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-muted/30 text-muted-foreground border-border hover:bg-muted/50"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>

          <ScrollArea className="h-[calc(100vh-280px)]">
            <div className="space-y-2 pr-2">
              {queue.length === 0 ? (
                <div className="text-sm text-muted-foreground py-8 text-center glass rounded-xl">
                  No claims for this filter.
                </div>
              ) : (
                queue.map((c) => {
                  const isSelected = c.claim_id === selectedId;
                  return (
                    <button
                      key={c.claim_id}
                      onClick={() => setSelectedId(c.claim_id)}
                      className={`w-full text-left rounded-xl p-3.5 transition border ${
                        isSelected
                          ? "bg-primary/10 border-primary/60 ring-1 ring-primary/40"
                          : "glass hover:bg-muted/40"
                      }`}
                    >
                      <div className="mono-id">{c.claim_id}</div>
                      <div className="mt-1 font-medium text-sm">
                        {c.farmer_name} · {c.crop_type}
                      </div>
                      <div className="mt-1 text-[11px] text-muted-foreground flex items-center justify-between">
                        <span className="tabular-nums">${c.estimated_loss_usd.toLocaleString()}</span>
                        <StatusBadge status={c.status} />
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </ScrollArea>
        </aside>

        {/* RIGHT: detail */}
        <section className="space-y-4">
          {detailLoading || !claim ? (
            <Card className="glass">
              <CardHeader>
                <Skeleton className="h-6 w-1/3" />
                <Skeleton className="h-4 w-1/4" />
              </CardHeader>
              <CardContent className="space-y-3">
                <Skeleton className="h-32 w-full" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-24 w-full" />
              </CardContent>
            </Card>
          ) : (
            <>
              {/* HEADER */}
              <div className="glass rounded-xl px-5 py-4 flex items-start gap-4">
                <div className="flex-1">
                  <div className="mono-id">{claim.claim_id}</div>
                  <h1 className="text-xl font-semibold mt-1">
                    {claim.farmer.name}&apos;s {claim.crop_type} claim
                  </h1>
                  <div className="mt-1 text-sm text-muted-foreground">
                    {claim.farmer.phone} · lang {claim.farmer.language} · loss{" "}
                    <span className="text-foreground font-semibold tabular-nums">
                      ${claim.estimated_loss_usd.toLocaleString()}
                    </span>
                  </div>
                </div>
                <StatusBadge status={claim.status} />
              </div>

              {/* PHOTO + VERIFICATION SIGNALS */}
              <PhotoAndVerification detail={detail} />

              {/* AI ASSESSMENT */}
              <Card className="glass">
                <CardHeader>
                  <CardTitle className="text-sm uppercase tracking-wider text-muted-foreground">
                    AI damage assessment · Qwen-VL-Max
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-4 gap-2">
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
                    <div className="text-sm">
                      <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1.5">
                        Visible indicators
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {claim.damage.visible_indicators.map((v) => (
                          <span
                            key={v}
                            className="px-2 py-0.5 rounded-full text-[11px] bg-muted/40 border border-border/60"
                          >
                            {v}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  {claim.damage.notes ? (
                    <p className="text-sm text-muted-foreground italic">{claim.damage.notes}</p>
                  ) : null}
                </CardContent>
              </Card>

              {/* WEATHER */}
              <Card className="glass">
                <CardHeader>
                  <CardTitle className="text-sm uppercase tracking-wider text-muted-foreground">
                    Weather corroboration · Open-Meteo + Qwen-Max
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-4 gap-2">
                    <Metric label="Precip (30d)" value={`${claim.weather.total_precip_mm} mm`} />
                    <Metric label="Days >35°C" value={claim.weather.days_above_35c} />
                    <Metric label="Heavy rain" value={claim.weather.days_with_heavy_rain} />
                    <Metric label="Dry-day run" value={`${claim.weather.consecutive_dry_days}d`} />
                  </div>
                  <div
                    className={`text-sm rounded-lg border-l-4 pl-4 py-3 ${
                      claim.corroboration.corroborated
                        ? "border-emerald-400/70 bg-emerald-500/5"
                        : "border-red-400/70 bg-red-500/5"
                    }`}
                  >
                    <div className="font-semibold mb-1">
                      {claim.corroboration.corroborated ? "Corroborated" : "Not corroborated"}{" "}
                      <span className="text-muted-foreground font-normal">
                        (strength {claim.corroboration.strength.toFixed(2)})
                      </span>
                    </div>
                    <div className="text-muted-foreground">{claim.corroboration.evidence}</div>
                    {claim.corroboration.flags?.length ? (
                      <ul className="list-disc list-inside mt-2 text-red-300/90">
                        {claim.corroboration.flags.map((f) => (
                          <li key={f}>{f}</li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                </CardContent>
              </Card>

              {/* FORENSICS */}
              {claim.forensics ? (
                <Card className="glass">
                  <CardHeader>
                    <CardTitle className="text-sm uppercase tracking-wider text-muted-foreground">
                      Photo forensics · EXIF + Qwen-VL authenticity
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="grid grid-cols-4 gap-2">
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
                      <p className="text-sm text-muted-foreground italic">
                        {claim.forensics.authenticity_reasoning}
                      </p>
                    ) : null}
                    {claim.forensics.flags.length ? (
                      <div className="flex flex-wrap gap-1.5">
                        {claim.forensics.flags.map((f) => (
                          <span
                            key={f}
                            className="px-2 py-0.5 rounded-full text-[11px] bg-amber-500/10 text-amber-300 border border-amber-400/30"
                          >
                            {f}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </CardContent>
                </Card>
              ) : null}

              {/* SIMILAR + FRAUD */}
              <div className="grid grid-cols-2 gap-4">
                <Card className="glass">
                  <CardHeader>
                    <CardTitle className="text-sm uppercase tracking-wider text-muted-foreground">
                      Similar past claims · DashVector
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {detail?.similar?.length ? (
                      detail.similar.map((s) => (
                        <div
                          key={s.claim_id ?? Math.random()}
                          className="rounded-lg border border-border/60 px-3 py-2 text-sm bg-card/40"
                        >
                          <div className="mono-id">{s.claim_id ?? "—"}</div>
                          <div className="mt-1">
                            {s.crop_type} / {s.damage_cause} ·{" "}
                            <span className="tabular-nums">
                              ${(s.estimated_loss_usd ?? 0).toLocaleString()}
                            </span>{" "}
                            <span className="text-muted-foreground">
                              · sim {s.score.toFixed(2)}
                            </span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-sm text-muted-foreground">No comparable claims.</div>
                    )}
                  </CardContent>
                </Card>

                <Card className="glass">
                  <CardHeader>
                    <CardTitle className="text-sm uppercase tracking-wider text-muted-foreground">
                      Risk flags
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {detail?.fraud_flags?.length ? (
                      detail.fraud_flags.map((f, i) => (
                        <div
                          key={i}
                          className={`text-sm rounded-lg border-l-4 px-3 py-2 ${
                            f.severity === "block"
                              ? "border-red-400 bg-red-500/5 text-red-200"
                              : "border-amber-400 bg-amber-500/5 text-amber-200"
                          }`}
                        >
                          <div className="font-semibold uppercase text-[10px] tracking-wider">
                            {f.severity}
                          </div>
                          <div className="mt-0.5">{f.message}</div>
                        </div>
                      ))
                    ) : (
                      <div className="text-sm text-muted-foreground">No fraud signals.</div>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* LOCALIZED MESSAGE */}
              {localizedReply ? (
                <Card className="glass">
                  <CardHeader>
                    <CardTitle className="text-sm uppercase tracking-wider text-muted-foreground">
                      Localized farmer message preview · {claim.farmer.language}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="rounded-lg border-l-4 border-primary/70 bg-primary/5 px-4 py-3 text-sm">
                      {localizedReply}
                    </div>
                  </CardContent>
                </Card>
              ) : null}

              {/* ADJUSTER DECISION */}
              <Card className="glass">
                <CardHeader>
                  <CardTitle className="text-sm uppercase tracking-wider text-muted-foreground">
                    Adjuster decision
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Textarea
                    placeholder="Adjuster notes…"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={3}
                    className="bg-card/40"
                  />
                  <div className="grid grid-cols-3 gap-2">
                    <Button
                      disabled={isPending}
                      onClick={() => onDecision("approve")}
                      className="bg-primary text-primary-foreground hover:bg-primary/90"
                    >
                      Approve &amp; submit
                    </Button>
                    <Button
                      disabled={isPending}
                      variant="outline"
                      onClick={() => onDecision("request_info")}
                      className="border-amber-400/40 text-amber-200 hover:bg-amber-500/10"
                    >
                      Request more info
                    </Button>
                    <Button
                      disabled={isPending}
                      variant="outline"
                      onClick={() => onDecision("reject")}
                      className="border-red-400/40 text-red-200 hover:bg-red-500/10"
                    >
                      Reject
                    </Button>
                  </div>
                </CardContent>
              </Card>
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

  // 1. Damage assessment vs. weather
  if (claim.corroboration) {
    signals.push({
      label: "Weather corroboration",
      status: claim.corroboration.corroborated ? "good" : "warn",
      value: claim.corroboration.corroborated ? "Corroborated" : "Mismatch",
      detail: `strength ${claim.corroboration.strength.toFixed(2)}`,
    });
  }
  // 2. EXIF
  if (f) {
    signals.push({
      label: "EXIF metadata",
      status: f.has_exif ? "good" : "warn",
      value: f.has_exif ? "Present" : "Stripped",
      detail: f.has_exif
        ? `${f.camera_make ?? "?"} ${f.camera_model ?? ""}`.trim()
        : "Common for downloaded/edited images",
    });
    // 3. EXIF GPS
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
    // 4. Capture time
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
    // 5. Qwen-VL authenticity
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
  // 6. Near-duplicate / fraud signals
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
    <Card className="glass">
      <CardHeader>
        <CardTitle className="text-sm uppercase tracking-wider text-muted-foreground">
          Claim photo + verification signals
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)] gap-4">
          <div className="rounded-xl overflow-hidden bg-black/40 border border-white/5 aspect-[4/3] grid place-items-center">
            {photoSrc ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={photoSrc}
                alt={`Claim ${claim.claim_id} photo`}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="text-center px-6">
                <div className="eyebrow-mono text-[#8B95A5]">no photo on file</div>
                <p className="mt-2 text-sm text-muted-foreground">
                  This claim has no photo attached. Demo seed claims are
                  text-only; live Telegram intake saves the photo to disk +
                  serves it here.
                </p>
              </div>
            )}
          </div>

          <ul className="space-y-2">
            {signals.map((s) => (
              <li
                key={s.label}
                className="flex items-start gap-3 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2.5"
              >
                <SignalDot status={s.status} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="text-[12px] uppercase tracking-wider text-muted-foreground">
                      {s.label}
                    </span>
                    <span className="text-[13px] font-medium text-[#F8FAFC] tabular-nums">
                      {s.value}
                    </span>
                  </div>
                  {s.detail ? (
                    <div className="mt-0.5 text-[11px] text-muted-foreground truncate">
                      {s.detail}
                    </div>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        </div>
        {!f ? (
          <p className="mt-3 text-[12px] text-amber-200/80">
            Photo forensics not run on this claim — likely a demo seed or an
            intake older than the forensics pipeline. New Telegram-filed claims
            include full EXIF + Qwen-VL authenticity by default.
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}

function SignalDot({ status }: { status: "good" | "warn" | "block" | "neutral" }) {
  const color =
    status === "good"
      ? "#BDF272"
      : status === "warn"
        ? "#FDD68A"
        : status === "block"
          ? "#FDA4AF"
          : "#8B95A5";
  return (
    <span
      className="mt-2 h-2 w-2 rounded-full shrink-0"
      style={{ background: color, boxShadow: `0 0 8px ${color}55` }}
      aria-hidden
    />
  );
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";
