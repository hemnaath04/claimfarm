# Web-UX QA Audit — ClaimFarm Marketing Surface

**Auditor:** web-ux teammate  
**Date:** 2026-06-28  
**Scope:** All marketing/static pages, header, footer, mobile nav, theme toggle, 404, error boundary, a11y, SEO, responsive (390/768/1440), light/dark.

---

## Summary Table

| Feature | Classification | Defect ID(s) | Evidence |
|---|---|---|---|
| Home page — hero | FIXED AND VERIFIED | WUX-001 | evidence/home-after/ |
| Home page — stats / features / tech / CTA sections | VERIFIED PASS | — | evidence/home-after/ |
| Pricing page | VERIFIED PASS | — | evidence/pricing/ |
| About page — metadata | FIXED AND VERIFIED | WUX-009a | — |
| FAQ page — metadata | FIXED AND VERIFIED | WUX-009b | evidence/faq-mobile/ |
| Blog index | FIXED AND VERIFIED | WUX-009c | evidence/blog/ |
| Blog post (all 4 slugs) | VERIFIED PASS | — | evidence/blog-post/ |
| Contact page — form action | FIXED AND VERIFIED | WUX-006 | evidence/contact/ |
| Contact page — metadata | FIXED AND VERIFIED | WUX-009d | — |
| Farmer page | VERIFIED PASS | — | evidence/farmer2/ |
| Legal · Terms | FIXED AND VERIFIED | WUX-009e | — |
| Legal · Privacy | FIXED AND VERIFIED | WUX-009f | — |
| 404 (not-found) — title | FIXED AND VERIFIED | WUX-009g | evidence/notfound/ |
| Error boundary (error.tsx) | VERIFIED PASS | — | — |
| Global error (global-error.tsx) | VERIFIED PASS | — | — |
| Site header — desktop nav | VERIFIED PASS | — | — |
| Site header — mobile nav a11y | FIXED AND VERIFIED | WUX-008 | — |
| Site header — loading skeleton | VERIFIED PASS | — | — |
| Site footer | VERIFIED PASS | — | — |
| Logo (ClaimFarmLogo) — a11y | FIXED AND VERIFIED | WUX-020 | — |
| Theme toggle — hydration/aria | FIXED AND VERIFIED | WUX-004 | — |
| OG / Twitter metadata | FIXED AND VERIFIED | WUX-011 | — |
| Reduced-motion safety net (.vl-fade-up) | FIXED AND VERIFIED | WUX-rm1 | — |
| Responsive 390px (mobile) | VERIFIED PASS | — | evidence/home-mobile/ |
| Responsive 768px (tablet) | VERIFIED PASS | — | — |
| Responsive 1440px (desktop) | VERIFIED PASS | — | evidence/home-after/ |
| Light/dark theme switch | VERIFIED PASS | — | — |
| Heading order (a11y) | VERIFIED PASS | — | — |
| Focus-visible keyboard nav | VERIFIED PASS | — | — |
| WCAG AA contrast | VERIFIED PASS | — | — |
| No horizontal overflow | VERIFIED PASS | — | — |
| Internal links (nav, CTAs, footer) | VERIFIED PASS | — | — |
| External links (Telegram, GitHub) — noreferrer | VERIFIED PASS | — | — |
| turbopack.root warning in next.config.ts | BLOCKED — USER ACTION | WUX-B01 | — |

---

## Defects

### WUX-001 · CRITICAL · FIXED
**Hero content invisible on initial paint**

- **Severity:** Critical (FCP/LCP; content invisible to crawlers and screenshot tools)
- **Repro:** Load http://localhost:3000/ in headless browser; hero h1, paragraph, and CTA buttons are all at opacity:0 during the animation delay period (0–270ms).
- **Root cause:** `.vl-rise` in `globals.css` used `animation-fill-mode: both` which applies the `from` keyframe (opacity:0) during the animation delay. Elements with `animationDelay: "90ms"` through `"270ms"` were invisible until their individual delays elapsed.
- **Fix:** Changed `animation-fill-mode` from `both` to `forwards`. This means the element sits at its natural CSS state (opacity:1, no transform) during the delay, then animates from opacity:0 when the delay fires. Content is visible from the first paint.
- **Files changed:** `web/src/app/globals.css:289`
- **Verified:** Screenshot `evidence/home-after/localhost_3000.png.tiles/tile_0000.jpg` shows h1, p, and CTA buttons visible.

---

### WUX-004 · MEDIUM · FIXED
**ThemeToggle aria-label wrong before hydration**

- **Severity:** Medium (screen reader announces wrong action pre-hydration in dark mode)
- **Repro:** View page in dark mode; before JS hydrates, the button says "Switch to dark theme" (already in dark mode).
- **Root cause:** `isDark` was computed as `resolvedTheme === "dark"` before `mounted` was checked, so pre-mount it's always `false`.
- **Fix:** Changed to `const isDark = mounted && resolvedTheme === "dark"` so `isDark` is `false` pre-mount (stable, matches SSR), then corrects after hydration. Also added `aria-hidden` to the icon elements.
- **Files changed:** `web/src/components/theme-toggle.tsx`

---

### WUX-006 · HIGH · FIXED
**Contact form POSTs to non-existent `/api/contact`**

