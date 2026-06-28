"use client";

import { useId } from "react";

type AuthFieldProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  hint?: React.ReactNode;
};

/**
 * Accessible labelled input for the auth forms: real <label htmlFor>, 44px
 * tall, visible focus ring, Verdant Ledger styling. Forwards all native
 * input props so existing form behavior (value, onChange, required, etc.)
 * is preserved unchanged.
 */
export function AuthField({ label, hint, className, ...props }: AuthFieldProps) {
  const id = useId();
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <label htmlFor={id} className="text-sm font-medium text-foreground">
          {label}
        </label>
        {hint}
      </div>
      <input
        id={id}
        className={
          "h-11 w-full rounded-lg border border-border bg-card px-3.5 text-[15px] text-foreground transition-colors placeholder:text-muted-foreground focus-visible:border-ring focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50 " +
          (className ?? "")
        }
        {...props}
      />
    </div>
  );
}
