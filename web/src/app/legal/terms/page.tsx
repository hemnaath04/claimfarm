import type { Metadata } from "next";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";

export const metadata: Metadata = { title: "Terms of Service · ClaimFarm" };

export default function TermsPage() {
  return (
    <>
      <SiteHeader />
      <main className="max-w-[800px] mx-auto px-6 pt-20 pb-16">
        <div className="text-xs font-semibold uppercase tracking-wider text-primary">Legal</div>
        <h1 className="mt-3 text-3xl md:text-4xl font-bold tracking-tight">Terms of Service</h1>
        <p className="mt-3 text-sm text-muted-foreground">Last updated: 2026-06-25</p>

        <div className="mt-10 space-y-6 text-muted-foreground leading-relaxed text-sm">
          <p>
            These Terms of Service ("Terms") govern your access to and use of the
            ClaimFarm website, dashboards, and APIs (the "Service"). By using the
            Service you agree to these Terms. This is a placeholder document
            generated for hackathon submission — production deployment requires
            review by qualified counsel in each jurisdiction of operation.
          </p>

          <h2 className="text-foreground font-semibold mt-8 text-lg">1. Account</h2>
          <p>
            You must be at least 18 years old (or the age of majority in your
            jurisdiction) and you may only use the Service if you have legal
            capacity to enter into a binding contract. You are responsible for
            anything that happens under your account.
          </p>

          <h2 className="text-foreground font-semibold mt-8 text-lg">2. Acceptable use</h2>
          <p>
            You will not use the Service to submit fraudulent claims, impersonate
            another person, scrape data, attempt to reverse engineer the AI
            models, or otherwise violate applicable law. ClaimFarm reserves the
            right to suspend or terminate accounts that violate this policy.
          </p>

          <h2 className="text-foreground font-semibold mt-8 text-lg">3. AI outputs</h2>
          <p>
            The Service uses AI models to assist with claim assessment.
            AI-generated outputs are advisory only and must be reviewed by a
            human adjuster before any insurance decision is made or
            communicated to a policyholder. ClaimFarm makes no warranty as to
            the accuracy of any individual AI output.
          </p>

          <h2 className="text-foreground font-semibold mt-8 text-lg">4. Identity verification</h2>
          <p>
            Some features require identity verification through a third-party
            provider. You consent to the collection, storage, and processing of
            your government-issued ID and biometric data (selfie / liveness) for
            the sole purpose of verifying that you are the person you claim to
            be.
          </p>

          <h2 className="text-foreground font-semibold mt-8 text-lg">5. Payments</h2>
          <p>
            Paid plans are billed monthly or annually as configured. Failure to
            pay may result in suspension. Refunds are not provided for partial
            usage of paid periods unless required by applicable law.
          </p>

          <h2 className="text-foreground font-semibold mt-8 text-lg">6. Liability</h2>
          <p>
            To the maximum extent permitted by law, ClaimFarm is not liable for
            any indirect, incidental, or consequential damages arising from your
            use of the Service. Our aggregate liability is capped at fees paid
            to us in the 12 months preceding the claim.
          </p>

          <h2 className="text-foreground font-semibold mt-8 text-lg">7. Changes</h2>
          <p>
            We may update these Terms from time to time. Material changes will
            be communicated by email or via in-product notice. Continued use of
            the Service after the changes take effect constitutes acceptance of
            the new Terms.
          </p>

          <h2 className="text-foreground font-semibold mt-8 text-lg">8. Contact</h2>
          <p>
            Questions about these Terms: <span className="text-foreground">legal@claimfarm.dev</span>
          </p>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
