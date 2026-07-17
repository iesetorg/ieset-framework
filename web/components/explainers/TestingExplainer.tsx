import Link from "next/link";

/**
 * Plain-English explainer for the testing pipeline. Sits on the homepage
 * directly under the hero, where readers naturally ask "OK but HOW are
 * these scored?" after the hero promises explicit registration status.
 *
 * The visual steps mirror what actually happens in the codebase:
 *   - new prospective hypothesis YAML committed before its first run
 *   - fetcher pulls series from a primary publisher, freezes a vintage
 *   - estimator runs on the pinned vintage; the recorded threshold decides
 *
 * The publisher ribbon below the steps is a credibility signal — the names
 * are pulled from the actual list of fetchers in `data/fetchers/`. The
 * homepage deliberately avoids aggregate counts; those live in the dataset
 * pages where they cannot drift away from the corpus.
 */
export function TestingExplainer() {
  return (
    <div className="rounded-lg border border-rule bg-panel p-5">
      <div className="mb-2 flex items-center gap-2">
        <span className="rounded-full bg-accent-soft px-2.5 py-[3px] text-[10.5px] font-semibold uppercase tracking-wider text-accent">
          How a hypothesis becomes a verdict
        </span>
      </div>
      <p className="m-0 mb-3 max-w-[760px] text-[14.5px] leading-[1.55] text-ink">
        New prospective tests have to leave a paper trail: the pass/fail rule
        is committed before the first run, then the recorded rule runs against
        a pinned data vintage. Historical records that entered git alongside
        their result remain visible but are labelled unverified.
      </p>

      <div className="grid grid-cols-1 gap-2.5 text-[13px] sm:grid-cols-3">
        <Step
          title="Write the rule first"
          body={
            <>
              The hypothesis YAML names the metrics, the threshold, and the
              estimator. For a verified prospective test, it&apos;s committed
              to git <strong>before</strong> the first run artifact. Git
              topology verifies that ordering; it is not an independent
              timestamping service.
            </>
          }
        />
        <Step
          title="Pull from primary publishers"
          body={
            <>
              Series are fetched from the original sources — World Bank, IMF,
              OECD, BIS, FRED, Eurostat — frozen as a versioned vintage with
              a content hash. Old vintages are never overwritten, so every run
              stays reproducible from the bytes it actually saw.
            </>
          }
        />
        <Step
          title="Run the locked rule"
          body={
            <>
              The estimator runs against the pinned vintage. The
              recorded threshold mechanically decides{" "}
              <span className="text-green font-semibold">supported</span>,{" "}
              <span className="text-amber font-semibold">partial</span>, or{" "}
              <span className="text-red font-semibold">refuted</span>. Every
              result ships with the steelman — the strongest argument
              against what we found.
            </>
          }
        />
      </div>

      {/* Publisher ribbon — credibility signal that the data is real */}
      <div className="mt-4 rounded border border-rule bg-white p-3">
        <div className="mb-2 text-[10.5px] font-semibold uppercase tracking-wider text-muted">
          Data comes from public publishers
        </div>
        <div className="flex flex-wrap gap-1 text-[11.5px]">
          {PUBLISHERS.map((p) => (
            <span
              key={p.short}
              className="rounded bg-panel px-1.5 py-[1px] font-mono text-muted"
              title={p.full}
            >
              {p.short}
            </span>
          ))}
          <span className="px-1.5 py-[1px] text-faint">
            … and more in the source registry
          </span>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-3 text-[12.5px]">
        <Link href="/methodology" className="text-accent hover:underline">
          Read the full methodology →
        </Link>
        <Link
          href="/h"
          className="text-muted hover:text-ink hover:underline"
        >
          Browse all hypotheses
        </Link>
      </div>
    </div>
  );
}

function Step({
  title,
  body,
}: {
  title: string;
  body: React.ReactNode;
}) {
  return (
    <div className="rounded border border-rule bg-white p-3">
      <div className="mb-1 flex items-center gap-1.5">
        <span className="inline-flex h-[9px] w-[9px] rounded-full bg-accent">
          <span className="sr-only">step</span>
        </span>
        <span className="text-[12px] font-semibold uppercase tracking-wider text-muted">
          {title}
        </span>
      </div>
      <div className="text-[13px] leading-[1.5] text-ink">{body}</div>
    </div>
  );
}

// Recognizable publishers used by the framework. `short` is what shows in the
// ribbon; `full` is the title-attribute hover, useful when the abbreviation is
// opaque.
const PUBLISHERS: { short: string; full: string }[] = [
  { short: "World Bank", full: "World Bank — WDI + WGI" },
  { short: "IMF", full: "International Monetary Fund — WEO" },
  { short: "OECD", full: "OECD" },
  { short: "BIS", full: "Bank for International Settlements" },
  { short: "FRED", full: "FRED — Federal Reserve Bank of St. Louis" },
  { short: "Eurostat", full: "Eurostat" },
  { short: "BLS", full: "U.S. Bureau of Labor Statistics" },
  { short: "ECB", full: "European Central Bank" },
  { short: "BoE", full: "Bank of England" },
  { short: "Maddison", full: "Maddison Project Database 2020" },
  { short: "Shiller", full: "Robert Shiller — long-run U.S. data" },
  { short: "V-Dem", full: "Varieties of Democracy" },
  { short: "Polity5", full: "Polity5 (Center for Systemic Peace)" },
  { short: "Fraser EFW", full: "Fraser Institute — Economic Freedom of the World" },
  { short: "Heritage", full: "Heritage Foundation — Index of Economic Freedom" },
  { short: "ILO", full: "International Labour Organization — ILOSTAT" },
  { short: "WHO", full: "World Health Organization — GHO" },
  { short: "UN DESA", full: "UN Department of Economic and Social Affairs" },
  { short: "FAO", full: "Food and Agriculture Organization — FAOSTAT" },
  { short: "IEA", full: "International Energy Agency" },
  { short: "WIPO", full: "World Intellectual Property Organization" },
  { short: "UN Comtrade", full: "UN Comtrade — international trade" },
  { short: "SIPRI", full: "Stockholm International Peace Research Institute" },
  { short: "Freedom House", full: "Freedom House" },
];
