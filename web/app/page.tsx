import Link from "next/link";

import {
  loadAllHypotheses,
  loadRunArtifacts,
  isHypothesisPubliclyVisible,
} from "@/lib/content";
import { verdictTone } from "@/lib/verdict";
import { Badge } from "@/components/badges/Badge";
import { VerdictLegend } from "@/components/badges/VerdictLegend";
import { AxesExplainer } from "@/components/explainers/AxesExplainer";
import { TestingExplainer } from "@/components/explainers/TestingExplainer";

export default async function HomePage() {
  const all = await loadAllHypotheses();
  const runs = await Promise.all(
    all.map(async (h) => ({ h, run: await loadRunArtifacts(h.hypothesis_id) }))
  );

  // Featured = hypotheses that pass the publicly-visible gate (real
  // replication, real verdict, sharpened falsification rule). The other
  // runs stay in the repo as drafts but don't surface here — see
  // isHypothesisPubliclyVisible() for the full criteria.
  const withResults = runs.filter((r) => isHypothesisPubliclyVisible(r.h, r.run));
  const preRegOnly = runs.filter((r) => !isHypothesisPubliclyVisible(r.h, r.run));

  // Curated featured-six. Picked deliberately to (a) feature recent runs from
  // the wave-4-through-integrity-sweep era, (b) headline a clean Austrian-school
  // win (UK Truss FX repricing) and a clean Marxist/Bolivarian-narrative loss
  // (Venezuela GDP collapse), (c) show the framework grades both directions —
  // including a heterodox-Minsky win and a degrowth-narrative loss — so it
  // doesn't read as one-sided, and (d) showcase the canonical-basket integrity
  // gate via the Costa Rica refutation.
  const FEATURED_IDS: readonly string[] = [
    "unfunded_fiscal_expansion_above_zlb_bond_market_response", // Austrian win — UK Truss
    "venezuela_chavismo_framework_validation",                  // Marxist/Bolivarian loss — VEN -79% gap
    "volcker_disinflation_output_recovery",                     // Monetarist credibility win
    "costa_rica_wellbeing_throughput_efficiency",               // Canonical-basket gate — degrowth refuted
    "washington_consensus_vs_developmental_state_performance",  // Developmentalist win — KOR vs ARG +69pp
    "gfc_endogenous_minsky_leverage_mechanism",                 // Heterodox-Minsky win — 3 of 4 indicators
  ];
  const byId = new Map(withResults.map((r) => [r.h.hypothesis_id, r] as const));
  const featured = FEATURED_IDS
    .map((id) => byId.get(id))
    .filter((r): r is (typeof withResults)[number] => r !== undefined);

  return (
    <div className="mx-auto max-w-content px-8">
      {/* Hero */}
      <section className="border-b border-rule py-14">
        <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-accent-soft px-3 py-1 text-[11px] font-medium uppercase tracking-wider text-accent">
          <span className="inline-block h-[6px] w-[6px] rounded-full bg-accent" />
          pre-registration-first economic framework
        </div>
        <h1 className="m-0 mb-4 max-w-[940px] text-[42px] font-semibold leading-[1.1] tracking-[-0.02em] md:text-[52px]">
          Economic politics should be settled by testable claims.
        </h1>
        <p className="mb-6 max-w-[720px] text-[18px] leading-[1.55] text-muted">
          IESET is a public evidence map for economic policy. Instead of
          asking which tribe sounds most confident, it asks every school to
          make claims that can lose: what should happen, where, over what
          period, and what data would change our mind. Those claims are
          registered before analysis and scored against reproducible runs.
        </p>
        <p className="mb-6 max-w-[720px] text-[15px] leading-[1.6] text-muted">
          Start with a claim, a school of thought, a policy, or a country. The
          library links each one through shared policy levers so a slogan can
          be traced down to its test, data vintage, code, steelman, and
          scoreboard impact.
        </p>
        <p className="mb-6 max-w-[720px] text-[15px] leading-[1.6] text-muted">
          One pattern already visible in the scoreboard: market institutions
          tend to turn conflict into positive-sum coordination, while many
          Marxian or heavily interventionist claims look, at best, like
          redistribution without durable surplus creation. The point is not to
          settle the argument by label; it is to ask whether the surplus grows,
          merely moves, or shrinks.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link
            href="/h"
            className="inline-block rounded border border-accent bg-accent px-5 py-2.5 text-sm font-medium text-white hover:bg-[#183e61] hover:no-underline"
          >
            Search hypotheses →
          </Link>
          <Link
            href="/scoreboard"
            className="inline-block rounded border border-rule-strong bg-white px-5 py-2.5 text-sm font-medium text-ink hover:bg-panel hover:no-underline"
          >
            Open the scoreboard
          </Link>
          <Link
            href="/how-it-works"
            className="inline-block rounded border border-rule-strong bg-white px-5 py-2.5 text-sm font-medium text-ink hover:bg-panel hover:no-underline"
          >
            How it works
          </Link>
        </div>
      </section>

      {/* Testing explainer — answers the immediate question raised by the
          hero ("how do you actually score these?") before introducing
          the axes vocabulary. */}
      <section className="border-b border-rule py-10">
        <TestingExplainer />
      </section>

      {/* Axes explainer — the framework's spine */}
      <section className="border-b border-rule py-10">
        <AxesExplainer variant="compact" />
      </section>

      {/* Results so far — curated cards only; exact counts live on /h and /scoreboard. */}
      {withResults.length > 0 && (
        <section className="border-b border-rule py-12">
          <div className="mb-5 flex items-baseline justify-between">
            <h2 className="m-0 text-xs font-semibold uppercase tracking-wider text-muted">
              Recent results
            </h2>
            <Link href="/h" className="text-sm text-muted hover:text-ink">
              Open the hypothesis library →
            </Link>
          </div>
          <div className="mb-4">
            <VerdictLegend />
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {featured.map(({ h, run }) => {
              const tone = verdictTone(run.verdict);
              const first = h.claim.split(/(?<=[.!?])\s+/)[0];
              const toneBar = tone === "green" ? "bg-green"
                : tone === "amber" ? "bg-amber"
                : tone === "red" ? "bg-red"
                : "bg-faint";
              return (
                <Link
                  key={h.hypothesis_id}
                  href={`/h/${h.hypothesis_id}`}
                  className="group block overflow-hidden rounded border border-rule bg-white hover:border-rule-strong hover:no-underline"
                >
                  <div className={`${toneBar}`} style={{ height: 3 }} />
                  <div className="p-5">
                    <div className="mb-3 flex flex-wrap items-center gap-2">
                      {tone === "green" && <Badge variant="green" dot>supported</Badge>}
                      {tone === "amber" && <Badge variant="amber" dot>partial</Badge>}
                      {tone === "red" && <Badge variant="red" dot>refuted / weakened</Badge>}
                      <Badge variant="muted">{h.topic.replace(/_/g, " ")}</Badge>
                    </div>
                    <h3 className="mb-2 text-[16px] font-semibold leading-snug text-ink group-hover:text-accent">
                      {first}
                    </h3>
                    <p className="m-0 text-[13.5px] leading-[1.5] text-muted">
                      Open the result card for the exact estimator, threshold,
                      data vintage, and diagnostic verdict.
                    </p>
                    <div className="mt-3 font-mono text-[10.5px] text-faint">
                      {h.hypothesis_id}
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </section>
      )}

      {/* Pre-registered, awaiting data/run — sample cards only; counts live in /h. */}
      {preRegOnly.length > 0 && (
        <section className="border-b border-rule py-12">
          <div className="mb-5 flex items-baseline justify-between">
            <div>
              <h2 className="m-0 text-xs font-semibold uppercase tracking-wider text-muted">
                Pre-registered — awaiting data or run
              </h2>
              <p className="mt-2 text-[14px] text-muted">
                Specs are committed to git with their falsification criteria.
                The locked library is the source of truth; runs fire when the
                data substrate is ready.
              </p>
            </div>
            <Link href="/h" className="text-sm text-muted hover:text-ink">
              Browse locked specs →
            </Link>
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            {preRegOnly.slice(0, 6).map(({ h }) => (
              <Link
                key={h.hypothesis_id}
                href={`/h/${h.hypothesis_id}`}
                className="block rounded border border-rule bg-white p-4 hover:border-rule-strong hover:no-underline"
              >
                <div className="mb-2 flex items-center gap-2">
                  <Badge variant="muted">{h.topic.replace(/_/g, " ")}</Badge>
                </div>
                <h3 className="m-0 text-[14px] font-medium leading-snug text-ink">
                  {h.claim.split(/(?<=[.!?])\s+/)[0]}
                </h3>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Methodology commitments */}
      <section className="py-12">
        <h2 className="mb-6 text-xs font-semibold uppercase tracking-wider text-muted">
          Methodology commitments
        </h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {INVARIANTS.map((inv, i) => (
            <div key={i} className="rounded border border-rule bg-white p-5">
              <div className="mb-1.5 font-mono text-[11px] text-accent">
                {String(i + 1).padStart(2, "0")}
              </div>
              <h3 className="mb-1.5 text-[15px] font-semibold leading-snug">
                {inv.title}
              </h3>
              <p className="m-0 text-[13.5px] leading-[1.55] text-muted">
                {inv.body}
              </p>
            </div>
          ))}
        </div>
        <div className="mt-6">
          <Link href="/methodology" className="text-sm">
            Read the full methodology →
          </Link>
        </div>
      </section>
    </div>
  );
}

const INVARIANTS = [
  {
    title: "Pre-registration precedes estimation",
    body:
      "Every hypothesis is committed to git before any data is examined. The git history is the proof-of-work: commit timestamps show the spec existed before the run.",
  },
  {
    title: "Provenance to publisher",
    body:
      "Every cell in every table resolves to a publisher API call with fetch UTC, license, and SHA256. Vintages never overwrite.",
  },
  {
    title: "Policy content, not coalition",
    body:
      "Reforms are scored by what they did on each axis, not by party label. Schröder's market-oriented labour reform is coded as market-oriented regardless of SPD.",
  },
  {
    title: "Surplus before sentiment",
    body:
      "Redistribution can be a real policy objective, but the scoreboard asks whether a claim creates durable gains or mostly reallocates a fixed pie.",
  },
  {
    title: "Channel-separated measurement",
    body:
      "Fiscal and regulatory interventions are measured on independent axes. They correlate politically but are causally distinct.",
  },
  {
    title: "Trajectory over snapshot",
    body:
      "Within-country change over time is the default analytical lens. Point-in-time cross-country comparison requires justification.",
  },
  {
    title: "Authored, reproducible, correctable",
    body:
      "IESET is authored, but the claims are pre-registered, reproducible, and open to specific correction.",
  },
];
