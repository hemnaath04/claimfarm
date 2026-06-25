"use client";

import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";

export default function SignUpPage() {
  const [name, setName] = useState("");
  const [org, setOrg] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      const r = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? ""}/auth/sign-up`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, org, email, password }),
        },
      );
      if (!r.ok) throw new Error(`sign-up failed: ${r.status}`);
      toast.success("Account created — check your email to verify.");
      window.location.href = "/auth/verify?sent=1";
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "sign-up failed");
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
