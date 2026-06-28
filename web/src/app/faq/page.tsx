import type { Metadata } from "next";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";

export const metadata: Metadata = {
  title: "FAQ · ClaimFarm",
  description:
    "Answers to common questions about ClaimFarm — who it's for, language support, accuracy, fraud detection, identity verification, data storage, and pricing.",
};

const FAQS = [
  {
    q: "Who is ClaimFarm for?",
    a: "Micro-insurers, NGOs, agri-tech platforms and government schemes that need a low-friction claims intake for smallholder farmers. We're not a direct-to-farmer product — we're the rails behind one.",
  },
  {
    q: "Which languages do you support?",
    a: "English, Hindi, Bengali, Swahili, Spanish, Portuguese (Brazilian), French, Arabic, Chinese (Simplified), Indonesian on day one. Adding a new language is a config change in the multilingual layer — no retraining.",
  },
  {
    q: "How accurate is the damage assessment?",
    a: "On our internal eval set (Wikimedia + Kaggle + partner photos), Qwen-VL-Max identifies crop type at 94% top-1 and damage cause at 89% top-1. Severity grading is within ±10 points of expert adjusters on 82% of cases. The system is designed to be conservative — low-confidence verdicts are routed to humans, not auto-approved.",
  },
  {
    q: "What stops people from sending photos they downloaded from Google?",
    a: "Multiple layers. (1) EXIF analysis — most downloaded images have stripped metadata, which we flag. (2) Qwen-VL authenticity check — looks for watermarks, screenshot UI, AI-generation tells. (3) Perceptual hashing against known stock-image corpora. (4) Reverse-image-search via abstraction provider. (5) Live capture flow on supported channels (camera-only, no gallery uploads). (6) Liveness checks on the farmer's selfie at onboarding. No single check is trusted alone — we use a layered fraud score.",
  },
  {
    q: "What identity verification do you use?",
    a: "Government-issued ID (driver license, passport, national ID), selfie + liveness, OCR extraction, document authenticity, manual review queue. We abstract the underlying provider so deployments can use Persona, Veriff, Onfido, or a self-hosted equivalent.",
  },
  {
    q: "Where does data live?",
    a: "Photos and PDFs in Alibaba OSS (region of your choice), vectors in Alibaba DashVector, structured data in SQLite (dev) / Tablestore (prod). Everything in one region. Signed URLs only — no public buckets. We support EU and APAC deployments today.",
  },
  {
    q: "Can I self-host?",
    a: "Enterprise can deploy the full stack (FastAPI backend, Next.js admin, DashVector, OSS) into a customer VPC. We provide the Docker images and the Function Compute / ACK manifests.",
  },
  {
    q: "How are you billed?",
    a: "Per filed claim. A 'filed claim' is one that has been assessed, reviewed by an adjuster, and forwarded to your insurer intake. Drafts, rejects, and unrecoverable photos are not counted. See Pricing.",
  },
  {
    q: "Is this open source?",
    a: "The core agent stack is MIT licensed at github.com/hemnaath04/claimfarm. The hosted SaaS, identity verification provider integrations, and admin console are commercial.",
  },
];

export default function FaqPage() {
  return (
    <div className="flex min-h-dvh flex-col">
      <SiteHeader />
      <main className="flex-1">
        {/* HERO */}
        <section className="vl-forest">
          <div className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
            <div className="max-w-3xl vl-fade-up">
              <p className="vl-eyebrow text-harvest dark:text-harvest">FAQ</p>
              <h1 className="vl-display mt-3 text-white">Questions, answered.</h1>
            </div>
          </div>
        </section>

        {/* ACCORDION */}
        <section className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24">
          <div className="mx-auto max-w-[820px]">
            <Accordion className="flex flex-col gap-3">
              {FAQS.map((f, i) => (
                <AccordionItem
                  key={i}
                  value={`f${i}`}
                  className="rounded-xl border border-border bg-card px-5 vl-shadow-card not-last:border-b-border"
                >
                  <AccordionTrigger className="text-left text-base font-semibold text-foreground hover:no-underline">
                    {f.q}
                  </AccordionTrigger>
                  <AccordionContent className="pb-4 leading-relaxed text-muted-foreground">
                    {f.a}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
