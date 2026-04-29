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

      const node = Plot.plot({
        width: ref.current.clientWidth,
        height,
        marginLeft: 56,
        marginRight: 24,
        marginBottom: 36,
        marginTop: 12,
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
          // Movement annotations on the trajectory line — colored dots only.
          // We removed the on-chart text labels because adjacent-year
          // movements (e.g. Canada 1980-2006 with 8 governments inside 26
          // years) made labels overlap unreadably no matter how we
          // staggered them. The full labelled timeline lives in the
          // movement-timeline table below the chart, which is more
          // legible and accessible than cramped on-chart text. The dots
          // alone still tell the user "an event happened in this year,
          // tone-coloured by its policy direction."
          ...(movements && movements.length > 0
            ? (() => {
                type AnnotatedDot = {
                  year: number;
                  value: number;
                  country: string;
                  tone: "left" | "right" | "centrist" | "auth" | "neutral";
                  label: string;
                };
                const dots: AnnotatedDot[] = movements
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
                    };
                  })
                  .filter((x): x is AnnotatedDot => x !== null);
                return [
                  Plot.dot(dots, {
                    x: "year",
                    y: "value",
                    r: 5,
                    fill: (d: { tone: string }) =>
                      TONE_COLOR[d.tone] ?? TONE_COLOR.neutral,
                    stroke: "white",
                    strokeWidth: 1.5,
                    title: (d: { label: string; year: number }) =>
                      `${d.year} · ${d.label}`,
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
