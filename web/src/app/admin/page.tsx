"use client";

import { useCallback, useEffect, useState, useTransition } from "react";
import { toast } from "sonner";
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
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-border/40 bg-background/80 backdrop-blur-md sticky top-0 z-20">
        <div className="max-w-[1400px] mx-auto px-6 py-3 flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold tracking-tight">claim</span>
            <span className="text-lg font-bold tracking-tight neon-text">farm</span>
          </div>
          <div className="text-sm text-muted-foreground">Adjuster Console</div>
          <div className="ml-auto flex items-center gap-2">
            <Badge variant="outline" className="border-emerald-400/30 text-emerald-300">
              ● Live
            </Badge>
            <Button variant="outline" size="sm" onClick={() => loadQueue()}>
              Refresh
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-[1400px] w-full mx-auto px-6 py-6 grid grid-cols-[340px_1fr] gap-6">
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
      </main>
    </div>
  );
}
