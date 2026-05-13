import {
  loadAllHypotheses,
  loadAxes,
  loadHypothesisSchoolPredictions,
  loadRunArtifacts,
  isHypothesisPubliclyVisible,
} from "@/lib/content";
import { loadHypothesisAxisIndex } from "@/lib/matching";
import { verdictTone, verdictShort } from "@/lib/verdict";
import {
  HypothesisFilterTable,
  type HypothesisFilterRow,
} from "@/components/hypotheses/HypothesisFilterTable";

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

export default async function HypothesesIndex() {
  const [all, axesMap, axisIndex, schoolsIndex] = await Promise.all([
    loadAllHypotheses(),
    loadAxes(),
    loadHypothesisAxisIndex(),
    loadHypothesisSchoolPredictions(),
  ]);
  const allRuns = await Promise.all(
    all.map(async (h) => ({
      h,
      run: await loadRunArtifacts(h.hypothesis_id),
    }))
  );

  const publicRuns = allRuns.filter((r) => isHypothesisPubliclyVisible(r.h, r.run));
  const verdictCount = publicRuns.length;

  // Sort: public hypotheses with a real verdict first (by tone), then the rest
  // as searchable pending / not-yet-public specs. Do not surface hidden stub
  // diagnostics as verdicts: they are repo artifacts, not public evidence.
  const sortedRuns = allRuns.slice().sort((a, b) => {
    const aPublic = isHypothesisPubliclyVisible(a.h, a.run);
    const bPublic = isHypothesisPubliclyVisible(b.h, b.run);
    if (aPublic !== bPublic) return aPublic ? -1 : 1;
    return (
      sortRank(aPublic ? a.run.verdict : undefined) -
      sortRank(bPublic ? b.run.verdict : undefined)
    );
  });
  const rows: HypothesisFilterRow[] = sortedRuns.map(({ h, run }) => {
    const isPublic = isHypothesisPubliclyVisible(h, run);
    const samplePeriod = h.sample?.period;
    const sample =
      h.sample && Array.isArray(samplePeriod) && samplePeriod.length >= 2
        ? {
            countries: Array.isArray(h.sample.countries)
              ? h.sample.countries
              : [],
            period: [Number(samplePeriod[0]), Number(samplePeriod[1])] as [
              number,
              number,
            ],
            temporal_structure: h.sample.temporal_structure,
          }
        : undefined;

    return {
      hypothesis_id: h.hypothesis_id,
      claim: h.claim,
      topic: h.topic,
      status: h.status,
      evidence_type: h.evidence_type,
      is_public: isPublic,
      verdict: isPublic ? run.verdict : undefined,
      verdict_label: isPublic ? verdictShort(run.verdict) : "run pending",
      verdict_tone: isPublic ? verdictTone(run.verdict) : "muted",
      axes: (axisIndex[h.hypothesis_id] ?? []).map((t) => ({
        axis: t.axis,
        score: t.score,
      })),
      schools: schoolsIndex[h.hypothesis_id] ?? [],
      sample,
    };
  });

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <h1 className="mb-3 text-[32px] font-semibold tracking-[-0.02em]">
        Hypotheses
      </h1>
      <p className="mb-2 max-w-[780px] text-[17px] text-muted">
        Every entry is pre-registered in git before any data is examined.
        Falsification criteria are committed alongside the spec. {verdictCount}{" "}
        of {all.length} are public verdicts; the rest are searchable as
        pre-registered, pending, or not-yet-public specs.
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

      <HypothesisFilterTable rows={rows} axesMap={axesMap} />
    </div>
  );
}
