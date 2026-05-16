"use client";

import { useEffect, useRef } from "react";

interface SeriesPoint {
  year: number;
  value: number;
  country: string;
}

interface MovementAnnotation {
  /** ISO3 — must match a key in `series`. */
  country: string;
  /** Year of the movement's start (positioning along x-axis). */
  year: number;
  /** Display name shown next to the marker. */
  label: string;
  /** Optional ideological tone — drives marker fill colour.
   *  "left" = state-expansion (red), "right" = market (green),
   *  "centrist" = amber, "auth" = grey, default = neutral. */
  tone?: "left" | "right" | "centrist" | "auth" | "neutral";
}

interface DriftChartProps {
  /** Per-country trajectory series. */
  series: Record<string, number[]>;
  /** Years aligned to each series. */
  years: number[];
  /** Map ISO3 → display name (must be serialisable; passed across the
   * server-component / client-component boundary). */
  labels?: Record<string, string>;
  /** Subtitle / caption shown below the chart. */
  caption?: string;
  /** Pixel height of the chart. */
  height?: number;
  /** Optional zero-line label for context. */
  zeroLineLabel?: string;
  /** Highlight a single country (drawn thicker). */
  highlight?: string;
  /** Movement events to plot directly on the country trajectory line. */
  movements?: MovementAnnotation[];
}

const FALLBACK_PALETTE = [
  "#2c5d8a",
  "#9e2f2f",
  "#2c7a4f",
  "#b7791f",
  "#5a3a78",
  "#8a4d2c",
  "#1f6470",
  "#7a2c4f",
  "#4f5a78",
  "#2c7a76",
  "#c0392b",
  "#27ae60",
];

const TONE_COLOR: Record<string, string> = {
  left: "#9e2f2f",
  right: "#2c7a4f",
  centrist: "#b7791f",
  auth: "#636363",
  neutral: "#3a3a35",
};

function compactLeaderLabel(label: string) {
  const parts = label.trim().split(/\s+/).filter(Boolean);
  if (parts.length < 2) return label;
  return parts[parts.length - 1];
}

