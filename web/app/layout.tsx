import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import { Topbar } from "@/components/layout/Topbar";
import { Footer } from "@/components/layout/Footer";
import {
  PUBLIC_CONTACT_EMAIL,
  PUBLIC_GITHUB_REPO,
  PUBLIC_SITE_ORIGIN,
  PUBLIC_X_PROFILE,
} from "@/lib/site";

export const metadata: Metadata = {
  metadataBase: new URL(PUBLIC_SITE_ORIGIN),
  title: {
    default: "IESET — empirically-grounded economic policy framework",
    template: "%s · IESET",
  },
  description:
    "An open empirical framework for contemporary economic policy questions. Results are reproducible research artifacts, not peer-reviewed findings by default.",
  alternates: {
    types: {
      "application/rss+xml": "/feed.xml",
    },
  },
  applicationName: "IESET",
  authors: [{ name: "IESET", url: PUBLIC_SITE_ORIGIN }],
  creator: "IESET",
  publisher: "IESET",
  category: "economic policy research",
  keywords: [
    "economic policy",
    "pre-registration",
    "falsification",
    "causal inference",
    "political economy",
    "replication",
    "open research",
  ],
  openGraph: {
    type: "website",
    locale: "en_US",
    url: PUBLIC_SITE_ORIGIN,
    siteName: "IESET",
    title: "IESET — empirically-grounded economic policy framework",
    description:
      "Pre-registered economic claims scored against pinned public data. Open specs, replication code, and integrity-gated scoreboard.",
  },
  twitter: {
    card: "summary_large_image",
    site: "@IESETorg",
    title: "IESET — empirically-grounded economic policy framework",
    description:
      "Pre-registered economic claims scored against pinned public data.",
  },
  robots: {
    index: true,
    follow: true,
  },
  other: {
    "llms-txt": `${PUBLIC_SITE_ORIGIN}/llms.txt`,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const siteJsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Organization",
        "@id": `${PUBLIC_SITE_ORIGIN}/#organization`,
        name: "IESET",
        alternateName:
          "Institute for Empirical Study of Economic Thought",
        url: PUBLIC_SITE_ORIGIN,
        sameAs: [PUBLIC_GITHUB_REPO, PUBLIC_X_PROFILE],
        description:
          "Open pre-registration-first framework for empirical economic policy questions.",
        email: `mailto:${PUBLIC_CONTACT_EMAIL}`,
        contactPoint: {
          "@type": "ContactPoint",
          email: PUBLIC_CONTACT_EMAIL,
          contactType: "public engagement",
        },
        publishingPrinciples: `${PUBLIC_SITE_ORIGIN}/methodology/`,
        ethicsPolicy: `${PUBLIC_SITE_ORIGIN}/disclosure/`,
        correctionsPolicy: `${PUBLIC_SITE_ORIGIN}/contribute/`,
      },
      {
        "@type": "WebSite",
        "@id": `${PUBLIC_SITE_ORIGIN}/#website`,
        name: "IESET",
        alternateName:
          "Institute for Empirical Study of Economic Thought",
        url: PUBLIC_SITE_ORIGIN,
        publisher: {
          "@id": `${PUBLIC_SITE_ORIGIN}/#organization`,
        },
        inLanguage: "en",
        license: "https://creativecommons.org/licenses/by/4.0/",
      },
    ],
  };

  return (
    <html lang="en">
      <body>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(siteJsonLd) }}
        />
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
