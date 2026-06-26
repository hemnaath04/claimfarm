"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

function VerifyInner() {
  const params = useSearchParams();
  const status = params.get("status");
  const error = params.get("error");

  if (status === "ok") {
    return (
      <Card className="glass">
        <CardContent className="p-7 text-center">
          <div className="text-5xl">✓</div>
          <h1 className="mt-4 text-xl font-semibold">
            Email <span className="neon-text">verified</span>
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Your account is fully activated. You can now file claims and invite
            adjusters to your organisation.
          </p>
          <div className="mt-6 flex justify-center gap-2">
            <Link href="/dashboard">
              <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
                Go to dashboard
              </Button>
            </Link>
            <Link href="/admin">
              <Button variant="outline">Open adjuster console</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    const messages: Record<string, string> = {
      expired:
        "That verification link has expired or was already used. Try signing in and we'll send a fresh one.",
      unknown:
        "We couldn't match that link to an account. It may have been deleted.",
    };
    return (
      <Card className="glass">
        <CardContent className="p-7 text-center">
          <div className="text-5xl">!</div>
          <h1 className="mt-4 text-xl font-semibold">Link no longer valid</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            {messages[error] ?? "Something went wrong verifying that link."}
          </p>
          <Link
            href="/auth/sign-in"
            className="mt-6 inline-block text-sm text-primary hover:underline"
          >
            Back to sign in →
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass">
      <CardContent className="p-7 text-center">
        <div className="text-5xl">📬</div>
        <h1 className="mt-4 text-xl font-semibold">Verify your email</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          We just sent you a verification link. Click it to activate your
          account. Didn&apos;t get it? Check spam, or{" "}
          <Link href="/auth/sign-up" className="text-primary hover:underline">
            resend
          </Link>
          .
        </p>
        <p className="mt-6 text-xs text-muted-foreground">
          Link expires in 24 hours.
        </p>
      </CardContent>
    </Card>
  );
}

export default function VerifyPage() {
  return (
    <Suspense fallback={null}>
      <VerifyInner />
    </Suspense>
  );
}