export function DriftChart({
  series,
  years,
  labels,
  caption,
  height = 380,
  zeroLineLabel,
  highlight,
  movements,
}: DriftChartProps) {
  const ref = useRef<HTMLDivElement>(null);
  const labelFor = (key: string) => labels?.[key] ?? key;

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!ref.current) return;
      // Observable Plot is dynamically loaded so it never goes through SSR.
      const Plot = await import("@observablehq/plot");
      const chartWidth = ref.current.clientWidth;

      // Flatten to long form.
      const points: SeriesPoint[] = [];
      for (const [country, traj] of Object.entries(series)) {
        for (let i = 0; i < traj.length; i++) {
          points.push({ year: years[i], value: traj[i], country });
        }
      }

      const countries = Object.keys(series);
      const palette: Record<string, string> = {};
      countries.forEach((c, i) => {
        palette[c] = FALLBACK_PALETTE[i % FALLBACK_PALETTE.length];
      });

      // Vanilla extent — d3-array is only a transitive dep so its import
      // can fail silently in the client bundle. min/max over the values
      // is two lines and saves the entire d3 dependency.
      const values = points.map((p) => p.value);
      const yMin = values.length ? Math.min(...values) : 0;
      const yMax = values.length ? Math.max(...values) : 1;
      const yExtent: [number, number] = [yMin, yMax];
      const yPad = Math.max(2, (yExtent[1] - yExtent[0]) * 0.08);
      const xMin = Math.min(...years);
      const xMax = Math.max(...years);

      const hasMovementLabels = Boolean(movements && movements.length > 0);
      const node = Plot.plot({
        width: chartWidth,
        height,
        marginLeft: 56,
        marginRight: hasMovementLabels ? 64 : 34,
        marginBottom: 36,
        marginTop: hasMovementLabels ? 28 : 12,
        x: {
          label: "year",
          domain: [xMin, xMax],
          tickFormat: "d",
        },
        y: {
          label: zeroLineLabel ?? "cumulative drift index",
          domain: [yExtent[0] - yPad, yExtent[1] + yPad],
          grid: true,
        },
        marks: [
          // zero reference line
          Plot.ruleY([0], { stroke: "#9b9b95", strokeDasharray: "3,3" }),
          // each country's trajectory
          Plot.line(points, {
            x: "year",
            y: "value",
            stroke: (d: SeriesPoint) => palette[d.country],
            strokeWidth: (d: SeriesPoint) => (d.country === highlight ? 2.6 : 1.5),
            curve: "step-after",
          }),
          // end-of-line label
          Plot.text(
            countries.map((c) => {
              const traj = series[c];
              return { country: c, year: years[years.length - 1], value: traj[traj.length - 1] };
            }),
            {
              x: "year",
              y: "value",
              text: (d: { country: string }) => labelFor(d.country),
              dx: 6,
              fontSize: 10.5,
              fill: (d: { country: string }) => palette[d.country],
              fontWeight: highlight ? 700 : 400,
              textAnchor: "start",
            }
          ),
          // Movement annotations on the trajectory line. The visible labels
          // stay short by using the movement's lead figure, while the timeline
          // below carries the full movement name and context.
          ...(movements && movements.length > 0
            ? (() => {
                type AnnotatedDot = {
                  year: number;
                  value: number;
                  country: string;
                  tone: "left" | "right" | "centrist" | "auth" | "neutral";
                  label: string;
                  displayLabel: string;
                  labelDy: number;
                  labelAnchor: "start" | "end";
                };
                const compactLabels = chartWidth < 640;
                const rawDots = movements
                  .map((m): AnnotatedDot | null => {
                    const traj = series[m.country];
                    if (!traj) return null;
                    const yi = years.indexOf(m.year);
                    if (yi < 0) return null;
                    return {
                      year: m.year,
                      value: traj[yi],
                      country: m.country,
                      tone: m.tone ?? "neutral",
                      label: m.label,
                      displayLabel: m.label,
                      labelDy: -11,
                      labelAnchor: "start",
                    };
                  })
                  .filter((x): x is AnnotatedDot => x !== null);
                const dots = [...rawDots].sort((a, b) => a.year - b.year);
                let lane = 0;
                let previousYear = Number.NEGATIVE_INFINITY;
                for (const dot of dots) {
                  lane = dot.year - previousYear <= 3 ? (lane + 1) % 4 : 0;
                  previousYear = dot.year;
                  const nearRightEdge = dot.year >= xMax - 3;
                  dot.labelAnchor =
                    nearRightEdge || (compactLabels && lane >= 2)
                      ? "end"
                      : "start";
                  dot.labelDy = [-12, 14, -28, 30][lane];
                  dot.displayLabel =
                    compactLabels && !(lane <= 1 || nearRightEdge)
                      ? ""
                      : compactLabels
                      ? compactLeaderLabel(dot.label)
                      : dot.label;
                }
                const labelMarks = [-28, -12, 14, 30].flatMap((dy) =>
                  (["start", "end"] as const).flatMap((anchor) => {
                    const labelled = dots.filter(
                      (d) =>
                        d.displayLabel &&
                        d.labelDy === dy &&
                        d.labelAnchor === anchor
                    );
                    if (labelled.length === 0) return [];
                    return [
                      Plot.text(labelled, {
                        x: "year",
                        y: "value",
                        text: (d: { displayLabel: string }) => d.displayLabel,
                        dx: anchor === "end" ? -8 : 8,
                        dy,
                        textAnchor: anchor,
                        fontSize: compactLabels ? 9.5 : 10.5,
                        fill: "#4a4a45",
                        stroke: "white",
                        strokeWidth: 4,
                        paintOrder: "stroke",
                      }),
                    ];
                  })
                );
                return [
                  ...labelMarks,
                  Plot.dot(dots, {
                    x: "year",
                    y: "value",
                    r: 5,
                    fill: (d: { tone: string }) =>
                      TONE_COLOR[d.tone] ?? TONE_COLOR.neutral,
                    stroke: "white",
                    strokeWidth: 1.5,
                    title: (d: { label: string }) => d.label,
                  }),
                ];
              })()
            : []),
        ],
      });

      if (cancelled) return;
      ref.current.innerHTML = "";
      ref.current.appendChild(node as unknown as Node);
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [series, years, labels, height, zeroLineLabel, highlight, movements]);

  return (
    <div>
      <div ref={ref} style={{ width: "100%" }} />
      {caption && (
        <p className="m-0 mt-2 text-[12.5px] leading-[1.5] text-muted">
          {caption}
        </p>
      )}
    </div>
  );
}
