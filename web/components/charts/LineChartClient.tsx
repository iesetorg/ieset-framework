"use client";

import { useEffect, useRef, useState } from "react";

export interface LineChartPoint {
  x: number;
  y: number;
}
export interface LineChartSeries {
  id: string;
  label: string;
  color?: string;
  nordic?: boolean;
  treated?: boolean;
  points: LineChartPoint[];
}
export interface LineChartData {
  chart_id?: string;
  title?: string;
  subtitle?: string;
  type: "line";
  x_axis: { label?: string; type?: string };
  y_axis: { label?: string; type?: "linear" | "log" };
  series: LineChartSeries[];
  annotations?: { type: string; label: string; x?: number }[];
  sources?: { publisher_id: string; series_id: string; vintage_file?: string }[];
  permalink?: string;
}

export default function LineChartClient({ data }: { data: LineChartData }) {
  const ref = useRef<HTMLDivElement>(null);
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const Plot = await import("@observablehq/plot");
        if (cancelled || !ref.current) return;

        const flat: { x: number; y: number; series: string }[] = [];
        for (const s of data.series) {
          if (hidden.has(s.id)) continue;
          for (const p of s.points) {
            if (Number.isFinite(p.x) && Number.isFinite(p.y)) {
              flat.push({ x: p.x, y: p.y, series: s.id });
            }
          }
        }
        const colorMap: Record<string, string> = {};
        for (const s of data.series) colorMap[s.id] = s.color ?? "#4E79A7";

        const endPoints = data.series
          .filter((s) => !hidden.has(s.id) && s.points.length > 0)
          .map((s) => {
            const last = s.points[s.points.length - 1];
            return {
              x: last.x,
              y: last.y,
              label: s.label,
              color: s.color ?? "#4E79A7",
            };
          });

        const marks: unknown[] = [
          Plot.line(flat, {
            x: "x",
            y: "y",
            stroke: "series",
            strokeWidth: 2,
          }),
          Plot.dot(endPoints, {
            x: "x",
            y: "y",
            fill: "color",
            r: 3.5,
          }),
          Plot.text(endPoints, {
            x: "x",
            y: "y",
            text: "label",
            fill: "color",
            dx: 8,
            fontSize: 11,
            fontFamily: "ui-monospace, monospace",
            textAnchor: "start",
          }),
        ];

        const chart = Plot.plot({
          width: 900,
          height: 420,
          marginTop: 24,
          marginRight: 80,
          marginBottom: 40,
          marginLeft: 56,
          style: {
            background: "transparent",
            fontFamily:
              "-apple-system, BlinkMacSystemFont, system-ui, sans-serif",
            fontSize: "12px",
            color: "#1f1f1f",
          },
          x: {
            label: data.x_axis.label ?? "",
            tickFormat: (d: number) => String(Math.round(d)),
            grid: false,
          },
          y: {
            label: data.y_axis.label ?? "",
            grid: true,
            ...(data.y_axis.type === "log" ? { type: "log" as const } : {}),
          },
          color: {
            domain: Object.keys(colorMap),
            range: Object.values(colorMap),
          },
          // @ts-expect-error marks typing is loose in Plot
          marks,
        });

        ref.current.innerHTML = "";
        ref.current.appendChild(chart);

        return () => chart.remove();
      } catch (e) {
        setErr(e instanceof Error ? e.message : String(e));
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [data, hidden]);

  const hasSources = data.sources && data.sources.length > 0;
  const hasLegend = data.series.length > 1;
  const treatedIds = new Set(
    data.series.filter((s) => s.treated).map((s) => s.id)
  );

  return (
    <figure className="my-2">
      {(data.title || data.subtitle) && (
        <figcaption className="mb-2">
          {data.title && (
            <div className="text-[15px] font-semibold leading-snug text-ink">
              {data.title}
            </div>
          )}
          {data.subtitle && (
            <div className="mt-0.5 text-[13px] text-muted">{data.subtitle}</div>
          )}
        </figcaption>
      )}

      <div
        ref={ref}
        className="w-full overflow-x-auto rounded border border-rule bg-white p-2"
        style={{ minHeight: 420 }}
      >
        {err ? (
          <div className="p-6 text-sm text-red">
            <div className="mb-2 font-semibold">Chart failed to render</div>
            <code className="text-xs">{err}</code>
          </div>
        ) : (
          <div className="p-6 text-sm text-muted">Loading chart…</div>
        )}
      </div>

      {hasLegend && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="sc mr-1 text-[10px]">series</span>
          {data.series.map((s) => {
            const isHidden = hidden.has(s.id);
            const isTreated = treatedIds.has(s.id);
            return (
              <button
                key={s.id}
                onClick={() =>
                  setHidden((prev) => {
                    const n = new Set(prev);
                    n.has(s.id) ? n.delete(s.id) : n.add(s.id);
                    return n;
                  })
                }
                className="inline-flex items-center rounded-full border px-2.5 py-[3px] text-xs font-medium transition-colors"
                style={{
                  color: isHidden ? "#8a8a8a" : "#1f1f1f",
                  background: isHidden ? "#fafaf8" : "#fff",
                  borderColor: isTreated ? s.color ?? "#4E79A7" : "#d9d9d9",
                  borderWidth: isTreated ? 1.5 : 1,
                  textDecoration: isHidden ? "line-through" : "none",
                }}
                aria-pressed={!isHidden}
                title={isTreated ? "treated unit" : "donor / comparison"}
              >
                <span
                  className="mr-1.5 inline-block h-2 w-2 rounded-full"
                  style={{
                    background: isHidden ? "#d9d9d9" : s.color ?? "#4E79A7",
                  }}
                />
                {s.label}
                {isTreated && (
                  <span className="ml-1 text-[9px] uppercase tracking-wider text-muted">
                    treated
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {hasSources && (
        <div className="mt-3 border-t border-rule pt-2 text-[11.5px] leading-[1.5] text-muted">
          <span className="sc mr-2 text-[10px]">sources</span>
          {data.sources!.map((s, i) => (
            <span key={i}>
              {i > 0 && " · "}
              <span className="font-mono text-[11px] text-ink">
                {s.publisher_id}:{s.series_id}
              </span>
            </span>
          ))}
        </div>
      )}
    </figure>
  );
}