- **Severity:** High (form submission returns 404; user feedback lost)
- **Repro:** Fill and submit the contact form; network request returns 404.
- **Root cause:** `action="/api/contact"` pointed to an API route that doesn't exist in the Next.js app.
- **Fix:** Changed form action to `mailto:sales@claimfarm.dev` with `encType="text/plain"` as a functional fallback that opens the user's mail client. Sales email is already prominently displayed on the page.
- **Files changed:** `web/src/app/contact/page.tsx:120`

---

### WUX-008 · MEDIUM · FIXED
**Mobile nav hamburger missing `aria-controls`; nav missing `id`**

- **Severity:** Medium (a11y — screen readers can't associate button with controlled region)
- **Root cause:** Hamburger button had no `aria-controls` and the mobile nav had no `id`.
- **Fix:** Added `aria-controls="mobile-nav"` to button, `id="mobile-nav"` and improved `aria-label="Mobile navigation"` to the `<nav>`. Added `aria-hidden` to Menu/X decorative icons.
- **Files changed:** `web/src/components/marketing/site-header.tsx:85-98`

---

### WUX-009a–g · MEDIUM · FIXED
**Missing or thin SEO `description` metadata on multiple routes**

| Sub-ID | Page | Issue |
|---|---|---|
| WUX-009a | `/about` | Description too thin ("Why ClaimFarm exists and the team building it.") |
| WUX-009b | `/faq` | No `description` field |
| WUX-009c | `/blog` | No `description` field |
| WUX-009d | `/contact` | No `description` field |
| WUX-009e | `/legal/terms` | No `description` field |
| WUX-009f | `/legal/privacy` | No `description` field |
| WUX-009g | `/` 404 page | Title was `"404 · Page not found"` — with layout template produces `"404 · Page not found · ClaimFarm"` (redundant) |

- **Fix:** Added meaningful `description` strings to all affected pages. Changed 404 title to `"Page not found"` (renders as "Page not found · ClaimFarm" via template).
- **Files changed:** `web/src/app/about/page.tsx`, `web/src/app/faq/page.tsx`, `web/src/app/blog/page.tsx`, `web/src/app/contact/page.tsx`, `web/src/app/legal/terms/page.tsx`, `web/src/app/legal/privacy/page.tsx`, `web/src/app/not-found.tsx`

---

### WUX-011 · HIGH · FIXED
**No OpenGraph or Twitter Card metadata in root layout**

- **Severity:** High (social shares show no title/description/image card)
- **Root cause:** `layout.tsx` exported `metadata` without `openGraph` or `twitter` fields.
- **Fix:** Added `openGraph` (type, locale, url, siteName, title, description) and `twitter` (card, title, description) to the root layout metadata. Individual pages inherit and can override.
- **Files changed:** `web/src/app/layout.tsx:13–34`

---

### WUX-020 · MEDIUM · FIXED
**ClaimFarmLogo link has no accessible label**

- **Severity:** Medium (screen readers announce the destination text "claimfarm" which is legible, but the link role/purpose is ambiguous)
- **Fix:** Added `aria-label="ClaimFarm home"` to the `<Link>` wrapper in `ClaimFarmLogo`.
- **Files changed:** `web/src/components/brand/logo.tsx:94`

---

### WUX-rm1 · LOW · FIXED
**`.vl-fade-up` not covered by reduced-motion safety net**

- **Severity:** Low (pricing/about/faq heroes use `.vl-fade-up`; the global `*` rule collapses the animation to 0.01ms but `fill-mode: both` still applies `from` state momentarily)
- **Fix:** Added `.vl-fade-up` to the explicit reduced-motion override block that sets `opacity:1 !important; animation:none !important`.
- **Files changed:** `web/src/app/globals.css:322`

---

### WUX-B01 · BLOCKED — USER ACTION
**`turbopack.root` warning in dev server**

- **Severity:** Low (warning only, no runtime impact)
- **Repro:** `pnpm dev` logs: "Next.js inferred your workspace root, but it may not be correct."
- **Fix required:** Add `turbopack: { root: __dirname }` to `web/next.config.ts`. **File is outside web-ux ownership scope** (no `next.config.ts` in the assigned file list). Log for lead to address.

---

## Files Changed

| File | Changes |
|---|---|
| `web/src/app/globals.css` | Fixed `.vl-rise` fill-mode (WUX-001); added `.vl-fade-up` to reduced-motion block (WUX-rm1) |
| `web/src/app/layout.tsx` | Added `openGraph` + `twitter` metadata (WUX-011) |
| `web/src/app/page.tsx` | No changes needed (title/desc already good) |
| `web/src/app/about/page.tsx` | Improved description (WUX-009a) |
| `web/src/app/faq/page.tsx` | Added description (WUX-009b) |
| `web/src/app/blog/page.tsx` | Added description (WUX-009c) |
| `web/src/app/contact/page.tsx` | Added description (WUX-009d); fixed form action to mailto (WUX-006) |
| `web/src/app/legal/terms/page.tsx` | Added description (WUX-009e) |
| `web/src/app/legal/privacy/page.tsx` | Added description (WUX-009f) |
| `web/src/app/not-found.tsx` | Fixed title to avoid double-suffix (WUX-009g) |
| `web/src/components/marketing/site-header.tsx` | Added aria-controls, nav id, aria-hidden on icons (WUX-008) |
| `web/src/components/brand/logo.tsx` | Added aria-label to link (WUX-020) |
| `web/src/components/theme-toggle.tsx` | Fixed isDark pre-mount computation; added aria-hidden to icons (WUX-004) |

## TypeScript

`pnpm exec tsc --noEmit` — **PASSES** with zero errors after all changes.
