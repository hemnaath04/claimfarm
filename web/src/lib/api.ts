/**
 * Adjuster JSON API client. Backed by the FastAPI process in /app on
 * port 8000 locally; the same routes also live on the deployed Function
 * Compute instance.
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export type ClaimSummary = {
  claim_id: string;
  status: string;
  created_at: string | null;
  farmer_name: string;
  farmer_language: string;
  crop_type: string;
  estimated_loss_usd: number;
};

export type QueueStats = {
  total: number;
  pending_review: number;
  approved: number;
  rejected: number;
  submitted: number;
  paid: number;
};

export type SimilarHit = {
  claim_id: string | null;
  farmer_phone: string | null;
  crop_type: string | null;
  damage_cause: string | null;
  status: string | null;
  estimated_loss_usd: number | null;
  score: number;
};

export type FraudFlag = {
  severity: "block" | "warn" | string;
  message: string;
  related_claim_id: string | null;
  similarity: number;
};

export type Forensics = {
  has_exif: boolean;
  capture_time: string | null;
  gps_lat: number | null;
  gps_lon: number | null;
  camera_make: string | null;
  camera_model: string | null;
  software: string | null;
  width: number | null;
  height: number | null;
  file_size_bytes: number;
  appears_real_phone_photo: boolean;
  authenticity_score: number;
  authenticity_reasoning: string;
  flags: string[];
};

export type ClaimDetail = {
  claim: {
    claim_id: string;
    farmer: {
      name: string;
      phone: string;
      language: string;
      latitude: number;
      longitude: number;
      region: string;
      farm_area_hectares: number;
    };
    crop_type: string;
    date_of_damage: string;
    photo_urls: string[];
    farmer_narrative: string;
    damage: {
      crop_type: string;
      damage_cause: string;
      severity: number;
      affected_area_pct: number;
      confidence: number;
      visible_indicators: string[];
      notes: string;
    };
    weather: {
      latitude: number;
      longitude: number;
      start_date: string;
      end_date: string;
      total_precip_mm: number;
      max_temp_c: number;
      min_temp_c: number;
      max_wind_kmh: number;
      days_above_35c: number;
      days_with_heavy_rain: number;
      days_with_frost: number;
      consecutive_dry_days: number;
    };
    corroboration: {
      corroborated: boolean;
      strength: number;
      evidence: string;
      flags: string[];
    };
    forensics: Forensics | null;
    estimated_loss_usd: number;
    status: string;
    created_at: string;
    adjuster_notes: string;
  };
  pdf_path: string | null;
  insurer_claim_id: string | null;
  similar: SimilarHit[];
  fraud_flags: FraudFlag[];
};

export async function fetchQueue(status: string = "pending_review"): Promise<{
  items: ClaimSummary[];
  stats: QueueStats;
}> {
  const r = await fetch(`${API_BASE}/api/claims?status=${encodeURIComponent(status)}`, {
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`queue load failed: ${r.status}`);
  return r.json();
}

export async function fetchClaim(claimId: string): Promise<ClaimDetail> {
  const r = await fetch(`${API_BASE}/api/claims/${claimId}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`claim load failed: ${r.status}`);
  return r.json();
}

export async function fetchLocalizedReply(claimId: string): Promise<string> {
  const r = await fetch(`${API_BASE}/api/claims/${claimId}/localized_reply`, {
    cache: "no-store",
  });
  if (!r.ok) return "";
  const data = (await r.json()) as { message?: string };
  return data.message ?? "";
}

export async function postDecision(
  claimId: string,
  decision: "approve" | "reject" | "request_info",
  notes: string,
): Promise<Record<string, unknown>> {
  const r = await fetch(`${API_BASE}/api/claims/${claimId}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, notes }),
  });
  if (!r.ok) {
    const err = await r.text();
    throw new Error(`decision ${decision} failed: ${err}`);
  }
  return r.json();
}
