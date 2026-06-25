import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
});

const mono = JetBrains_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "ClaimFarm · Adjuster Console",
  description:
    "Triage smallholder farmer crop-insurance claims, triaged by Qwen-VL, Open-Meteo and DashVector.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${mono.variable} dark h-full antialiased`}
    >
      <body className="min-h-full">
        {children}
        <Toaster richColors closeButton position="bottom-right" />
      </body>
    </html>
  );
}
