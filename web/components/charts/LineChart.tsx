"use client";

import dynamic from "next/dynamic";
import type { LineChartData } from "./LineChartClient";

// Observable Plot touches `document` inside Plot.plot(); disable SSR entirely.
const LineChartClient = dynamic(() => import("./LineChartClient"), {
  ssr: false,
  loading: () => (
    <div
      className="my-2 flex items-center justify-center rounded border border-rule bg-white p-2 text-sm text-muted"
      style={{ minHeight: 420 }}
    >
      Loading chart…
    </div>
  ),
});

export type { LineChartData, LineChartSeries, LineChartPoint } from "./LineChartClient";

export function LineChart({ data }: { data: LineChartData }) {
  return <LineChartClient data={data} />;
}
