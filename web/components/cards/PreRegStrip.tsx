import type { Hypothesis } from "@/lib/types";

export function PreRegStrip({ hypothesis }: { hypothesis: Hypothesis }) {
  const priorPct = Math.round((hypothesis.prior_confidence ?? 0) * 100);
  const commit = hypothesis._first_commit;
  return (
    <div className="mb-5 flex items-center gap-5 rounded bg-green-soft px-5 py-3.5">
      <div>
        <div className="sc text-[11px] font-semibold tracking-[0.08em] text-green">pre-registered</div>
        <div className="mt-0.5 font-mono text-[13px] text-ink">
          {commit
            ? `commit ${commit.hash} · ${commit.iso.slice(0, 19)}Z`
            : "commit pending — not yet in git history"}
        </div>
      </div>
      <div className="ml-auto flex items-center gap-2.5">
        <div>
          <div className="sc text-[11px]">prior</div>
          <div className="mt-1 h-[6px] w-[100px] overflow-hidden rounded-[3px] bg-black/10">
            <div className="h-full bg-green" style={{ width: `${priorPct}%` }} />
          </div>
        </div>
        <div className="text-base font-semibold text-green">
          {hypothesis.prior_confidence != null ? hypothesis.prior_confidence.toFixed(2) : "—"}
        </div>
      </div>
    </div>
  );
}
