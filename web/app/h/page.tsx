import Link from "next/link";

import {
  loadAllHypotheses,
  loadAxes,
  loadHypothesisSchoolPredictions,
  loadRunArtifacts,
} from "@/lib/content";
import { loadHypothesisAxisIndex } from "@/lib/matching";
import { verdictTone, verdictShort } from "@/lib/verdict";
import { AxisChip } from "@/components/badges/AxisChip";
import { Badge } from "@/components/badges/Badge";

export const metadata = {
  title: "Hypotheses",
  description:
    "Every hypothesis in the IESET framework, pre-registered in git before the data is examined.",
};

/**
 * Sort key for the hypothesis table. Lower = earlier on the page.
 * Tier 1 (with verdict): supported (green) → partial (amber) → refuted (red)
 *   → other muted. Tier 2 (no verdict): pre-registered, pending estimator.
 * Within each tier, the underlying stable sort preserves YAML load order.
 */
function sortRank(verdict: string | undefined): number {
  if (!verdict) return 99;
  const tone = verdictTone(verdict);
  if (tone === "green") return 0;
  if (tone === "amber") return 1;
  if (tone === "red") return 2;
  return 3;
}

function alignmentTone(
  alignment: "aligned" | "partial" | "opposed" | "untested"
) {
  if (alignment === "aligned")
    return { bg: "#dff1e4", fg: "#2c7a4f", ring: "#bcdcc4", glyph: "✓" };
  if (alignment === "partial")
    return { bg: "#fdf1da", fg: "#b7791f", ring: "#ecd6a6", glyph: "~" };
  if (alignment === "opposed")
    return { bg: "#f3d9d9", fg: "#9e2f2f", ring: "#e3b6b6", glyph: "✗" };
  return { bg: "#f3f3f1", fg: "#636363", ring: "#dcdad4", glyph: "·" };
}

/**
 * Compare a school's expected verdict to the actual verdict to compute whether
 * the run "vindicated" or "rebuked" the school.
 */
function schoolOutcome(
  expected: "supported" | "falsified" | "mixed",
  actual: string | undefined
): "aligned" | "partial" | "opposed" | "untested" {
  if (!actual) return "untested";
  const v = actual.toLowerCase();
  const hypSupp = v.startsWith("supported");
  const hypRef =
    v.startsWith("refuted") ||
    v.startsWith("weakened") ||
    v.startsWith("not supported") ||
    v.startsWith("not_supported");
  const hypPart =
    v.startsWith("partial") ||
    v.startsWith("partially") ||
    v.startsWith("mixed") ||
    v.startsWith("weakly");
  if (expected === "supported" && hypSupp) return "aligned";
  if (expected === "supported" && hypRef) return "opposed";
  if (expected === "falsified" && hypRef) return "aligned";
  if (expected === "falsified" && hypSupp) return "opposed";
  if (hypPart || expected === "mixed") return "partial";
  return "untested";
}

