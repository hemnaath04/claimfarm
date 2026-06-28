import type { Metadata } from "next";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";

export const metadata: Metadata = {
  title: "Terms of Service · ClaimFarm",
  description:
    "ClaimFarm Terms of Service — account requirements, acceptable use, AI output disclaimer, identity verification, payments, and liability.",
};

export default function TermsPage() {
  return (
    <div className="flex min-h-dvh flex-col">
      <SiteHeader />
      <main className="flex-1">
        <article className="mx-auto max-w-[720px] px-5 py-16 sm:px-8 sm:py-24">
          <p className="vl-eyebrow">Legal · Updated 2026-06-25</p>
          <h1 className="mt-3 text-4xl font-bold tracking-tight text-foreground">
            Terms of Service
          </h1>

          <div className="mt-10 space-y-6 text-base leading-7 text-foreground/90">
            <div className="rounded-3xl border border-border bg-muted/50 p-6 vl-shadow-card">
              <p className="text-sm leading-7 text-muted-foreground">
                These Terms of Service (&quot;Terms&quot;) govern your access to and use of the
                ClaimFarm website, dashboards, and APIs (the &quot;Service&quot;). By using the
                Service you agree to these Terms. This is a placeholder document
                generated for hackathon submission — production deployment requires
                review by qualified counsel in each jurisdiction of operation.
              </p>
            </div>

            <h2 className="pt-2 text-xl font-semibold text-foreground">1. Account</h2>
            <p>
              You must be at least 18 years old (or the age of majority in your
              jurisdiction) and you may only use the Service if you have legal
              capacity to enter into a binding contract. You are responsible for
              anything that happens under your account.
            </p>

            <h2 className="pt-2 text-xl font-semibold text-foreground">2. Acceptable use</h2>
            <p>
              You will not use the Service to submit fraudulent claims, impersonate
              another person, scrape data, attempt to reverse engineer the AI
              models, or otherwise violate applicable law. ClaimFarm reserves the
              right to suspend or terminate accounts that violate this policy.
            </p>

            <h2 className="pt-2 text-xl font-semibold text-foreground">3. AI outputs</h2>
            <p>
              The Service uses AI models to assist with claim assessment.
              AI-generated outputs are advisory only and must be reviewed by a
              human adjuster before any insurance decision is made or
              communicated to a policyholder. ClaimFarm makes no warranty as to
              the accuracy of any individual AI output.
            </p>

            <h2 className="pt-2 text-xl font-semibold text-foreground">4. Identity verification</h2>
            <p>
              Some features require identity verification through a third-party
              provider. You consent to the collection, storage, and processing of
              your government-issued ID and biometric data (selfie / liveness) for
              the sole purpose of verifying that you are the person you claim to
              be.
            </p>

            <h2 className="pt-2 text-xl font-semibold text-foreground">5. Payments</h2>
            <p>
              Paid plans are billed monthly or annually as configured. Failure to
              pay may result in suspension. Refunds are not provided for partial
              usage of paid periods unless required by applicable law.
            </p>

            <h2 className="pt-2 text-xl font-semibold text-foreground">6. Liability</h2>
            <p>
              To the maximum extent permitted by law, ClaimFarm is not liable for
              any indirect, incidental, or consequential damages arising from your
              use of the Service. Our aggregate liability is capped at fees paid
              to us in the 12 months preceding the claim.
            </p>

            <h2 className="pt-2 text-xl font-semibold text-foreground">7. Changes</h2>
            <p>
              We may update these Terms from time to time. Material changes will
              be communicated by email or via in-product notice. Continued use of
              the Service after the changes take effect constitutes acceptance of
              the new Terms.
            </p>

            <h2 className="pt-2 text-xl font-semibold text-foreground">8. Contact</h2>
            <p>
              Questions about these Terms:{" "}
              <span className="font-medium text-foreground">legal@claimfarm.dev</span>
            </p>
          </div>
        </article>
      </main>
      <SiteFooter />
    </div>
  );
}
