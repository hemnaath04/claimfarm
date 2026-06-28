import Link from "next/link";
import type { Metadata } from "next";
import { ArrowUpRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";

export const metadata: Metadata = {
  title: "Blog · ClaimFarm",
  description:
    "Engineering and product writing about how ClaimFarm works — AI damage assessment, fraud detection, multilingual claims, and shipping on Alibaba Function Compute.",
};

const POSTS = [
  {
    slug: "why-photo-first-claims-work",
    title: "Why photo-first claims work for smallholder farmers",
    excerpt:
      "A photo carries more reliable evidence than a paper form filled in by a third party. Here's the data on intake completion when you collapse the form to a single image.",
    tag: "Product",
    readingTime: "6 min",
    date: "2026-06-22",
  },
  {
    slug: "qwen-vl-on-crop-damage",
    title: "Benchmarking Qwen-VL-Max on a 200-photo crop-damage eval set",
    excerpt:
      "We labeled 200 Wikimedia + Kaggle photos across 8 crops and 6 damage causes and put Qwen-VL-Max head-to-head with GPT-4V and Gemini 1.5 Pro. Numbers inside.",
    tag: "Engineering",
    readingTime: "11 min",
    date: "2026-06-18",
  },
  {
    slug: "no-watermarks-please",
    title: "How we catch images downloaded from stock libraries",
    excerpt:
      "Five layers of fraud detection, including a Qwen-VL prompt that names visible watermarks back to the adjuster.",
    tag: "Engineering",
    readingTime: "8 min",
    date: "2026-06-12",
  },
  {
    slug: "deploying-on-function-compute",
    title: "Deploying a Python + WeasyPrint app on Alibaba Function Compute 3.0",
    excerpt:
      "What worked, what didn't (looking at you, cross-account WhatsApp media URLs), and the Dockerfile that finally cold-started cleanly.",
    tag: "DevOps",
    readingTime: "10 min",
    date: "2026-06-05",
  },
];

export default function BlogIndex() {
  return (
    <div className="flex min-h-dvh flex-col">
      <SiteHeader />
      <main className="flex-1">
        {/* Editorial intro on a harvest band */}
        <section className="vl-harvest">
          <div className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
            <p className="vl-eyebrow text-forest-deep">Blog</p>
            <h1 className="vl-display mt-3 max-w-3xl">Notes from the build.</h1>
            <p className="mt-5 max-w-2xl text-lg leading-7 text-forest-deep/80">
              Engineering and product writing about how ClaimFarm works, what we
              measure, and what we&apos;ve learned shipping AI agents into the
              insurance loop.
            </p>
          </div>
        </section>

        <section className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
            {POSTS.map((p) => (
              <Link
                key={p.slug}
                href={`/blog/${p.slug}`}
                className="group block min-w-0 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60"
              >
                <Card className="h-full border border-border bg-card vl-shadow-card transition-shadow hover:vl-shadow-raised">
                  <CardContent className="flex h-full flex-col p-6">
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
                      <span className="rounded-full bg-forest/10 px-2.5 py-0.5 font-semibold text-forest">
                        {p.tag}
                      </span>
                      <span className="text-muted-foreground">{p.readingTime}</span>
                      <span aria-hidden className="text-muted-foreground">·</span>
                      <span className="text-muted-foreground">{p.date}</span>
                    </div>
                    <h2 className="mt-4 text-xl font-semibold leading-snug tracking-tight text-card-foreground">
                      {p.title}
                    </h2>
                    <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                      {p.excerpt}
                    </p>
                    <span className="mt-5 inline-flex items-center gap-1 text-sm font-medium text-forest">
                      Read note
                      <ArrowUpRight
                        aria-hidden
                        className="size-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
                      />
                    </span>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
