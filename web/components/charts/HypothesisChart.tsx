import type { Hypothesis } from "@/lib/types";
import { loadChartData } from "@/lib/content";
import { PlaceholderChart } from "./PlaceholderChart";
import { LineChart, type LineChartData } from "./LineChart";

interface ChartPayload extends LineChartData {
  kind?: "sketch" | "result";
}

export async function HypothesisChart({ hypothesis }: { hypothesis: Hypothesis }) {
  const chartData = (await loadChartData(hypothesis.hypothesis_id)) as
    | ChartPayload
    | null;
  if (!chartData) return <PlaceholderChart hypothesis={hypothesis} />;

  const isSketch = chartData.kind === "sketch";
  return (
    <div>
      {isSketch && (
        <div className="mb-3 inline-flex items-center gap-2 rounded-sm bg-amber-soft px-2.5 py-[3px] text-[11px] font-medium text-amber">
          <span className="inline-block h-[6px] w-[6px] rounded-full bg-amber" />
          descriptive sketch · model not yet run
        </div>
      )}
      <LineChart data={chartData} />
    </div>
  );
}
