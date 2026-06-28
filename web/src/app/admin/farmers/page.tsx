"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { RefreshCw } from "lucide-react";
import { AppShell } from "@/components/app/app-shell";
import { Button } from "@/components/ui/button";
import { StatusBadge as Pill } from "@/components/ui/status-badge";
import { listFarmers, type Farmer } from "@/lib/api";

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

export default function FarmersPage() {
  const router = useRouter();
  const [farmers, setFarmers] = useState<Farmer[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  // Mirror admin/page.tsx: a 401 means no session — send them to sign-in
  // with a ?next so they bounce straight back here once authenticated.
  const handle401 = useCallback(
    (e: unknown) => {
      if (e instanceof Error && e.message === "unauthorized") {
        router.replace("/auth/sign-in?next=/admin/farmers");
        return true;
      }
      return false;
    },
    [router],
  );

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listFarmers();
      setFarmers(res.items);
      setTotal(res.total);
    } catch (e) {
      if (!handle401(e))
        toast.error(e instanceof Error ? e.message : "farmers load failed");
    } finally {
      setLoading(false);
    }
  }, [handle401]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <AppShell>
      <div className="mx-auto flex w-full max-w-[1320px] items-center justify-between gap-3 px-5 pb-3 pt-8 sm:px-8">
        <div>
          <p className="vl-eyebrow">Farmer profiles</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-foreground">
            Registered farmers
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {total} farmer{total === 1 ? "" : "s"} on record · registered via the
            Telegram bot.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Pill tone="info">{total} total</Pill>
          <Button variant="outline" size="sm" onClick={() => load()}>
            <RefreshCw className="size-3.5" aria-hidden /> Refresh
          </Button>
        </div>
      </div>

      <div className="mx-auto w-full max-w-[1320px] px-5 pb-16 sm:px-8">
        {loading ? (
          <div className="space-y-2" aria-busy="true">
            <div className="h-12 animate-pulse rounded-xl bg-muted" />
            <div className="h-12 animate-pulse rounded-xl bg-muted" />
            <div className="h-12 animate-pulse rounded-xl bg-muted" />
          </div>
        ) : farmers.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border bg-card py-16 text-center vl-shadow-card">
            <p className="text-base font-semibold text-foreground">
              No farmers yet
            </p>
            <p className="mx-auto mt-2 max-w-sm text-sm text-muted-foreground">
              Farmers register via the Telegram bot. Once they complete first-run
              registration, their profile appears here.
            </p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-border bg-card vl-shadow-card">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-secondary/50 text-left">
                    {[
                      "Name",
                      "Region / Village",
                      "Crops",
                      "Farm size",
                      "Language",
                      "Claims",
                      "Joined",
                      "Status",
                    ].map((h) => (
                      <th
                        key={h}
                        className="whitespace-nowrap px-4 py-3 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {farmers.map((f) => (
                    <tr
                      key={f.farmer_id}
                      className="transition-colors hover:bg-muted/40"
                    >
                      <td className="px-4 py-3">
                        <div className="font-medium text-foreground">
                          {f.name || "—"}
                        </div>
                        <div className="mt-0.5 text-[12px] text-muted-foreground">
                          {f.phone || f.email || (
                            <span className="font-mono">{f.farmer_id}</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-foreground">
                        {f.region || "—"}
                        {f.village ? (
                          <span className="text-muted-foreground">
                            {" "}
                            · {f.village}
                          </span>
                        ) : null}
                      </td>
                      <td className="px-4 py-3">
                        {f.crops?.length ? (
                          <div className="flex flex-wrap gap-1">
                            {f.crops.map((c) => (
                              <span
                                key={c}
                                className="rounded-full border border-border bg-secondary px-2 py-0.5 text-[11px] text-foreground"
                              >
                                {c}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 tabular-nums text-foreground">
                        {f.farm_area_hectares
                          ? `${f.farm_area_hectares} ha`
                          : "—"}
                      </td>
                      <td className="px-4 py-3 text-foreground">
                        {f.language || "—"}
                      </td>
                      <td className="px-4 py-3 tabular-nums text-foreground">
                        {f.claim_count}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                        {fmtDate(f.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        {f.registration_complete ? (
                          <Pill tone="success">Registered</Pill>
                        ) : (
                          <Pill tone="warning">Incomplete</Pill>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
