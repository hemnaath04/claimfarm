import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import { ThemeProvider } from "@/components/theme-provider";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://claimfarm-dashboard.vercel.app"),
  title: {
    default: "ClaimFarm · Photo-first crop insurance",
    template: "%s · ClaimFarm",
  },
  description:
    "Crop insurance that starts with a photo. ClaimFarm turns a farmer's photo into a filed claim — assessed by Qwen-VL, corroborated against weather, reviewed by a human adjuster.",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://claimfarm-dashboard.vercel.app",
    siteName: "ClaimFarm",
    title: "ClaimFarm · Photo-first crop insurance",
    description:
      "Crop insurance that starts with a photo. ClaimFarm turns a farmer's photo into a filed claim — assessed by Qwen-VL, corroborated against weather, reviewed by a human adjuster.",
  },
  twitter: {
    card: "summary_large_image",
    title: "ClaimFarm · Photo-first crop insurance",
    description:
      "Crop insurance that starts with a photo. ClaimFarm turns a farmer's photo into a filed claim — assessed by Qwen-VL, corroborated against weather, reviewed by a human adjuster.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${inter.variable} h-full antialiased`}
    >
      <head>
        {/* Reveal everything if JS is unavailable so no content is hidden. */}
        <noscript>
          {/* eslint-disable-next-line react/no-danger */}
          <style
            dangerouslySetInnerHTML={{
              __html:
                ".reveal{opacity:1!important;transform:none!important}.vl-rise{opacity:1!important;animation:none!important}",
            }}
          />
        </noscript>
      </head>
      <body className="min-h-full">
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem
          disableTransitionOnChange
        >
          {children}
          <Toaster richColors closeButton position="bottom-right" />
        </ThemeProvider>
      </body>
    </html>
  );
}
