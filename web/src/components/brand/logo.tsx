import Link from "next/link";
import { cn } from "@/lib/utils";

/**
 * ClaimFarm mark — harvest-yellow rounded tile holding a sky-blue leaf set
 * behind a forest-green leaf with an ivory checkmark (leaf = farm, check =
 * filed claim). Fixed brand colors so it reads on any surface. Self-contained
 * SVG, scales cleanly from 20px (mobile header) to 128px (cover).
 */
export function ClaimFarmMark({
  size = 32,
  className,
}: {
  size?: number;
  className?: string;
}) {
  // Almond leaf, upright + centered on (20,20); the group is rotated so the
  // tip points to the upper-right, matching the brand artwork.
  const leaf = "M20 5.5C28.5 11.5 28.5 28.5 20 34.5C11.5 28.5 11.5 11.5 20 5.5Z";
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
      <rect width="40" height="40" rx="10.5" fill="#F4C95D" />
      <g transform="rotate(-38 20 20)">
        {/* sky-blue leaf set slightly behind */}
        <path d={leaf} transform="translate(2.3 2.1)" fill="#7FB3D2" />
        {/* forest-green leaf on top */}
        <path d={leaf} fill="#1F6E4E" />
      </g>
      {/* ivory checkmark, near-upright over the leaf */}
      <path
        d="M14.8 20.6l3.6 3.6 7.2-8.4"
        transform="rotate(-6 20 20)"
        stroke="#FFFCF5"
        strokeWidth="3"
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
