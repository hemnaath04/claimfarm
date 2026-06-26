import type { Metadata } from "next";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";

export const metadata: Metadata = { title: "Privacy Policy · ClaimFarm" };

export default function PrivacyPage() {
  return (
    <>
      <SiteHeader />
      <main className="max-w-[800px] mx-auto px-6 pt-20 pb-16">
        <div className="text-xs font-semibold uppercase tracking-wider text-primary">Legal</div>
        <h1 className="mt-3 text-3xl md:text-4xl font-bold tracking-tight">Privacy Policy</h1>
        <p className="mt-3 text-sm text-muted-foreground">Last updated: 2026-06-25</p>

        <div className="mt-10 space-y-6 text-muted-foreground leading-relaxed text-sm">
          <p>
            This Privacy Policy describes how ClaimFarm ("we", "us") collects,
            uses, and discloses information about you. This is a placeholder
            document; production deployment requires review by qualified
            counsel for GDPR (EU), DPDP (India), PIPL (China), LGPD (Brazil),
            and CCPA (California) compliance.
          </p>

          <h2 className="text-foreground font-semibold mt-8 text-lg">Data we collect</h2>
          <ul className="list-disc list-inside space-y-1.5">
            <li>Account data: name, email, organization, phone, role.</li>
            <li>Claim data: crop photos, narrative text, GPS, EXIF, capture time.</li>
            <li>
              Identity-verification data: government-issued ID image, selfie,
              liveness video frames, OCR-extracted fields.
            </li>
            <li>
              Usage data: actions taken in the dashboard, claim decision history,
              IP address, user-agent, timestamps.
            </li>
          </ul>

          <h2 className="text-foreground font-semibold mt-8 text-lg">How we use data</h2>
          <ul className="list-disc list-inside space-y-1.5">
            <li>Provide and operate the Service (assess claims, file with insurer).</li>
            <li>Detect and prevent fraud (perceptual hashing, similarity search).</li>
            <li>Improve our AI models in aggregate, never on identifiable individuals.</li>
            <li>Comply with legal obligations.</li>
          </ul>

          <h2 className="text-foreground font-semibold mt-8 text-lg">Storage and security</h2>
          <p>
            Photos and PDFs are stored in Alibaba OSS with server-side encryption
            and signed-URL access only. Identity documents are stored in a
            separate, more restricted bucket with shorter signed-URL TTL and
            stricter access logging. Vectors live in Alibaba DashVector. All
            communication with our APIs is over HTTPS.
          </p>

          <h2 className="text-foreground font-semibold mt-8 text-lg">Sharing</h2>
          <p>
            We share claim data with your designated insurer for the sole purpose
            of filing claims. We use the following sub-processors: Alibaba Cloud
            (compute, storage, vector DB), Qwen Cloud (AI inference), Twilio /
            Bird / Telegram (messaging), Persona / Veriff / Onfido
            (configurable identity verification), Paddle / LemonSqueezy /
            Razorpay (configurable payments). A current
            sub-processor list is maintained at /legal/subprocessors.
          </p>

          <h2 className="text-foreground font-semibold mt-8 text-lg">Your rights</h2>
          <p>
            You may request access to, correction of, or deletion of your data
            by emailing <span className="text-foreground">privacy@claimfarm.dev</span>. We respond
            within 30 days. You also have the right to data portability and to
            object to certain processing.
          </p>

          <h2 className="text-foreground font-semibold mt-8 text-lg">Retention</h2>
          <p>
            Claim photos are retained for 7 years (default insurance regulatory
            window). Identity documents are retained for 5 years after account
            closure and then deleted, or sooner upon request unless retention is
            required by law. Audit logs are retained for 3 years.
          </p>

          <h2 className="text-foreground font-semibold mt-8 text-lg">Contact</h2>
          <p>privacy@claimfarm.dev</p>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
