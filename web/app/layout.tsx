import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import { Topbar } from "@/components/layout/Topbar";
import { Footer } from "@/components/layout/Footer";

export const metadata: Metadata = {
  title: {
    default: "IESET — empirically-grounded economic policy framework",
    template: "%s · IESET",
  },
  description:
    "An open empirical framework for contemporary economic policy questions. Results are reproducible research artifacts, not peer-reviewed findings by default.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Topbar />
        {children}
        <Footer />
        {/* Cloudflare Web Analytics — first-party, cookie-less, GDPR-friendly. */}
        <Script
          src="https://static.cloudflareinsights.com/beacon.min.js"
          data-cf-beacon='{"token": "ac7593aeb84a443c889566add26504cd"}'
          strategy="afterInteractive"
        />
      </body>
    </html>
  );
}
