import { loadEvidenceTierAudit } from "@/lib/content";
import { loadPublicCensus } from "@/lib/stats";
import {
  PUBLIC_GITHUB_REPO,
  PUBLIC_SITE_ORIGIN,
} from "@/lib/site";

export const dynamic = "force-static";

export async function GET() {
  const census = loadPublicCensus();
  const audit = loadEvidenceTierAudit();

  return Response.json({
    "@context": "https://schema.org",
    "@type": "DataCatalog",
    name: "IESET economic policy research catalog",
    description:
      "Open hypothesis, policy, movement, and school-prediction records with registration, replication, evidence-tier, and estimator-floor metadata.",
    url: `${PUBLIC_SITE_ORIGIN}/evidence/`,
    sameAs: PUBLIC_GITHUB_REPO,
    license: "https://creativecommons.org/licenses/by/4.0/",
    isAccessibleForFree: true,
    peer_review_status: "not_peer_reviewed_by_default",
    production_method: "LLM-assisted under human direction",
    counts: census?.counts ?? null,
    evidence_summary: audit?.summary ?? null,
    dataset: [
      {
        "@type": "Dataset",
        name: "IESET hypothesis index",
        description:
          "Hypothesis claims, verdicts, evidence tiers, registration status, estimator-floor status, and canonical links.",
        distribution: {
          "@type": "DataDownload",
          encodingFormat: "application/json",
          contentUrl: `${PUBLIC_SITE_ORIGIN}/api/hypotheses.json`,
        },
      },
      {
        "@type": "Dataset",
        name: "IESET evidence quality ledger",
        description:
          "Record-level inclusion and exclusion reasons for featured, calibration, and archive tiers.",
        distribution: {
          "@type": "DataDownload",
          encodingFormat: "application/json",
          contentUrl: `${PUBLIC_SITE_ORIGIN}/evidence-tiers.json`,
        },
      },
      {
        "@type": "Dataset",
        name: "IESET school scoreboard",
        description:
          "Ranked schools and separately reported benchmark controls with strict attribution and integrity weights.",
        distribution: {
          "@type": "DataDownload",
          encodingFormat: "application/json",
          contentUrl: `${PUBLIC_SITE_ORIGIN}/api/scoreboard.json`,
        },
      },
      {
        "@type": "Dataset",
        name: "IESET public corpus census",
        description:
          "Definition-bearing counts for the tracked public research corpus.",
        distribution: {
          "@type": "DataDownload",
          encodingFormat: "application/json",
          contentUrl: `${PUBLIC_SITE_ORIGIN}/stats.json`,
        },
      },
    ],
  });
}
