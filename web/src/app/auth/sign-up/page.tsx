"use client";

import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { postAuthJson } from "@/lib/auth-fetch";

const FRIENDLY: Record<number, string> = {
  409: "That email is already registered. Try signing in instead.",
  422: "Please double-check your email and password — they didn't look valid.",
  429: "Too many sign-up attempts. Wait a minute and try again.",
};

export default function SignUpPage() {
  const [name, setName] = useState("");
  const [org, setOrg] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [conflict, setConflict] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setConflict(false);
    try {
      const data = await postAuthJson<{
        user_id: string;
        verification_url?: string;
      }>("/auth/sign-up", { name, org, email, password });
      if (data.verification_url) {
        toast.success("Account created — opening the verification link.");
        window.location.href = data.verification_url;
      } else {
        toast.success("Account created — check your email to verify.");
        window.location.href = "/auth/verify?sent=1";
      }
    } catch (err) {
      const e = err as { status?: number; detail?: string };
      if (e.status === 409) setConflict(true);
      const message =
        (e.status && FRIENDLY[e.status]) || e.detail || "Sign-up failed. Try again.";
      toast.error(message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card className="glass">
      <CardContent className="p-7">
        <h1 className="text-xl font-semibold">Start your ClaimFarm pilot</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Free for the first 100 filed claims. No card required.
        </p>

        {conflict ? (
          <div className="mt-4 rounded-md border border-amber-400/40 bg-amber-500/10 p-3 text-sm text-amber-100">
            That email is already registered.{" "}
            <Link href="/auth/sign-in" className="underline">
              Sign in
            </Link>{" "}
            or{" "}
            <Link href="/auth/reset" className="underline">
              reset your password
            </Link>
            .
          </div>
        ) : null}

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs uppercase tracking-wider text-muted-foreground">Name</label>
              <Input
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-1.5 bg-card/40"
              />
            </div>
            <div>
              <label className="text-xs uppercase tracking-wider text-muted-foreground">
                Organisation
              </label>
              <Input
                value={org}
                onChange={(e) => setOrg(e.target.value)}
                className="mt-1.5 bg-card/40"
              />
            </div>
          </div>
          <div>
            <label className="text-xs uppercase tracking-wider text-muted-foreground">Work email</label>
            <Input
              required
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1.5 bg-card/40"
            />
          </div>
          <div>
            <label className="text-xs uppercase tracking-wider text-muted-foreground">Password</label>
            <Input
              required
              type="password"
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1.5 bg-card/40"
            />
            <p className="mt-1.5 text-[11px] text-muted-foreground">
              Minimum 8 characters. We hash with Argon2id.
            </p>
          </div>
          <Button
            disabled={busy}
            type="submit"
            className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
          >
            {busy ? "Creating account…" : "Create account →"}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/auth/sign-in" className="text-primary hover:underline">
            Sign in
          </Link>
        </p>
        <p className="mt-3 text-center text-[11px] text-muted-foreground">
          By creating an account you agree to our{" "}
          <Link href="/legal/terms" className="underline">Terms</Link> and{" "}
          <Link href="/legal/privacy" className="underline">Privacy Policy</Link>.
        </p>
      </CardContent>
    </Card>
  );
}
