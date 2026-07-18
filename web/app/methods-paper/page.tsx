import type { Metadata } from "next";

import { loadRepoMarkdown } from "@/lib/content";
import { PUBLIC_SITE_ORIGIN } from "@/lib/site";

export const metadata: Metadata = {
  title: "Methods and limitations working paper",
  description:
    "IESET's citable working methods note: registration, evidence tiers, estimator floor, school scoring, machine-assisted production, and threats to validity.",
  alternates: { canonical: `${PUBLIC_SITE_ORIGIN}/methods-paper/` },
  openGraph: {
    title: "IESET methods and limitations working paper",
    description:
      "A public, unrefereed methods note documenting the framework and its remaining threats to validity.",
    url: `${PUBLIC_SITE_ORIGIN}/methods-paper/`,
    type: "article",
    siteName: "IESET",
  },
};

export default async function MethodsPaperPage() {
  const html = await loadRepoMarkdown("METHODS_PAPER.md");
  const scholarlyArticle = {
    "@context": "https://schema.org",
    "@type": "ScholarlyArticle",
    headline:
      "IESET: a registered, machine-assisted evidence framework for economic-policy claims",
    description:
      "Working methods and limitations note for the IESET framework.",
    datePublished: "2026-07-18",
    dateModified: "2026-07-18",
    version: "1.2.0",
    url: `${PUBLIC_SITE_ORIGIN}/methods-paper/`,
    author: {
      "@type": "Organization",
      name: "IESET",
      url: PUBLIC_SITE_ORIGIN,
    },
    publisher: {
      "@type": "Organization",
      name: "IESET",
      url: PUBLIC_SITE_ORIGIN,
    },
    isAccessibleForFree: true,
    creativeWorkStatus: "Public working paper; not peer-reviewed",
    license: "https://creativecommons.org/licenses/by/4.0/",
  };

  return (
    <div className="mx-auto max-w-[780px] px-8 py-10">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(scholarlyArticle) }}
      />
      <div className="prose-body" dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  );
}
