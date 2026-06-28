import { cn } from "@/lib/utils";

export type StatusTone =
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "neutral";

const TONE: Record<
  StatusTone,
  { bg: string; fg: string; dot: string; ring: string }
> = {
  // Filled pills matching the Figma status badges. A dot is always rendered
  // so the status is legible without relying on color alone.
  success: { bg: "#218A57", fg: "#ffffff", dot: "#bdf7d4", ring: "#218A5733" },
  warning: { bg: "#D8951C", fg: "#191B18", dot: "#5c3d00", ring: "#D8951C33" },
  danger: { bg: "#C64B4B", fg: "#ffffff", dot: "#ffd9d9", ring: "#C64B4B33" },
  info: { bg: "#367EAE", fg: "#ffffff", dot: "#cfe6f6", ring: "#367EAE33" },
  neutral: { bg: "#F0E7D2", fg: "#5b5848", dot: "#9a9482", ring: "#0000000f" },
};

export function StatusBadge({
  tone = "neutral",
  children,
  className,
}: {
  tone?: StatusTone;
  children: React.ReactNode;
  className?: string;
}) {
  const t = TONE[tone];
  return (
    <span
      className={cn("vl-pill", className)}
      style={{ background: t.bg, color: t.fg, boxShadow: `0 0 0 1px ${t.ring}` }}
    >
      <span
        aria-hidden
        className="size-1.5 rounded-full"
        style={{ background: t.dot }}
      />
      {children}
    </span>
  );
}
