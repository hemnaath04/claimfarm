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
    credentials: "include",
  });
  if (r.status === 401) throw new Error("unauthorized");
  if (!r.ok) throw new Error(`queue load failed: ${r.status}`);
  return r.json();
}

export async function fetchClaim(claimId: string): Promise<ClaimDetail> {
  const r = await fetch(`${API_BASE}/api/claims/${claimId}`, {
    cache: "no-store",
    credentials: "include",
  });
  if (r.status === 401) throw new Error("unauthorized");
  if (!r.ok) throw new Error(`claim load failed: ${r.status}`);
  return r.json();
}

export async function fetchLocalizedReply(claimId: string): Promise<string> {
  const r = await fetch(`${API_BASE}/api/claims/${claimId}/localized_reply`, {
    cache: "no-store",
    credentials: "include",
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
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, notes }),
  });
  if (r.status === 401) throw new Error("unauthorized");
  if (!r.ok) {
    const err = await r.text();
    throw new Error(`decision ${decision} failed: ${err}`);
  }
  return r.json();
}

// ---------- API keys (cookie-authenticated) ----------

export type ApiKeySummary = {
  key_id: string;
  name: string;
  scope: string;
  created_at: string | null;
  last_used_at: string | null;
  expires_at: string | null;
  revoked_at: string | null;
};

export type IssuedApiKey = ApiKeySummary & {
  secret: string;
};

export async function listApiKeys(): Promise<ApiKeySummary[]> {
  const r = await fetch(`${API_BASE}/api/keys`, {
    cache: "no-store",
    credentials: "include",
  });
  if (r.status === 401) throw new Error("unauthorized");
  if (!r.ok) throw new Error(`list keys failed: ${r.status}`);
  const data = (await r.json()) as { items: ApiKeySummary[] };
  return data.items;
}

export async function issueApiKey(
  name: string,
  scope: string = "claims:read",
): Promise<IssuedApiKey> {
  const r = await fetch(`${API_BASE}/api/keys`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, scope }),
  });
  if (r.status === 401) throw new Error("unauthorized");
  if (!r.ok) {
    const err = await r.text();
    throw new Error(`issue key failed: ${err}`);
  }
  return r.json();
}

export async function revokeApiKey(keyId: string): Promise<void> {
  const r = await fetch(`${API_BASE}/api/keys/${encodeURIComponent(keyId)}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (r.status === 401) throw new Error("unauthorized");
  if (!r.ok) throw new Error(`revoke failed: ${r.status}`);
}

// ---------- Farmer profiles (cookie-authenticated, admin-only) ----------

export type Farmer = {
  farmer_id: string;
  name: string;
  language: string;
  region: string;
  village: string;
  crops: string[];
  farm_area_hectares: number;
  email: string | null;
  phone: string | null;
  channel: string;
  registration_complete: boolean;
  created_at: string | null;
  claim_count: number;
};

export async function listFarmers(): Promise<{
  items: Farmer[];
  total: number;
}> {
  const r = await fetch(`${API_BASE}/api/farmers`, {
    cache: "no-store",
    credentials: "include",
  });
  if (r.status === 401) throw new Error("unauthorized");
  if (!r.ok) throw new Error(`farmers load failed: ${r.status}`);
  return r.json();
}

// ---------- Workspace invites (cookie-authenticated, owner-only) ----------

export type Invite = {
  invite_id: string;
  email: string | null;
  role: string;
  created_at: string | null;
  expires_at: string | null;
  used_at: string | null;
  status: string;
};

export type IssuedInvite = {
  invite: Invite & { accept_url: string };
  accept_url: string;
};

export async function listInvites(): Promise<Invite[]> {
  const r = await fetch(`${API_BASE}/api/admin/invites`, {
    cache: "no-store",
    credentials: "include",
  });
  if (r.status === 401) throw new Error("unauthorized");
  if (!r.ok) throw new Error(`list invites failed: ${r.status}`);
  const data = (await r.json()) as { items: Invite[] };
  return data.items;
}

export async function createInvite(body: {
  email?: string;
  role: string;
}): Promise<IssuedInvite> {
  const r = await fetch(`${API_BASE}/api/admin/invites`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (r.status === 401) throw new Error("unauthorized");
  if (!r.ok) {
    const err = await r.text();
    throw new Error(`create invite failed: ${err}`);
  }
  return r.json();
}

export async function revokeInvite(inviteId: string): Promise<void> {
  const r = await fetch(
    `${API_BASE}/api/admin/invites/${encodeURIComponent(inviteId)}/revoke`,
    {
      method: "POST",
      credentials: "include",
    },
  );
  if (r.status === 401) throw new Error("unauthorized");
  if (!r.ok) throw new Error(`revoke invite failed: ${r.status}`);
}

export async function acceptInvite(body: {
  token: string;
  password: string;
  name: string;
  email?: string;
}): Promise<{ user_id: string; session?: unknown; role: string }> {
  const r = await fetch(`${API_BASE}/auth/accept-invite`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const err = await r.text();
    throw new Error(`accept invite failed: ${err}`);
  }
  return r.json();
}
