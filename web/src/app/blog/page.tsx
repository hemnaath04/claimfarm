import Link from "next/link";
import type { Metadata } from "next";
import { Card, CardContent } from "@/components/ui/card";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";

export const metadata: Metadata = { title: "Blog · ClaimFarm" };

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
    <>
      <SiteHeader />
      <main className="max-w-[1080px] mx-auto px-6 pt-20 pb-16">
        <div className="text-xs font-semibold uppercase tracking-wider text-primary">Blog</div>
        <h1 className="mt-3 text-4xl md:text-5xl font-bold tracking-tight">
          Notes from the build.
        </h1>
        <p className="mt-4 text-muted-foreground max-w-2xl">
          Engineering and product writing about how ClaimFarm works, what we
          measure, and what we've learned shipping AI agents into the
          insurance loop.
        </p>

        <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-4">
          {POSTS.map((p) => (
            <Link key={p.slug} href={`/blog/${p.slug}`}>
              <Card className="glass hover:ring-1 hover:ring-primary/40 transition cursor-pointer h-full">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 text-xs">
                    <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">
                      {p.tag}
                    </span>
                    <span className="text-muted-foreground">{p.readingTime}</span>
                    <span className="text-muted-foreground">·</span>
                    <span className="text-muted-foreground">{p.date}</span>
                  </div>
                  <h3 className="mt-3 text-lg font-semibold leading-snug">
                    {p.title}
                  </h3>
                  <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                    {p.excerpt}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
