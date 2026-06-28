import Link from "next/link";
import { cn } from "@/lib/utils";

/**
 * "Verdant Claim" mark — a forest-green tile holding a harvest-yellow leaf
 * with a checkmark: leaf = farm, check = filed claim. Self-contained SVG,
 * scales cleanly from 20px (mobile header) to 128px (cover).
 */
export function ClaimFarmMark({
  size = 32,
  className,
}: {
  size?: number;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      role="img"
      aria-label="ClaimFarm"
      className={className}
    >
      <rect width="40" height="40" rx="11" fill="var(--forest-700)" />
      {/* leaf */}
      <path
        d="M20 8C26 13 28 22 20 31C12 22 14 13 20 8Z"
        fill="var(--harvest-400)"
      />
      {/* check — sits on the leaf, dark forest for strong contrast */}
      <path
        d="M15.6 20.4l3.2 3.2 6.6-7.8"
        stroke="var(--forest-900)"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/**
 * Full logo: mark + wordmark. `tone` controls wordmark color so it reads on
 * both ivory and forest surfaces. `suffix` adds e.g. "console" for the app.
 */
export function ClaimFarmLogo({
  href = "/",
  size = 32,
  tone = "ink",
  suffix,
  className,
}: {
  href?: string | null;
  size?: number;
  tone?: "ink" | "light";
  suffix?: string;
  className?: string;
}) {
  const inner = (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <ClaimFarmMark size={size} />
      <span
        className={cn(
          "font-bold tracking-[-0.02em] leading-none",
          tone === "light" ? "text-white" : "text-foreground"
        )}
        style={{ fontSize: Math.round(size * 0.66) }}
      >
        claimfarm
      </span>
      {suffix ? (
        <span
          className={cn(
            "text-[11px] font-medium uppercase tracking-[0.14em] leading-none",
            tone === "light" ? "text-white/70" : "text-muted-foreground"
          )}
        >
          {suffix}
        </span>
      ) : null}
    </span>
  );

  if (href === null) return inner;
  return (
    <Link href={href} className="inline-flex items-center rounded-md">
      {inner}
    </Link>
  );
}
