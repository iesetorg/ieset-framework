import Link from "next/link";

import {
  loadHypothesis,
  loadRunArtifacts,
} from "@/lib/content";
import { verdictTone } from "@/lib/verdict";

/**
 * Two hypotheses, side-by-side, showing what one round of pre-registration →
 * data → verdict actually looks like. One supported, one refuted, deliberately —
 * to demonstrate that a verdict against the framework's own author's prior is
 * scored the same as one in their favour.
 *
 * Picks specific IDs so the showcase is reproducible on every deploy and the
 * editorial logic is transparent.
 */

const FEATURED = [
  {
    hypothesis_id: "post_soviet_market_reform_life_expectancy",
    short_claim:
      "Post-1989 fast-reforming countries (Poland, Czechia, Estonia) gained more life-years than slow-reformers (Belarus, Ukraine).",
    falsification:
      "REFUTE if fast reformers don't gain at least +1.5 more life-years than slow reformers from 1989 → 2019.",
    headline:
      "β_fast = −0.04y (n.s.) · β_slow = −3.46y (p<0.001) · gap = +3.43y",
  },
  {
    hypothesis_id: "liberal_democracy_managerial_flywheel_drift",
    short_claim:
      "Liberal democracies experience monotonic positional drift toward more state activity over multi-decade horizons (the 'managerial flywheel' thesis).",
    falsification:
      "SUPPORTED only if median LD final composite drift > 0 AND share-positive significantly > 50% AND median per-decade slope > 0.",
    headline:
      "12 / 26 LDs net-positive · median drift −1.00 · slope −4.43 / decade · binomial p = 0.72",
  },
] as const;

export async function WorkedExamples() {
  const featured = await Promise.all(
    FEATURED.map(async (entry) => {
      const [hyp, run] = await Promise.all([
        loadHypothesis(entry.hypothesis_id),
        loadRunArtifacts(entry.hypothesis_id),
      ]);
      return { entry, hyp, run };
    })
  );

  return (
    <div className="rounded-lg border border-rule bg-white p-6">
      <div className="mb-2 flex items-baseline justify-between">
        <h2 className="m-0 text-[22px] font-semibold tracking-[-0.01em]">
          Two worked examples
        </h2>
        <Link href="/h" className="text-[13px] text-muted hover:text-ink">
          all hypotheses →
        </Link>
      </div>
      <p className="mb-5 max-w-[780px] text-[14.5px] leading-[1.6] text-muted">
        Every hypothesis is committed to git with its claim, its data sources,
        and its falsification rule <em>before</em> the data is examined. The
        rule is what determines the verdict — never an after-the-fact judgement
        call. Below: one hypothesis the data supported, one the data refuted.
        Same rule shape, opposite outcomes.
      </p>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {featured.map(({ entry, hyp, run }) => {
          const tone = verdictTone(run.verdict);
          const tonePill =
            tone === "green"
              ? { bg: "#dff1e4", fg: "#2c7a4f", label: "supported" }
              : tone === "red"
              ? { bg: "#f3d9d9", fg: "#9e2f2f", label: "refuted" }
              : tone === "amber"
              ? { bg: "#fdf1da", fg: "#b7791f", label: "partial" }
              : { bg: "#f3f3f1", fg: "#636363", label: "result" };
          const bar =
            tone === "green"
              ? "#2c7a4f"
              : tone === "red"
              ? "#9e2f2f"
              : tone === "amber"
              ? "#b7791f"
              : "#aaa";
          const preRegIso =
            (hyp?._first_commit?.iso ?? "").slice(0, 10) || "—";

          return (
            <Link
              key={entry.hypothesis_id}
              href={`/h/${entry.hypothesis_id}`}
              className="group block overflow-hidden rounded border border-rule bg-white hover:border-rule-strong hover:no-underline"
            >
              <div className="h-[3px]" style={{ background: bar }} />
              <div className="p-5">
                <div className="mb-3 flex items-center gap-2">
                  <span
                    className="inline-flex items-center rounded px-2 py-[3px] text-[10.5px] font-semibold uppercase tracking-wider"
                    style={{ background: tonePill.bg, color: tonePill.fg }}
                  >
                    {tonePill.label}
                  </span>
                  <span className="text-[10.5px] uppercase tracking-wider text-muted">
                    pre-registered {preRegIso}
                  </span>
                </div>

                <h3 className="m-0 mb-3 text-[15.5px] font-semibold leading-[1.35] text-ink group-hover:text-accent">
                  {entry.short_claim}
                </h3>

                <dl className="m-0 space-y-2.5 text-[12.5px] leading-[1.5]">
                  <div>
                    <dt className="text-[10px] font-semibold uppercase tracking-wider text-muted">
                      Falsification rule (pre-committed)
                    </dt>
                    <dd className="m-0 mt-0.5 text-ink">{entry.falsification}</dd>
                  </div>
                  <div>
                    <dt className="text-[10px] font-semibold uppercase tracking-wider text-muted">
                      Result
                    </dt>
                    <dd
                      className="m-0 mt-0.5 font-mono text-[12px] leading-[1.5]"
                      style={{ color: tonePill.fg }}
                    >
                      {entry.headline}
                    </dd>
                  </div>
                </dl>

                <div className="mt-3 flex items-center justify-between text-[11.5px]">
                  <span className="font-mono text-[10.5px] text-faint">
                    {entry.hypothesis_id}
                  </span>
                  <span className="text-accent">read full result card →</span>
                </div>
              </div>
            </Link>
          );
        })}
      </div>

      <p className="mt-5 text-[12.5px] leading-[1.55] text-muted">
        <strong className="text-ink">What this is doing:</strong> the
        falsification rule is committed{" "}
        <em>before</em> the run, the data substrate is logged with vintages,
        the replication.py is reproducible end-to-end, and the verdict is
        whatever the rule says — no post-hoc reframing. The right-hand card
        explicitly rebuked one of the framework author&apos;s priors. That&apos;s
        the system working.
      </p>
    </div>
  );
}
