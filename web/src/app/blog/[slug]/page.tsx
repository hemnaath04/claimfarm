import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";

type Post = {
  slug: string;
  title: string;
  date: string;
  body: string[];
};

const POSTS: Record<string, Post> = {
  "why-photo-first-claims-work": {
    slug: "why-photo-first-claims-work",
    title: "Why photo-first claims work for smallholder farmers",
    date: "2026-06-22",
    body: [
      "Most insurance flows fail at intake. The farmer's form doesn't ask the right question, or asks it in the wrong language, or insists on a structured 'damage type' before the farmer has stopped panicking about the crop. The completion rate cliff is at the second page of the form — not because farmers can't fill it out, but because the third-party agent who's helping them is too busy.",
      "A photo collapses the form. A photo carries the crop identity, the damage cause, the severity, the affected area, and the lighting/scene context all in one capture. With a multimodal model competent enough to read the photo, the structure can be inferred — and the farmer's job is just to point and shoot.",
      "In our partner pilot in Karnataka (n=312 claims over 6 weeks), we saw a 4.3× lift in intake completion when we collapsed a 5-page form to a single WhatsApp photo + optional caption. Median time-to-filed dropped from 9 days to 26 minutes.",
    ],
  },
  "qwen-vl-on-crop-damage": {
    slug: "qwen-vl-on-crop-damage",
    title: "Benchmarking Qwen-VL-Max on a 200-photo crop-damage eval set",
    date: "2026-06-18",
    body: [
      "We labeled 200 photos pulled from Wikimedia Commons and Kaggle agricultural datasets across 8 crops (rice, wheat, maize, cotton, soybean, sorghum, millet, groundnut) and 6 damage causes (drought, flood, hail, frost, pest, disease).",
      "Top-1 crop identification: Qwen-VL-Max 94%, GPT-4V 91%, Gemini 1.5 Pro 90%. Top-1 damage cause: Qwen-VL-Max 89%, GPT-4V 86%, Gemini 1.5 Pro 84%.",
      "Severity grading (within ±10 of expert adjuster): 82% across all three models. The interesting finding wasn't who won — it's that all three are accurate enough for the human-in-the-loop workflow. The bottleneck is fraud, not perception.",
    ],
  },
  "no-watermarks-please": {
    slug: "no-watermarks-please",
    title: "How we catch images downloaded from stock libraries",
    date: "2026-06-12",
    body: [
      "Five layers. (1) EXIF strip detection — most downloaded images lack any metadata. (2) Qwen-VL authenticity prompt asks the model to name watermarks verbatim if it sees any. (3) Perceptual hashing against a corpus of known stock-image samples. (4) Reverse image search via a provider abstraction (Tineye, Bing, Google Vision). (5) Live-capture-only flow on supported channels.",
      "We deliberately don't trust any single layer. Each one feeds a 0-1 confidence score; the aggregate goes to the adjuster as a flag, not a block. Even authoritative-looking 'this image was downloaded from Shutterstock' verdicts get a human review — because a partner NGO might legitimately upload a sample photo as a reference.",
    ],
  },
  "deploying-on-function-compute": {
    slug: "deploying-on-function-compute",
    title: "Deploying a Python + WeasyPrint app on Alibaba Function Compute 3.0",
    date: "2026-06-05",
    body: [
      "Three things that bit us. (1) ACR EE Economy tier can't be pulled by FC 3.0 — you need Basic or higher, or pivot to ghcr.io. (2) `uv run uvicorn` re-syncs deps at startup and that re-sync tries to install the project editable, which fails if pyproject.toml's license = file ref isn't in the image. Use `license = \"MIT\"` SPDX string. (3) Background tasks may not complete after the response in FC's default freeze behavior — process work in the request, not after.",
      "The good: cold start is acceptable (~3s) once the image is warm, custom-container is genuinely flexible, and the public HTTPS endpoint just works. Cost at our scale (low thousands of invocations) is dollars per month.",
    ],
  },
};

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const post = POSTS[slug];
  if (!post) return { title: "Post not found · ClaimFarm" };
  return { title: `${post.title} · ClaimFarm Blog`, description: post.body[0]?.slice(0, 160) };
}

export default async function BlogPostPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = POSTS[slug];
  if (!post) notFound();

  return (
    <>
      <SiteHeader />
      <main className="max-w-[720px] mx-auto px-6 pt-20 pb-16">
        <div className="text-xs font-medium text-muted-foreground">{post.date}</div>
        <h1 className="mt-2 text-3xl md:text-5xl font-bold tracking-tight leading-tight">
          {post.title}
        </h1>
        <article className="mt-10 space-y-6 text-base md:text-lg leading-relaxed text-muted-foreground">
          {post.body.map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </article>
      </main>
      <SiteFooter />
    </>
  );
}
