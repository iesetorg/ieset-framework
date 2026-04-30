// RatioChart — for chart_data.json payloads where each series entry is a
// single scalar (value + threshold), not a time series. Used by ratio /
// canonical-basket comparison charts (Costa Rica wellbeing-throughput, Cuba
// canonical basket, Japan wellbeing, single-payer cost-outcome, UK-Cameron
// austerity, Cuba resilience). The LineChart can't render this shape because
// there's no x-axis time dimension.

interface RatioPoint {
  name: string;
  value: number | null;
  threshold?: number | null;
}

interface RatioChartData {
  kind?: "result" | "sketch";
  title?: string;
  series: RatioPoint[];
  annotations?: string[];
}

export function RatioChart({ data }: { data: RatioChartData }) {
  const points = (data.series ?? []).filter(
    (p) => typeof p.value === "number" && !Number.isNaN(p.value)
  ) as { name: string; value: number; threshold?: number | null }[];

  if (points.length === 0) {
    return (
      <div className="rounded border border-rule bg-panel p-6 text-[13px] text-muted">
        No comparable values were emitted by this run.
      </div>
    );
  }

  // Bar scale: max of all |value| and |threshold| × 1.1 padding.
  const allMagnitudes = points.flatMap((p) => [
    Math.abs(p.value),
    typeof p.threshold === "number" ? Math.abs(p.threshold) : 0,
  ]);
  const max = Math.max(...allMagnitudes, 1) * 1.15;

  return (
    <div className="rounded border border-rule bg-white">
      <div className="border-b border-rule px-5 py-3">
        <h3 className="m-0 text-[14px] font-semibold text-ink">
          {data.title ?? "Run statistics"}
        </h3>
      </div>
      <div className="space-y-3 px-5 py-5">
        {points.map((p) => {
          const valuePct = (Math.abs(p.value) / max) * 100;
          const thresholdPct =
            typeof p.threshold === "number"
              ? (Math.abs(p.threshold) / max) * 100
              : null;
          return (
            <div key={p.name} className="space-y-1">
              <div className="flex items-baseline justify-between gap-3 text-[12.5px]">
                <span className="font-mono text-muted">{p.name}</span>
                <span className="font-mono text-ink">
                  {formatNumber(p.value)}
                  {typeof p.threshold === "number" && (
                    <span className="ml-2 text-faint">
                      threshold {formatNumber(p.threshold)}
                    </span>
                  )}
                </span>
              </div>
              <div className="relative h-2 rounded-sm bg-panel">
                <div
                  className="absolute inset-y-0 left-0 rounded-sm bg-[#1f4e79]"
                  style={{ width: `${valuePct}%` }}
                />
                {thresholdPct !== null && (
                  <div
                    className="absolute inset-y-[-3px] w-px bg-[#9e2f2f]"
                    style={{ left: `${thresholdPct}%` }}
                    title={`threshold ${p.threshold}`}
                  />
                )}
              </div>
            </div>
          );
        })}
      </div>
      {data.annotations && data.annotations.length > 0 && (
        <div className="border-t border-rule px-5 py-3 text-[12px] leading-relaxed text-muted">
          {data.annotations.map((a, i) => (
            <p key={i} className="m-0">
              {a}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

function formatNumber(n: number): string {
  if (Math.abs(n) >= 1000) return n.toLocaleString();
  if (Math.abs(n) >= 1) return n.toFixed(2);
  if (Math.abs(n) >= 0.001) return n.toFixed(4);
  return n.toExponential(2);
}
