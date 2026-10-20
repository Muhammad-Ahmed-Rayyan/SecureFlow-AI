import "./globals.css";
import type { Metadata } from "next";
import localFont from "next/font/local";
import TopBar from "@/components/layout/TopBar";
import FloatingNav from "@/components/layout/FloatingNav";

const sans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-sans",
  display: "swap",
});

const mono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "SecureFlow AI | Autonomous Vulnerability Remediation",
  description: "Scanner findings in, validated draft pull requests out. Remediate application security backlogs in minutes.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable}`}>
      <body className="bg-space min-h-screen relative overflow-x-hidden text-ink font-sans selection:bg-accent/30 selection:text-white">
        <div className="stars" aria-hidden="true" />
        <TopBar />
        <main className="relative z-10 pb-32">{children}</main>
        <FloatingNav />
      </body>
    </html>
  );
}
