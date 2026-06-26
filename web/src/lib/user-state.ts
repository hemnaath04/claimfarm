"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "";

export type AuthUser = {
  user_id: string;
  email: string;
  name: string;
  role: string;
  org_id: string | null;
  email_verified: boolean;
  identity_status: string;
};

/**
 * Cookie-backed `/auth/me` check. Returns `null` while loading, a user
 * object once signed in, or `false` once we know they're signed out.
 */
export function useAuthUser() {
  const [user, setUser] = useState<AuthUser | null | false>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(`${API_BASE}/auth/me`, {
          credentials: "include",
          cache: "no-store",
        });
        if (cancelled) return;
        if (r.ok) {
          setUser((await r.json()) as AuthUser);
        } else {
          setUser(false);
        }
      } catch {
        if (!cancelled) setUser(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return user;
}

export async function signOut() {
  try {
    await fetch(`${API_BASE}/auth/sign-out`, {
      method: "POST",
      credentials: "include",
    });
  } catch {
    /* ignore — we still want to redirect */
  }
  window.location.href = "/";
}
