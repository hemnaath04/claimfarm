"use client";

import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";

export default function ResetPage() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? ""}/auth/reset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      setSent(true);
      toast.success("If an account exists for that email, a reset link is on its way.");
    } catch {
      toast.error("Could not send reset email. Try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card className="glass">
      <CardContent className="p-7">
        {sent ? (
          <>
            <h1 className="text-xl font-semibold">Check your inbox</h1>
            <p className="mt-3 text-sm text-muted-foreground">
              If an account exists for <span className="text-foreground">{email}</span>, we just
              sent it a password-reset link. The link expires in 1 hour.
            </p>
            <Link href="/auth/sign-in" className="mt-6 inline-block text-sm text-primary hover:underline">
              Back to sign in →
            </Link>
          </>
        ) : (
          <>
            <h1 className="text-xl font-semibold">Reset your password</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              We&apos;ll email you a link to set a new one.
            </p>
            <form onSubmit={onSubmit} className="mt-6 space-y-4">
              <div>
                <label className="text-xs uppercase tracking-wider text-muted-foreground">Email</label>
                <Input
                  required
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="mt-1.5 bg-card/40"
                />
              </div>
              <Button
                disabled={busy}
                type="submit"
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
              >
                {busy ? "Sending…" : "Send reset link"}
              </Button>
            </form>
          </>
        )}
      </CardContent>
    </Card>
  );
}
