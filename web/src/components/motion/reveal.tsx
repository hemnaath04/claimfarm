"use client";

import { useEffect, useRef } from "react";

type RevealProps = React.HTMLAttributes<HTMLDivElement> & {
  /** Stagger offset in ms applied as transition-delay. */
  delay?: number;
};

/**
 * Scroll-reveal wrapper. Adds `.is-visible` when the element scrolls into
 * view (IntersectionObserver), then stops observing. Progressive
 * enhancement only — content is server-rendered; the global reduced-motion
 * rule and the layout's <noscript> block keep content visible when motion
 * is off or JS is unavailable. Use below the fold; above-the-fold content
 * should use the pure-CSS `.vl-rise` instead.
 */
export function Reveal({ delay = 0, className = "", style, children, ...rest }: RevealProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (typeof IntersectionObserver === "undefined") {
      el.classList.add("is-visible");
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            el.classList.add("is-visible");
            io.unobserve(el);
          }
        }
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={`reveal ${className}`}
      style={delay ? { transitionDelay: `${delay}ms`, ...style } : style}
      {...rest}
    >
      {children}
    </div>
  );
}
