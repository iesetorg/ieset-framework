import type { Hypothesis } from "@/lib/types";

const seriesColors = [
  "#4E79A7", "#59A14F", "#B07AA1", "#E15759",
  "#F28E2B", "#76B7B2", "#EDC948", "#B6992D", "#9C755F",
];

// An illustrative-only static SVG shown while the hypothesis has no run artifact.
// The shape is stylised, not real data. A clear "run pending" banner makes this
// unambiguous per METHODOLOGY.md invariant 6 (legible about what's known vs claimed).
export function PlaceholderChart({ hypothesis }: { hypothesis: Hypothesis }) {
  const countries = hypothesis.sample?.countries ?? [];
  const [start, end] = hypothesis.sample?.period ?? [2000, 2025];

  // Generate stylised illustrative trajectories (not real data; visually conveys shape only)
  const showCountries = countries.slice(0, 7);
  const trajectories = showCountries.map((code, i) => ({
    code,
    color: seriesColors[i % seriesColors.length],
    path: makeStylisedPath(i),
    endY: 320 + (i % 7) * 8,
  }));

  return (
    <figure className="my-4">
      <div className="relative">
        <svg
          viewBox="0 0 900 420"
          preserveAspectRatio="xMidYMid meet"
          className="block h-auto w-full"
        >
          {/* grid */}
          <g className="chart-grid">
            <line x1="70" y1="40"  x2="820" y2="40" />
            <line x1="70" y1="108" x2="820" y2="108" />
            <line x1="70" y1="176" x2="820" y2="176" />
            <line x1="70" y1="244" x2="820" y2="244" />
            <line x1="70" y1="312" x2="820" y2="312" />
          </g>
          {/* axes */}
          <g className="chart-axis">
            <line x1="70" y1="40" x2="70" y2="380" />
            <text x="60" y="44"  textAnchor="end">100</text>
            <text x="60" y="112" textAnchor="end">75</text>
            <text x="60" y="180" textAnchor="end">50</text>
            <text x="60" y="248" textAnchor="end">25</text>
            <text x="60" y="384" textAnchor="end">0</text>
            <line x1="70" y1="380" x2="820" y2="380" />
            <text x="70"  y="400" textAnchor="middle">{start}</text>
            <text x="445" y="400" textAnchor="middle">{Math.round((start + end) / 2)}</text>
            <text x="820" y="400" textAnchor="middle">{end}</text>
          </g>
          <line className="chart-baseline" x1="70" y1="40" x2="820" y2="40" />

          {trajectories.map((t) => (
            <g key={t.code}>
              <path fill="none" stroke={t.color} strokeWidth="2" d={t.path} />
              <circle cx="820" cy={t.endY} r="3" fill={t.color} />
              <text
                className="chart-end-label"
                x="826"
                y={t.endY + 3}
                fill={t.color}
              >
                {t.code}
              </text>
            </g>
          ))}
        </svg>

        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div className="max-w-[440px] rounded border border-amber/40 bg-white/95 px-5 py-3.5 text-center shadow-sm">
            <div className="sc mb-1 text-[10px] font-semibold tracking-[0.1em] text-amber">
              illustrative sketch · run pending
            </div>
            <div className="text-[13px] leading-[1.5] text-ink">
              No coefficients yet. When the model fires, this chart will show{" "}
              <strong className="font-semibold">
                {hypothesis.variables?.outcome?.[0]?.name ?? "the outcome variable"}
              </strong>{" "}
              across {(hypothesis.sample?.countries?.length ?? 0) || "the"} sampled
              countries over {hypothesis.sample?.period?.[0] ?? ""}
              {hypothesis.sample?.period ? "–" : ""}
              {hypothesis.sample?.period?.[1] ?? ""}.
            </div>
            <div className="mt-1.5 text-[11.5px] text-muted">
              The shapes above are stylised — none of the lines are real data.
            </div>
          </div>
        </div>
      </div>
      <figcaption className="mt-3 text-[11px] leading-[1.5] text-faint">
        Placeholder for <code className="text-[10.5px]">{hypothesis.hypothesis_id}</code>.
        Published chart will be generated from{" "}
        <code className="text-[10.5px]">engine/runs/{hypothesis.hypothesis_id}/chart_data.json</code>.
      </figcaption>
    </figure>
  );
}

// A handful of stylised declining trajectories — different shapes per series index.
function makeStylisedPath(idx: number): string {
  const base = [
    "M70 40 L125 62 L180 120 L235 175 L290 200 L345 190 L400 185 L455 195 L510 215 L565 230 L620 240 L675 250 L730 290 L785 325 L820 340",
    "M70 40 L125 90 L180 160 L235 210 L290 230 L345 230 L400 240 L455 250 L510 260 L565 260 L620 270 L675 280 L730 310 L785 345 L820 355",
    "M70 40 L125 58 L180 105 L235 150 L290 165 L345 160 L400 170 L455 195 L510 210 L565 225 L620 230 L675 245 L730 275 L785 315 L820 325",
    "M70 40 L125 95 L180 170 L235 230 L290 255 L345 265 L400 275 L455 280 L510 285 L565 285 L620 290 L675 295 L730 320 L785 355 L820 362",
    "M70 40 L125 110 L180 210 L235 280 L290 310 L345 320 L400 325 L455 325 L510 330 L565 330 L620 335 L675 340 L730 345 L785 368 L820 370",
    "M70 40 L125 70 L180 135 L235 170 L290 175 L345 155 L400 165 L455 180 L510 200 L565 220 L620 235 L675 240 L730 270 L785 310 L820 330",
    "M70 40 L125 85 L180 150 L235 200 L290 225 L345 225 L400 235 L455 250 L510 265 L565 275 L620 285 L675 290 L730 315 L785 345 L820 350",
  ];
  return base[idx % base.length];
}
