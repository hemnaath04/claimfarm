"use client";

import Link from "next/link";
import { MailPlus } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import { cn } from "@/lib/utils";

export default function SignUpPage() {
  return (
    <div>
      <MailPlus className="size-10 text-primary" aria-hidden />
      <h1 className="mt-4 text-3xl font-bold tracking-tight text-foreground">
        ClaimFarm is invite-only
      </h1>
      <p className="mt-2 text-[15px] text-muted-foreground">
        Workspace access is by invitation. If your team uses ClaimFarm, ask your
        workspace owner to send you an invite — you&apos;ll get a link that lets
        you set a password and join.
      </p>
      <div className="mt-4">
        <StatusBadge tone="info">Invitation required</StatusBadge>
      </div>

      <a
        href="mailto:help@hemnaath.tech?subject=ClaimFarm%20access%20request"
        className={cn(buttonVariants(), "mt-6 h-11 w-full text-[15px]")}
      >
        Request access
      </a>
      <Link
        href="/auth/sign-in"
        className={cn(
          buttonVariants({ variant: "outline" }),
          "mt-3 h-11 w-full text-[15px]",
        )}
      >
        I already have an account
      </Link>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Have an invite link? Open it to{" "}
        <Link
          href="/auth/sign-in"
          className="font-medium text-primary hover:underline"
        >
          accept your invitation
        </Link>
        .
      </p>
    </div>
  );
}
