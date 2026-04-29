import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";

import { loadDrift, countryName } from "@/lib/drift";
import { loadAxes } from "@/lib/content";
import { DriftChart } from "@/components/charts/DriftChartLoader";
import { AxisChip } from "@/components/badges/AxisChip";

export async function generateStaticParams() {
  const data = await loadDrift();
  if (!data) return [];
  return Object.keys(data.countries).map((iso3) => ({ iso3 }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ iso3: string }>;
}): Promise<Metadata> {
  const { iso3 } = await params;
  const name = countryName(iso3);
  return {
    title: `${name} — positional drift`,
    description: `Per-axis cumulative drift trajectory for ${name}, computed from movement axes_summaries.`,
  };
}

const CHANNEL_ORDER = ["fiscal", "regulatory", "monetary", "institutional"];

export default async function CountryPage({
  params,
}: {
  params: Promise<{ iso3: string }>;
}) {
  const { iso3 } = await params;
  const data = await loadDrift();
  if (!data) return notFound();
  const country = data.countries[iso3];
  if (!country) return notFound();

  const axesMap = await loadAxes();

  const finalDrift = country.statist_drift[country.statist_drift.length - 1] ?? 0;
  const tone =
    finalDrift > 8
      ? { bg: "#f3d9d9", fg: "#9e2f2f", label: "net statist drift" }
      : finalDrift < -8
      ? { bg: "#dff1e4", fg: "#2c7a4f", label: "net market drift" }
      : { bg: "#fdf1da", fg: "#b7791f", label: "≈ stable" };

  // Group axes by channel + only show ones that actually moved.
  const movedAxes: Record<string, string[]> = {};
  for (const axis of data.axes) {
    const traj = country.axes[axis];
    if (!traj || traj.every((v) => v === 0)) continue;
    const channel = axis.split(".")[0];
    (movedAxes[channel] ??= []).push(axis);
  }
  const orderedChannels = [
    ...CHANNEL_ORDER.filter((c) => movedAxes[c]),
    ...Object.keys(movedAxes).filter((c) => !CHANNEL_ORDER.includes(c)),
  ];

  // For per-channel charts, build a series-of-axes (one line per axis).
  function seriesForChannel(channel: string) {
    const out: Record<string, number[]> = {};
    for (const axis of movedAxes[channel] ?? []) {
      const traj = country.axes[axis];
      if (!traj) continue;
      // Use short label as the series key so the chart legend shows
      // human-readable axis names.
      const short = axis.split(".").slice(-1)[0].replace(/_/g, " ");
      out[short] = traj;
    }
    return out;
  }

  // Composite series, just the country alone.
  const compositeSeries: Record<string, number[]> = {
    [iso3]: country.statist_drift,
  };

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <div className="mb-3 flex items-center gap-3 text-[13px] text-muted">
        <Link
          href="/drift"
          className="text-muted hover:text-ink hover:no-underline"
        >
          Drift overview
        </Link>
        <span>·</span>
        <span className="font-mono text-[11px] text-faint">{iso3}</span>
      </div>
      <h1 className="m-0 mb-3 text-[36px] font-semibold leading-[1.15] tracking-[-0.02em]">
        {countryName(iso3)}
      </h1>

      <div className="mb-6 flex flex-wrap items-center gap-3 text-[13.5px]">
        <span
          className="inline-flex items-center rounded px-2 py-[3px] text-[11px] font-semibold uppercase tracking-wider"
          style={{ background: tone.bg, color: tone.fg }}
        >
          {tone.label}
        </span>
        <span className="text-muted">
          {country.movement_count} movements coded ·{" "}
          {country.movements[0]?.year} → {country.movements[country.movements.length - 1]?.year}
        </span>
        <span className="text-muted">·</span>
        <span className="text-ink">
          final composite drift:{" "}
          <strong className="tabular-nums">
            {finalDrift >= 0 ? "+" : ""}
            {finalDrift.toFixed(1)}
          </strong>
        </span>
      </div>

      {/* Composite trajectory with movement annotations */}
      <div className="mb-3 flex flex-wrap items-center gap-3 text-[11.5px] text-muted">
        <span className="font-semibold uppercase tracking-wider">tone legend</span>
        <span className="inline-flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: "#9e2f2f" }} />
          left / state-expansion
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: "#2c7a4f" }} />
          right / market
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: "#b7791f" }} />
          centrist / mixed
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: "#636363" }} />
          authoritarian
        </span>
      </div>
      <div className="mb-10 rounded border border-rule bg-white p-5">
        <h2 className="m-0 mb-3 text-[16px] font-semibold">
          Composite statist-drift trajectory with movements
        </h2>
        <DriftChart
          series={compositeSeries}
          years={data.years}
          labels={{ [iso3]: countryName(iso3) }}
          movements={country.movements
            .filter((m) => m.year >= data.year_min)
            .map((m) => ({
              country: iso3,
              year: m.year,
              label: m.name.length > 28 ? m.name.slice(0, 26) + "…" : m.name,
              tone: m.tone ?? "neutral",
            }))}
          height={300}
          zeroLineLabel="cumulative statist drift"
          caption="Cumulative net direction across all 14 valenced axes. Above 0 = state-expansion direction since corpus start; below 0 = state-retreat direction. Steps occur at movement start years."
        />
      </div>

      {/* Per-channel breakdown — one chart per channel */}
      {orderedChannels.map((channel) => {
        const series = seriesForChannel(channel);
        if (Object.keys(series).length === 0) return null;
        return (
          <section key={channel} className="mb-10">
            <h2 className="mb-3 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
              {channel} axes — what moved and which way
            </h2>
            <div className="mb-3 flex flex-wrap gap-2">
              {(movedAxes[channel] ?? []).map((axis) => (
                <AxisChip key={axis} axisId={axis} axisDef={axesMap[axis]} />
              ))}
            </div>
            <div className="rounded border border-rule bg-white p-5">
              <DriftChart
                series={series}
                years={data.years}
                labels={Object.fromEntries(Object.keys(series).map((s) => [s, s]))}
                height={280}
              />
            </div>
          </section>
        );
      })}

      {/* Movement timeline */}
      <section className="mb-10">
        <h2 className="mb-3 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
          Movement timeline ({country.movement_count})
        </h2>
        <div className="overflow-x-auto rounded border border-rule bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-rule bg-panel">
                <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                  Year
                </th>
                <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                  Movement
                </th>
              </tr>
            </thead>
            <tbody>
              {country.movements.map((m) => (
                <tr key={m.movement_id} className="border-b border-rule last:border-0">
                  <td className="p-3 tabular-nums text-muted">
                    {m.year}
                    {m.end ? `–${m.end}` : ""}
                  </td>
                  <td className="p-3">
                    <Link
                      href={`/m/${m.movement_id}`}
                      className="font-medium text-ink hover:underline"
                    >
                      {m.name}
                    </Link>
                    <div className="font-mono text-[10.5px] text-faint">
                      {m.movement_id}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
