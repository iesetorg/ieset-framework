import Link from "next/link";

import { scoreAllPositions } from "@/lib/content";
import { VerdictLegend } from "@/components/badges/VerdictLegend";

export const metadata = {
  title: "Scoreboard — evidence coverage by school of thought",
  description:
    "Every position makes specific predictions linked to specific hypotheses. This page separates forecast accuracy from attribution-aware evidence about school-level mechanisms.",
  alternates: { canonical: "https://framework.ieset.org/scoreboard/" },
};

function formatPct(n: number): string {
  return `${Math.round(n * 100)}%`;
}

const COVERAGE_LINKED_FLOOR = 100;
const COVERAGE_TESTED_FLOOR = 60;

export default async function ScoreboardPage() {
  const scores = await scoreAllPositions();
  const rankedSchools = scores.filter((s) => s.scoreboard_role === "school");
  const benchmarkControls = scores.filter(
    (s) => s.scoreboard_role === "benchmark_control"
  );
  const tested = rankedSchools
    .filter((s) => s.tested > 0)
    .sort((a, b) => {
      const adjustedNetDiff = b.adjusted_net_score - a.adjusted_net_score;
      if (Math.abs(adjustedNetDiff) > 0.001) return adjustedNetDiff;
      const adjustedWeightDiff =
        b.adjusted_tested_weight - a.adjusted_tested_weight;
      if (Math.abs(adjustedWeightDiff) > 0.001) return adjustedWeightDiff;
      const rawNetDiff = b.net_score - a.net_score;
      if (Math.abs(rawNetDiff) > 0.001) return rawNetDiff;
      return a.position_id.localeCompare(b.position_id);
    });
  const untestedOnly = rankedSchools.filter((s) => s.tested === 0);
  const totalRun = rankedSchools.reduce((a, s) => a + s.tested, 0);
  const totalClaims = rankedSchools.reduce((a, s) => a + s.total_claims, 0);
  const coverageRows = rankedSchools
    .map((s) => {
      const linked = new Set(
        s.scored_claims
          .filter((c) => c.hypothesis_exists && c.linked_hypothesis_id)
          .map((c) => c.linked_hypothesis_id)
      );
      const testedLinked = new Set(
        s.scored_claims
          .filter(
            (c) =>
              c.hypothesis_exists &&
              c.linked_hypothesis_id &&
              c.verdict
          )
          .map((c) => c.linked_hypothesis_id)
      );
      const linkedCount = linked.size;
      const testedCount = testedLinked.size;
      return {
        position_id: s.position_id,
        school: s.school,
        linkedCount,
        testedCount,
        pendingCount: Math.max(0, linkedCount - testedCount),
        linkedGap: Math.max(0, COVERAGE_LINKED_FLOOR - linkedCount),
        testedGap: Math.max(0, COVERAGE_TESTED_FLOOR - testedCount),
      };
    })
    .sort((a, b) => {
      const gapDiff = b.linkedGap + b.testedGap - (a.linkedGap + a.testedGap);
      if (gapDiff !== 0) return gapDiff;
      return a.testedCount - b.testedCount;
    });
  const balancedCoverage = coverageRows.filter(
    (r) => r.linkedGap === 0 && r.testedGap === 0
  ).length;

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <h1 className="m-0 text-[34px] font-semibold tracking-[-0.02em]">
        Scoreboard — schools of thought vs the data
      </h1>
      <p className="mt-4 max-w-[780px] text-[17px] leading-[1.55] text-muted">
        Every school of thought (position) lists specific predictions it makes,
        each linked to a hypothesis in the library. When a hypothesis runs, its
        verdict feeds back into the schools that predicted an outcome on it,
        while discounting broad failure calls that do not identify why a policy
        failed. This page is a diagnostic of the current authored corpus, not an
        independent ranking of economic truth.
      </p>

      <div className="my-6 flex flex-wrap gap-6 text-[14px]">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">Schools tracked</div>
          <div className="text-[22px] font-semibold">{rankedSchools.length}</div>
        </div>
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">Total predictions</div>
          <div className="text-[22px] font-semibold">{totalClaims}</div>
        </div>
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">Predictions with a test run</div>
          <div className="text-[22px] font-semibold">{totalRun}</div>
        </div>
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">V1 coverage balanced</div>
          <div className="text-[22px] font-semibold">{balancedCoverage}/{rankedSchools.length}</div>
        </div>
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">Benchmark controls</div>
          <div className="text-[22px] font-semibold">{benchmarkControls.length}</div>
        </div>
      </div>

      <div className="mb-4">
        <VerdictLegend />
      </div>
      <div className="mb-6 border-l-[3px] border-accent bg-panel px-4 py-3 text-[13.5px] leading-[1.55] text-ink">
        <div className="sc mb-1 text-[10px] font-semibold tracking-[0.1em] text-accent">
          how to read this
        </div>
        <p className="m-0">
          <strong>Support rate</strong> = of a school&apos;s predictions that
          have actually been tested, the fraction where the data agreed with
          the school. A school with 1-of-1 tested prediction supported is not
          more vindicated than one with 3-of-5 — the <strong>Tested</strong>{" "}
          column matters as much as <strong>Rate</strong>. This scoreboard{" "}
          <em>is</em> the framework updating on evidence in public.
        </p>
        <p className="mt-3 mb-0">
          The strict integrity layer is deliberately conservative. It currently
          separates no school from the no-call band, so this table is presented
          as a forecast-quality view rather than a high-integrity ranking. The
          stricter gate remains active and published; its tier rules, exclusions,
          and current audit counts are on the{" "}
          <Link href="/evidence/" className="font-medium text-accent hover:underline">
            evidence quality page
          </Link>
          .
        </p>
        <p className="mt-3 mb-0">
          <strong>Raw net</strong> is the simple forecast scoreboard: a clear win counts
          +1, a partial win +0.5, a partial loss -0.5, and a clear loss -1.{" "}
          <strong>Forecast Q-net</strong> starts from that same score, then asks how
          strong the test design is. A study that can credibly test a causal
          claim should move the scoreboard more than a broad pattern match like
          &quot;this country got richer and healthier.&quot;
        </p>
        <p className="mt-3 mb-0">
          The <strong>strict integrity gate</strong> goes further than Q-net. It
          also checks claim-link confidence, first-pass screening cautions, and
          whether a school actually identified the causal mechanism behind a
          failed policy. Policy-experiment evidence cannot establish a
          high-integrity school ranking until required mechanism, incidence,
          supply, quality, leakage, fiscal, and welfare layers are measured or
          explicitly cleared.
        </p>
        <div className="mt-3 grid gap-px overflow-hidden border border-rule bg-rule text-[12.5px] md:grid-cols-4">
          <div className="bg-white px-3 py-2">
            <strong>Causal tests: 1×</strong>
            <div className="mt-0.5 text-muted">
              Strongest base weight, but still gated if second-order mechanism
              layers are missing.
            </div>
          </div>
          <div className="bg-white px-3 py-2">
            <strong>Associational tests: 0.5×</strong>
            <div className="mt-0.5 text-muted">
              Useful evidence, but weaker because correlation may not be the
              mechanism.
            </div>
          </div>
          <div className="bg-white px-3 py-2">
            <strong>Descriptive patterns: 0.25×</strong>
            <div className="mt-0.5 text-muted">
              Real evidence, but mostly says the outcome happened, not why it
              happened.
            </div>
          </div>
          <div className="bg-white px-3 py-2">
            <strong>Failure attribution: capped</strong>
            <div className="mt-0.5 text-muted">
              Negative forecasts get full losses when wrong, but wins are held
              or capped unless the test identifies the failure mechanism.
            </div>
          </div>
        </div>
        <p className="mt-3 mb-0">
          Rows are ordered by <strong>Forecast Q-net</strong>, then forecast
          tested weight, raw net, and school ID. Q-net and the original raw score
          stay visible for transparency, while tiny margins are muted as too
          close to call. This ordering is not a high-integrity winner call.
          Benchmark controls are reported separately and never compete in the
          school table.
        </p>
      </div>

      <h2 className="mt-10 mb-3 text-xs font-semibold uppercase tracking-wider text-muted">
        Schools with tested predictions — Forecast Q-net view
      </h2>
      <div className="overflow-x-auto rounded border border-rule bg-white">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-rule bg-panel">
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">School</th>
              <th className="p-3 text-right text-[10px] font-semibold uppercase tracking-wider text-muted" title="Forecast quality net: raw outcome score discounted by evidence type">Forecast Q-net</th>
              <th className="p-3 text-right text-[10px] font-semibold uppercase tracking-wider text-muted" title="Raw weighted net: full wins + 0.5·partial-wins − 0.5·partial-losses − full losses">Raw net</th>
              <th className="p-3 text-right text-[10px] font-semibold uppercase tracking-wider text-muted" title="Weighted support rate: partial directional verdicts count at half-weight">Rate</th>
              <th className="p-3 text-right text-[10px] font-semibold uppercase tracking-wider text-muted">Supports</th>
              <th className="p-3 text-right text-[10px] font-semibold uppercase tracking-wider text-muted" title="Direction-correct partial verdicts — weak evidence in school's favour">Partial +</th>
              <th className="p-3 text-right text-[10px] font-semibold uppercase tracking-wider text-muted" title="Direction-wrong partial verdicts — weak evidence against school">Partial −</th>
              <th className="p-3 text-right text-[10px] font-semibold uppercase tracking-wider text-muted">Refutes</th>
              <th className="p-3 text-right text-[10px] font-semibold uppercase tracking-wider text-muted" title="Test-quality failures (pre-trend issues, identification problems) — neither school wins nor loses">Neutral</th>
              <th className="p-3 text-right text-[10px] font-semibold uppercase tracking-wider text-muted">Untested</th>
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">Progress</th>
            </tr>
          </thead>
          <tbody>
            {tested.map((s) => {
              return (
                <tr
                  key={s.position_id}
                  className="border-b border-rule last:border-0 hover:bg-panel"
                >
                  <td className="p-3 align-top">
                    <Link
                      href={`/pos/${s.position_id}`}
                      className="font-medium text-ink hover:underline"
                    >
                      {s.school}
                    </Link>
                    <div className="mt-0.5 font-mono text-[10.5px] text-faint">
                      {s.position_id}
                    </div>
                  </td>
                  <td
                    className="p-3 text-right align-top font-mono text-[13px]"
                    title={`Forecast Q-net no-call band: ±${s.adjusted_signal_threshold.toFixed(1)} points.`}
                    style={{ color: scoreTone(s.adjusted_score_signal) }}
                  >
                    {s.adjusted_net_score > 0 ? "+" : ""}{s.adjusted_net_score.toFixed(1)}
                  </td>
                  <td
                    className="p-3 text-right align-top font-mono text-[13px]"
                    title={`Raw no-call band: ±${s.signal_threshold.toFixed(1)} net points.`}
                    style={{ color: scoreTone(s.score_signal) }}
                  >
                    {s.net_score > 0 ? "+" : ""}{s.net_score.toFixed(1)}
                  </td>
                  <td className="p-3 text-right align-top">
                    <span
                      className="inline-block rounded px-2 py-[3px] text-xs font-semibold"
                      style={{
                        background: rateTone(s.support_rate).bg,
                        color: rateTone(s.support_rate).fg,
                      }}
                    >
                      {formatPct(s.support_rate)}
                    </span>
                  </td>
                  <td className="p-3 text-right align-top text-green font-semibold">{s.supports}</td>
                  <td className="p-3 text-right align-top" style={{ color: "#5fa673" }}>{s.partial_supports}</td>
                  <td className="p-3 text-right align-top" style={{ color: "#c4756d" }}>{s.partial_refutes}</td>
                  <td className="p-3 text-right align-top text-red font-semibold">{s.refutes}</td>
                  <td className="p-3 text-right align-top text-amber">{s.partial}</td>
                  <td className="p-3 text-right align-top text-muted">{s.untested}</td>
                  <td className="p-3 align-top" style={{ minWidth: 180 }}>
                    <StackedBar s={s} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {untestedOnly.length > 0 && (
        <>
          <h2 className="mt-12 mb-3 text-xs font-semibold uppercase tracking-wider text-muted">
            Schools with no tested predictions yet
          </h2>
          <div className="rounded border border-rule bg-white">
            <ul className="divide-y divide-rule">
              {untestedOnly.map((s) => (
                <li key={s.position_id} className="flex items-center justify-between p-3">
                  <Link href={`/pos/${s.position_id}`} className="font-medium text-ink hover:underline">
                    {s.school}
                  </Link>
                  <span className="text-[13px] text-muted">
                    {s.total_claims} prediction{s.total_claims === 1 ? "" : "s"} pending test
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}

      {benchmarkControls.length > 0 && (
        <>
          <h2 className="mt-12 mb-3 text-xs font-semibold uppercase tracking-wider text-muted">
            Benchmark controls — reported, never ranked
          </h2>
          <div className="grid gap-3 md:grid-cols-2">
            {benchmarkControls.map((s) => (
              <div key={s.position_id} className="rounded border border-rule bg-white p-4">
                <Link
                  href={`/pos/${s.position_id}`}
                  className="font-medium text-ink hover:underline"
                >
                  {s.school}
                </Link>
                <div className="mt-1 text-[12.5px] leading-relaxed text-muted">
                  Calibration row only · Q-net {s.adjusted_net_score > 0 ? "+" : ""}
                  {s.adjusted_net_score.toFixed(1)}
                  {" · "}raw {s.net_score > 0 ? "+" : ""}
                  {s.net_score.toFixed(1)}
                  {" · "}{s.tested} tested of {s.total_claims}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <section className="mt-14 rounded border border-rule bg-panel p-6">
        <h3 className="m-0 text-[16px] font-semibold">Notes on interpretation</h3>
        <ul className="mt-3 list-disc pl-5 text-[14px] leading-[1.6] text-muted">
          <li>
            A school can look supported because its predictions happen to align
            with well-documented patterns the framework hasn&apos;t seriously
            challenged yet. Small-n wins don&apos;t imply the school is right;
            they imply the framework has tested few things.
          </li>
          <li>
            A failed policy can count as a correct forecast without proving
            the opponent&apos;s causal story. The strict integrity gate holds
            those wins unless the underlying hypothesis is causal or mechanism
            discriminating.
          </li>
          <li>
            A school can look refuted because a specific prediction failed on a
            specific sample. Aggregate refutation of a school requires many
            predictions failing. One v1 hypothesis refutation is not a full
            verdict on the school.
          </li>
          <li>
            Predictions marked &quot;untested&quot; are either hypotheses we haven&apos;t
            run yet, or hypotheses we haven&apos;t written yet. Both are tracked
            as open work.
          </li>
          <li>
            Distributional wins are not treated as fake wins. They are treated
            as incomplete until the associated surplus question is visible: did
            the intervention create durable gains, trade off against other
            groups, or shrink the base it redistributed from?
          </li>
          <li>
            The score updates automatically when hypothesis runs land. This page
            is a live read of the git state.
          </li>
          <li>
            House or calibration positions are benchmark controls. They remain
            visible for auditability but are excluded from school counts,
            ranking, and aggregate ranked-school totals.
          </li>
        </ul>
      </section>
    </div>
  );
}

function rateTone(r: number): { bg: string; fg: string } {
  if (r >= 0.66) return { bg: "#dff1e4", fg: "#2c7a4f" };
  if (r >= 0.33) return { bg: "#fdf1da", fg: "#b7791f" };
  return { bg: "#f3d9d9", fg: "#9e2f2f" };
}

function scoreTone(signal: string): string {
  if (signal === "positive_signal") {
    return "#2c7a4f";
  }
  if (signal === "negative_signal") {
    return "#9e2f2f";
  }
  if (signal === "untested") {
    return "#57554e";
  }
  return "#57554e";
}

function StackedBar({
  s,
}: {
  s: {
    total_claims: number;
    supports: number;
    refutes: number;
    partial_supports: number;
    partial_refutes: number;
    partial: number;
    untested: number;
  };
}) {
  const total = s.total_claims;
  if (total === 0) return <span className="text-xs text-muted">—</span>;
  const seg = (n: number) => `${(n / total) * 100}%`;
  return (
    <div className="flex h-[10px] w-full overflow-hidden rounded-full bg-panel">
      <div className="h-full bg-green" style={{ width: seg(s.supports) }} title={`supports: ${s.supports}`} />
      <div className="h-full" style={{ width: seg(s.partial_supports), background: "#a8d4b5" }} title={`partial+: ${s.partial_supports}`} />
      <div className="h-full bg-amber" style={{ width: seg(s.partial) }} title={`neutral partial: ${s.partial}`} />
      <div className="h-full" style={{ width: seg(s.partial_refutes), background: "#e3b5b0" }} title={`partial−: ${s.partial_refutes}`} />
      <div className="h-full bg-red" style={{ width: seg(s.refutes) }} title={`refutes: ${s.refutes}`} />
      <div className="h-full" style={{ width: seg(s.untested), background: "#e8e6e0" }} title={`untested: ${s.untested}`} />
    </div>
  );
}