export default async function HypothesesIndex() {
  const [all, axesMap, axisIndex, schoolsIndex] = await Promise.all([
    loadAllHypotheses(),
    loadAxes(),
    loadHypothesisAxisIndex(),
    loadHypothesisSchoolPredictions(),
  ]);
  const withRuns = await Promise.all(
    all.map(async (h) => ({
      h,
      run: await loadRunArtifacts(h.hypothesis_id),
    }))
  );

  // Hypothesis count summary — distinguish actual verdicts from runs in flight.
  // A run directory exists for any hypothesis whose pipeline has been kicked
  // off, but only the ones with a `verdict` field in diagnostics.json have a
  // real result to show. The rest are still pre-registered awaiting data or
  // a complete estimator pass.
  const verdictCount = withRuns.filter((r) => r.run.verdict).length;

  // Sort: hypotheses with a verdict first (by tone — supported ranks above
  // partial above refuted), pre-registered/pending last. Stable sort preserves
  // YAML load order inside each tier so deploys don't reshuffle the table.
  const sortedRuns = withRuns.slice().sort((a, b) => {
    return sortRank(a.run.verdict) - sortRank(b.run.verdict);
  });

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <h1 className="mb-3 text-[32px] font-semibold tracking-[-0.02em]">
        Hypotheses
      </h1>
      <p className="mb-2 max-w-[780px] text-[17px] text-muted">
        Every entry is pre-registered in git before any data is examined.
        Falsification criteria are committed alongside the spec. {verdictCount}{" "}
        of {all.length} have a verdict; the rest are pre-registered awaiting
        data or estimation.
      </p>

      {/* COMBINED LEGEND */}
      <div className="mb-6 grid gap-2 text-[11px] text-muted md:grid-cols-3">
        <div className="flex flex-wrap items-center gap-3">
          <span className="sc text-[10px]">verdict</span>
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-block h-2 w-2 rounded-full bg-green" />{" "}
            supported
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-block h-2 w-2 rounded-full bg-amber" />{" "}
            partial
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-block h-2 w-2 rounded-full bg-red" />{" "}
            refuted
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-block h-2 w-2 rounded-full bg-faint" />{" "}
            pending
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <span className="sc text-[10px]">axis channel</span>
          <span className="inline-flex items-center gap-1.5">
            <span
              className="inline-block h-[10px] w-[10px] rounded-sm"
              style={{ background: "#eef3fb", border: "1px solid #cad8eb" }}
            />
            fiscal
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span
              className="inline-block h-[10px] w-[10px] rounded-sm"
              style={{ background: "#f3eef6", border: "1px solid #dccae6" }}
            />
            regulatory
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span
              className="inline-block h-[10px] w-[10px] rounded-sm"
              style={{ background: "#fdf2e9", border: "1px solid #ecd2b5" }}
            />
            monetary
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span
              className="inline-block h-[10px] w-[10px] rounded-sm"
              style={{ background: "#eef6ef", border: "1px solid #c8dccc" }}
            />
            institutional
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <span className="sc text-[10px]">school outcome</span>
          <span className="inline-flex items-center gap-1.5">
            <span
              className="inline-flex h-[14px] w-[14px] items-center justify-center rounded-sm text-[10px] font-bold"
              style={{ background: "#2c7a4f", color: "#dff1e4" }}
            >
              ✓
            </span>
            vindicated
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span
              className="inline-flex h-[14px] w-[14px] items-center justify-center rounded-sm text-[10px] font-bold"
              style={{ background: "#9e2f2f", color: "#f3d9d9" }}
            >
              ✗
            </span>
            rebuked
          </span>
          <span className="text-faint">· grey = pending</span>
        </div>
      </div>

      <div className="overflow-x-auto rounded border border-rule bg-white">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-rule bg-panel">
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Hypothesis
              </th>
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Verdict
              </th>
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Axes
              </th>
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Schools predicting
              </th>
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Sample
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedRuns.map(({ h, run }) => {
              const tone = verdictTone(run.verdict);
              const label = verdictShort(run.verdict);
              const axes = (axisIndex[h.hypothesis_id] ?? []).slice(0, 6);
              const schools = schoolsIndex[h.hypothesis_id] ?? [];
              return (
                <tr
                  key={h.hypothesis_id}
                  className="border-b border-rule last:border-0 hover:bg-panel"
                >
                  <td className="p-3 align-top">
                    <Link
                      href={`/h/${h.hypothesis_id}`}
                      className="font-medium text-ink hover:underline"
                    >
                      {h.claim.split(/(?<=[.!?])\s+/)[0]}
                    </Link>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-[10.5px] text-faint">
                      <span className="font-mono">{h.hypothesis_id}</span>
                      <span className="capitalize">
                        {h.topic.replace(/_/g, " ")}
                      </span>
                    </div>
                  </td>
                  <td className="p-3 align-top">
                    {tone === "green" && (
                      <Badge variant="green" dot>
                        {label}
                      </Badge>
                    )}
                    {tone === "amber" && (
                      <Badge variant="amber" dot>
                        {label}
                      </Badge>
                    )}
                    {tone === "red" && (
                      <Badge variant="red" dot>
                        {label}
                      </Badge>
                    )}
                    {tone === "muted" && (
                      <Badge variant="muted" dot>
                        {label}
                      </Badge>
                    )}
                  </td>
                  <td className="p-3 align-top">
                    {axes.length === 0 ? (
                      <span className="text-[11.5px] text-faint">—</span>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {axes.map((t) => (
                          <AxisChip
                            key={t.axis}
                            axisId={t.axis}
                            axisDef={axesMap[t.axis]}
                            noExplain
                          />
                        ))}
                      </div>
                    )}
                  </td>
                  <td className="p-3 align-top">
                    {schools.length === 0 ? (
                      <span className="text-[11.5px] text-faint">—</span>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {schools.map((s) => {
                          const outcome = schoolOutcome(
                            s.expected_verdict,
                            run.verdict
                          );
                          const outTone = alignmentTone(outcome);
                          return (
                            <Link
                              key={s.position_id}
                              href={`/pos/${s.position_id}`}
                              className="inline-flex items-center gap-1.5 rounded px-1.5 py-[2px] text-[11.5px] font-medium leading-snug ring-1 ring-inset hover:no-underline"
                              style={{
                                background: outTone.bg,
                                color: outTone.fg,
                                borderColor: outTone.ring,
                              }}
                              title={`${s.school} expects ${s.expected_verdict}${
                                s.polarity === "inverted"
                                  ? " (claim is inverted vs hypothesis)"
                                  : ""
                              }${
                                run.verdict
                                  ? ` · actual: ${run.verdict.toLowerCase()}`
                                  : " · run pending"
                              }`}
                            >
                              <span
                                className="inline-flex h-[13px] w-[13px] items-center justify-center rounded-sm text-[9px] font-bold leading-none"
                                style={{
                                  background: outTone.fg,
                                  color: outTone.bg,
                                }}
                                aria-hidden
                              >
                                {outTone.glyph}
                              </span>
                              <span className="font-mono text-[11px]">
                                {s.position_id}
                              </span>
                            </Link>
                          );
                        })}
                      </div>
                    )}
                  </td>
                  <td className="p-3 align-top text-[12px] text-muted">
                    {h.sample
                      ? `${h.sample.countries.length} · ${h.sample.period[0]}–${h.sample.period[1]}`
                      : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
