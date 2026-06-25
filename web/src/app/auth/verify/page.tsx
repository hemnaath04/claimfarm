import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";

export default function VerifyPage() {
  return (
    <Card className="glass">
      <CardContent className="p-7 text-center">
        <div className="text-5xl">📬</div>
        <h1 className="mt-4 text-xl font-semibold">Verify your email</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          We just sent you a verification link. Click it to activate your
          account. Didn&apos;t get it? Check spam, or{" "}
          <Link href="/auth/sign-up" className="text-primary hover:underline">
            resend
          </Link>
          .
        </p>
        <p className="mt-6 text-xs text-muted-foreground">
          Link expires in 24 hours.
        </p>
      </CardContent>
    </Card>
  );
}
