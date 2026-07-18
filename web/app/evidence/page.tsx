import type { Metadata } from "next";
import Link from "next/link";

import {
  loadAllHypotheses,
  loadEvidenceTierAudit,
  scoreAllPositions,
} from "@/lib/content";
import { loadPublicCensus } from "@/lib/stats";
import { PUBLIC_GITHUB_REPO, PUBLIC_SITE_ORIGIN } from "@/lib/site";

export const metadata: Metadata = {
  title: "Evidence quality ledger",
  description:
    "IESET evidence tiers, estimator-floor exclusions, registration status, reference set, external-review status, and machine-readable audit endpoints.",
  alternates: { canonical: `${PUBLIC_SITE_ORIGIN}/evidence/` },
  openGraph: {
    title: "IESET evidence quality ledger",
    description:
      "Every public-evidence inclusion and exclusion rule, with current counts and a small balanced reference set.",
    url: `${PUBLIC_SITE_ORIGIN}/evidence/`,
    type: "website",
    siteName: "IESET",
  },
};

const NUMBER = new Intl.NumberFormat("en-US");

function fmt(value: number | undefined): string {
  return NUMBER.format(value ?? 0);
}

function label(value: string): string {
  return value.replace(/_/g, " ");
}

export default async function EvidencePage() {
  const audit = loadEvidenceTierAudit();
  const census = loadPublicCensus();
  const [hypotheses, scores] = await Promise.all([
    loadAllHypotheses(),
    scoreAllPositions(),
  ]);

  if (!audit) {
    return (
      <div className="mx-auto max-w-[780px] px-8 py-10">
        <h1 className="text-[32px] font-semibold">Evidence quality ledger</h1>
        <p className="text-muted">
          The generated evidence audit is unavailable in this build.
        </p>
      </div>
    );
  }

  const hypothesisIndex = new Map(
    hypotheses.map((hypothesis) => [
      hypothesis.hypothesis_id,
      hypothesis,
    ])
  );
  const rankedSchools = scores.filter(
    (score) => score.scoreboard_role === "school"
  );
  const strictSchoolSignals = rankedSchools.filter(
    (score) =>
      score.integrity_score_signal === "positive_signal" ||
      score.integrity_score_signal === "negative_signal"
  );
  const counts = census?.counts;
  const estimatorFailures = Object.entries(
    audit.summary.estimator_floor_failures
  ).sort((a, b) => b[1] - a[1]);
  const exclusions = Object.entries(audit.summary.exclusion_counts).sort(
    (a, b) => b[1] - a[1]
  );

  const datasetJsonLd = {
    "@context": "https://schema.org",
    "@type": "Dataset",
    name: "IESET economic policy hypothesis and evidence corpus",
    alternateName: "IESET evidence quality ledger",
    description:
      "Machine-readable economic-policy hypothesis registry with strict git registration status, evidence tiers, estimator-floor exclusions, verdicts, policies, movements, and school-level prediction links. Results are research artifacts and are not peer-reviewed by default.",
    url: `${PUBLIC_SITE_ORIGIN}/evidence/`,
    sameAs: PUBLIC_GITHUB_REPO,
    creator: {
      "@type": "Organization",
      name: "IESET",
      url: PUBLIC_SITE_ORIGIN,
    },
    license: "https://creativecommons.org/licenses/by/4.0/",
    isAccessibleForFree: true,
    version: "2",
    keywords: [
      "economic policy",
      "pre-registration",
      "falsification",
      "causal inference",
      "political economy",
      "open data",
    ],
    variableMeasured: [
      "registration status",
      "evidence tier",
      "estimator-floor status",
      "hypothesis verdict",
      "school prediction outcome",
    ],
    distribution: [
      {
        "@type": "DataDownload",
        name: "Corpus census",
        encodingFormat: "application/json",
        contentUrl: `${PUBLIC_SITE_ORIGIN}/stats.json`,
      },
      {
        "@type": "DataDownload",
        name: "Evidence tier ledger",
        encodingFormat: "application/json",
        contentUrl: `${PUBLIC_SITE_ORIGIN}/evidence-tiers.json`,
      },
      {
        "@type": "DataDownload",
        name: "Hypothesis index",
        encodingFormat: "application/json",
        contentUrl: `${PUBLIC_SITE_ORIGIN}/api/hypotheses.json`,
      },
      {
        "@type": "DataDownload",
        name: "Scoreboard",
        encodingFormat: "application/json",
        contentUrl: `${PUBLIC_SITE_ORIGIN}/api/scoreboard.json`,
      },
    ],
  };

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(datasetJsonLd) }}
      />

      <p className="mb-2 text-[12px] font-semibold uppercase tracking-wider text-muted">
        Public audit
      </p>
      <h1 className="m-0 text-[34px] font-semibold tracking-[-0.02em]">
        Evidence quality ledger
      </h1>
      <p className="mt-4 max-w-[860px] text-[17px] leading-[1.6] text-muted">
        This page publishes the rules that decide which records can support a
        headline claim. Corpus size is not evidence quality: strict
        registration, a real replication, a sharpened falsification rule, and
        the estimator floor all have to pass before a result enters the public
        evidence set.
      </p>

      <section className="mt-8 rounded border border-amber bg-[#fff8e8] p-5">
        <h2 className="m-0 text-[17px] font-semibold">
          Current school-level conclusion
        </h2>
        <p className="mt-2 m-0 max-w-[900px] text-[14px] leading-[1.65] text-ink">
          {strictSchoolSignals.length === 0
            ? `No ranked school has a positive or negative strict integrity signal. All ${rankedSchools.length} schools remain inside the no-call band.`
            : `${strictSchoolSignals.length} of ${rankedSchools.length} schools currently sit outside the strict no-call band.`}{" "}
          This is the claim the corpus supports today; raw result volume does
          not override it.
        </p>
      </section>

      <section className="mt-8 grid grid-cols-2 gap-px overflow-hidden rounded border border-rule bg-rule md:grid-cols-4">
        {[
          ["Featured", audit.summary.tier_counts.featured],
          ["Calibration", audit.summary.tier_counts.calibration],
          ["Archive", audit.summary.tier_counts.archive],
          ["Reference set", audit.summary.reference_set],
          ["Verified registration", audit.summary.registration_counts.verified],
          [
            "Legacy same-commit",
            audit.summary.registration_counts.legacy_same_commit,
          ],
          ["External reviews", counts?.completed_review_logs],
          ["Review submissions", counts?.review_submissions],
        ].map(([name, value]) => (
          <div key={String(name)} className="bg-white p-4">
            <div className="font-mono text-[25px] font-semibold">
              {fmt(Number(value))}
            </div>
            <div className="mt-1 text-[11px] font-semibold uppercase tracking-wider text-muted">
              {name}
            </div>
          </div>
        ))}
      </section>

      <section className="mt-12">
        <h2 className="m-0 text-[22px] font-semibold">The three tiers</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {(["featured", "calibration", "archive"] as const).map((tier) => (
            <div key={tier} className="rounded border border-rule bg-white p-5">
              <div className="text-[12px] font-semibold uppercase tracking-wider text-accent">
                {tier}
              </div>
              <div className="mt-2 font-mono text-[24px] font-semibold">
                {fmt(audit.summary.tier_counts[tier])}
              </div>
              <p className="mt-3 text-[13.5px] leading-[1.6] text-muted">
                {audit.definitions[tier]}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-12">
        <h2 className="m-0 text-[22px] font-semibold">
          Reference set (“gold set”)
        </h2>
        <p className="mt-3 max-w-[860px] text-[14px] leading-[1.65] text-muted">
          Six deliberately balanced examples make review tractable: supported
          and refuted results, multiple policy areas, and strict registration.
          This is a review queue, not a claim of peer review. Membership never
          overrides the record&apos;s mechanical tier.
        </p>
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {audit.reference_set.map((record) => {
            const hypothesis = hypothesisIndex.get(record.hypothesis_id);
            return (
              <Link
                key={record.hypothesis_id}
                href={`/h/${record.hypothesis_id}/`}
                className="rounded border border-rule bg-white p-4 hover:border-rule-strong hover:no-underline"
              >
                <div className="text-[11px] font-semibold uppercase tracking-wider text-accent">
                  {record.tier}
                </div>
                <h3 className="mt-1 text-[15px] font-semibold leading-snug text-ink">
                  {hypothesis?.claim.split(/(?<=[.!?])\s+/)[0] ??
                    record.hypothesis_id}
                </h3>
                <p className="mt-2 text-[12.5px] leading-[1.55] text-muted">
                  {record.note}
                </p>
              </Link>
            );
          })}
        </div>
      </section>

      <section className="mt-12 grid gap-8 md:grid-cols-2">
        <div>
          <h2 className="m-0 text-[20px] font-semibold">
            Estimator-floor findings
          </h2>
          <p className="mt-2 text-[13.5px] leading-[1.6] text-muted">
            A single record may trigger more than one finding. The public gate
            excludes the record once, while this table preserves every reason.
          </p>
          <table className="mt-4 w-full border-collapse text-[13px]">
            <tbody>
              {estimatorFailures.map(([reason, count]) => (
                <tr key={reason} className="border-b border-rule">
                  <td className="py-2 font-mono text-[12px]">{label(reason)}</td>
                  <td className="py-2 text-right font-mono">{fmt(count)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div>
          <h2 className="m-0 text-[20px] font-semibold">
            Public-credit exclusions
          </h2>
          <p className="mt-2 text-[13.5px] leading-[1.6] text-muted">
            Exclusion means no headline or scoreboard evidence credit. It does
            not delete the record or hide the diagnostic trail.
          </p>
          <table className="mt-4 w-full border-collapse text-[13px]">
            <tbody>
              {exclusions.map(([reason, count]) => (
                <tr key={reason} className="border-b border-rule">
                  <td className="py-2 font-mono text-[12px]">{label(reason)}</td>
                  <td className="py-2 text-right font-mono">{fmt(count)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-12 rounded border border-rule bg-panel p-6">
        <h2 className="m-0 text-[20px] font-semibold">
          External validation status
        </h2>
        <ul className="mt-4 list-disc space-y-2 pl-5 text-[14px] leading-[1.65] text-ink">
          <li>
            Completed external review logs:{" "}
            <strong>{fmt(counts?.completed_review_logs)}</strong>.
          </li>
          <li>
            Submitted external challenges:{" "}
            <strong>{fmt(counts?.review_submissions)}</strong>.
          </li>
          <li>No bounty programme is active and no payouts are claimed.</li>
          <li>
            No DOI or independent repository timestamp is claimed until an
            external archive deposit actually exists.
          </li>
          <li>
            Production is LLM-assisted under human direction; results are not
            peer-reviewed by default.
          </li>
        </ul>
        <p className="mt-4 text-[13.5px] text-muted">
          The next legitimacy threshold is independent hostile review of the
          reference set, followed by a versioned external archive deposit. The
          site will report those only after they are verifiable. The{" "}
          <a
            href={`${PUBLIC_GITHUB_REPO}/blob/main/review/REFERENCE_SET_REVIEW_PROTOCOL.md`}
            className="text-accent underline"
          >
            adversarial review protocol
          </a>{" "}
          publishes the frozen packet and acceptance standard without
          pretending a review has already happened.
        </p>
      </section>

      <section className="mt-12">
        <h2 className="m-0 text-[20px] font-semibold">Machine access</h2>
        <div className="mt-4 flex flex-wrap gap-3 text-[13px]">
          {[
            ["/methods-paper/", "Methods and limitations"],
            ["/evidence-tiers.json", "Evidence tier ledger"],
            ["/stats.json", "Corpus census"],
            ["/api/hypotheses.json", "Hypothesis index"],
            ["/api/scoreboard.json", "Scoreboard"],
            ["/llms.txt", "LLM guide"],
            ["/llms-full.txt", "Expanded LLM guide"],
          ].map(([href, name]) => (
            <a
              key={href}
              href={href}
              className="rounded border border-rule bg-white px-3 py-2 text-accent hover:no-underline"
            >
              {name} →
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}
