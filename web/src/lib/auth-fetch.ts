/**
 * Auth-flow fetch helper.
 *
 * The backend uses FastAPI's standard error shape `{ "detail": "..." }`.
 * The auth forms used to swallow that and toast "sign-up failed: 409",
 * which is unfriendly. This helper parses the body, raises a typed error
 * the form can branch on (status + detail), and never leaves the caller
 * stuck with a bare status code.
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "";

export class AuthApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

export async function postAuthJson<T>(
  path: string,
  body: Record<string, unknown>,
): Promise<T> {
  let r: Response;
  try {
    r = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    // Browser-level failure (DNS / network / CORS preflight) lands here.
    throw new AuthApiError(0, "Couldn't reach the server. Check your connection and try again.");
  }

  let data: unknown = null;
  try {
    data = await r.json();
  } catch {
    // Response wasn't JSON — keep going so the status path is informative.
  }

  if (!r.ok) {
    const detail =
      (data as { detail?: string } | null)?.detail ??
      `Request failed (${r.status}).`;
    throw new AuthApiError(r.status, detail);
  }

  return data as T;
}
