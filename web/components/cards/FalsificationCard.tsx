import type { Hypothesis } from "@/lib/types";

function formatThreshold(test?: string, threshold?: string | number | null): string {
  const testLine = `test:      ${test ?? "—"}`;
  if (threshold == null) return testLine;
  const thresholdStr = typeof threshold === "string" ? threshold.trim() : String(threshold);
  return `${testLine}\nthreshold: ${thresholdStr}`;
}

export function FalsificationCard({ hypothesis }: { hypothesis: Hypothesis }) {
  if (!hypothesis.falsification) return null;
  const { rule, test, threshold } = hypothesis.falsification;
  return (
    <div className="mb-4 border-l-[3px] border-accent bg-panel px-5 py-4">
      <div className="sc mb-2 text-[11px] font-semibold tracking-[0.1em] text-accent">
        set before the run · honoured after
      </div>
      <p className="mb-1 text-[12.5px] text-muted">
        This hypothesis is considered <strong className="font-semibold text-ink">falsified</strong> if:
      </p>
      <p className="m-0 text-[15px] leading-[1.55] text-ink">{rule.trim()}</p>
      {(test || threshold != null) && (
        <details className="mt-3">
          <summary className="cursor-pointer text-[11.5px] text-muted hover:text-ink">
            formal test &amp; threshold
          </summary>
          <pre className="mt-2 whitespace-pre-wrap rounded bg-code-bg p-3 font-mono text-[12.5px] text-ink">
            {formatThreshold(test, threshold)}
          </pre>
        </details>
      )}
    </div>
  );
}
