"use client";

import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

export default function SignInPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      // POSTs to the backend /auth/sign-in route. Backend is placeholder
      // and currently returns 200 with a stub session.
      const r = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? ""}/auth/sign-in`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        },
      );
      if (!r.ok) throw new Error(`sign-in failed: ${r.status}`);
      toast.success("Signed in (stub) — redirecting…");
      window.location.href = "/admin";
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "sign-in failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card className="glass">
      <CardContent className="p-7">
        <h1 className="text-xl font-semibold">Sign in</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Welcome back. Sign in to your ClaimFarm account.
        </p>

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <div>
            <label className="text-xs uppercase tracking-wider text-muted-foreground">Email</label>
            <Input
              required
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="mt-1.5 bg-card/40"
            />
          </div>
          <div>
            <div className="flex items-center justify-between">
              <label className="text-xs uppercase tracking-wider text-muted-foreground">
                Password
              </label>
              <Link href="/auth/reset" className="text-xs text-primary hover:underline">
                Forgot?
              </Link>
            </div>
            <Input
              required
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1.5 bg-card/40"
            />
          </div>
          <Button
            disabled={busy}
            type="submit"
            className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
          >
            {busy ? "Signing in…" : "Sign in →"}
          </Button>
        </form>

        <div className="my-6 flex items-center gap-3 text-xs text-muted-foreground">
          <Separator className="flex-1" />
          OR CONTINUE WITH
          <Separator className="flex-1" />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <Button variant="outline" disabled>
            Google (TODO)
          </Button>
          <Button variant="outline" disabled>
            Apple (TODO)
          </Button>
        </div>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          New here?{" "}
          <Link href="/auth/sign-up" className="text-primary hover:underline">
            Create an account
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
