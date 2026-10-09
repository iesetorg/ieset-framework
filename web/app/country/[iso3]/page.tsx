import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";

import {
  loadDrift,
  loadDriftStartingContext,
  countryName,
  type DriftContextObservation,
} from "@/lib/drift";
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
    description: `Cumulative movement-direction coding for ${name}. Most steps are movement-start attributions, not enactment dates.`,
    alternates: {
      canonical: `https://framework.ieset.org/country/${encodeURIComponent(
        iso3
      )}/`,
    },
  };
}

const CHANNEL_ORDER = ["fiscal", "regulatory", "monetary", "institutional"];

function shortMovementLabel(name: string) {
  const label = name.split("—", 1)[0].replace(/\s*\([^)]*\)\s*$/g, "").trim();
  if (!label) return name;
  return label.length > 24 ? `${label.slice(0, 23)}…` : label;
}

function ContextMeasure({
  heading,
  observation,
  firstYear,
  openingWindow,
  unavailableReason,
  unavailableSourceUrl,
}: {
  heading: string;
  observation: DriftContextObservation | null;
  firstYear: number;
  openingWindow: number;
  unavailableReason?: string;
  unavailableSourceUrl?: string;
}) {
  if (!observation) {
    return (
      <div className="rounded border border-rule bg-white p-4">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">{heading}</div>
        <p className="mt-2 mb-0 text-[13px] text-muted">
          {unavailableReason ?? "No observation in the pinned source."}
          {unavailableSourceUrl && (
            <> <a href={unavailableSourceUrl} className="text-accent hover:underline">View source directly</a>.</>
          )}
        </p>
      </div>
    );
  }
  const isOpening = observation.relation_to_first_coded_year === "opening";
  const snapshot = observation.vintage_file.match(/@(\d{4}-\d{2}-\d{2})/)?.[1];
  return (
    <div className="rounded border border-rule bg-white p-4">
      <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">{heading}</div>
      <div className="mt-2 text-[22px] font-semibold tabular-nums text-ink">
        {observation.value.toFixed(1)} <span className="text-[13px] font-normal text-muted">{observation.unit}</span>
      </div>
      <div className="mt-1 text-[12px] font-medium text-ink">
        {isOpening
          ? `Opening observation · ${observation.observed_year}`
          : `Later observation only · ${observation.observed_year}`}
      </div>
      <p className="mt-2 mb-2 text-[12px] leading-[1.5] text-muted">
        {isOpening
          ? `Measured within ${openingWindow} years before the first coded movement (${firstYear}).`
          : `Measured ${observation.observed_year - firstYear} years after coding began in ${firstYear}; it cannot describe the opening level.`}{" "}
        {observation.caveat}
      </p>
      <div className="text-[11px] leading-[1.5] text-muted">
        <a href={observation.source_url} className="text-accent hover:underline">{observation.publisher}: {observation.label}</a>
        {snapshot ? ` · source snapshot ${snapshot}` : ""}
        {" · "}<a href={observation.definition_url} className="text-accent hover:underline">definition</a>
        {" · "}<a href={observation.license_url} className="text-accent hover:underline">{observation.license}</a>
        {" · "}values rounded for display
        <span title={`${observation.vintage_file} · SHA-256 ${observation.vintage_sha256}`}>
          {" · "}pinned vintage
        </span>
      </div>
    </div>
  );
}

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
  const firstMovementYear = country.first_coded_year;
  const contextDataset = await loadDriftStartingContext();
  const contextRow = contextDataset?.countries[iso3];
  const startingContext =
    contextRow?.first_coded_year === firstMovementYear ? contextRow : undefined;
  const contextNeedsRefresh = Boolean(contextRow && !startingContext);

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

      <p className="mb-5 max-w-[820px] text-[13px] leading-[1.55] text-muted">
        This country&apos;s line begins with its first coded movement in{" "}
        {firstMovementYear}. Earlier numeric zeros are unobserved placeholders
        outside its coded coverage.
        Most axis summaries are placed at the movement&apos;s start as a period
        proxy. Some summarize policies adopted years later; only reviewed
        entries with an explicit attribution year are placed at that event.
        This index is neither an annual enactment timeline nor a measured
        policy level or implementation outcome.
        Existing registered drift verdicts used older 1976–2025 snapshots and
        await a rerun against this refreshed map.
      </p>

      <section className="mb-10 rounded border border-rule bg-panel p-5">
        <h2 className="m-0 mb-2 text-[17px] font-semibold text-ink">
          Market and state: opening context and later data
        </h2>
        <p className="mb-4 max-w-[820px] text-[13px] leading-[1.55] text-muted">
          The drift line shows the direction of coded movements from {firstMovementYear},
          not the country&apos;s policy level. The fiscal measure and
          perception-based regulatory-quality estimate below remain separate from that line. Only a
          measurement from {firstMovementYear - (contextDataset?.opening_window_years ?? 5)}–{firstMovementYear}
          is called an opening observation; later data is labelled separately.
        </p>
        <div className="grid gap-3 md:grid-cols-2">
          <ContextMeasure
            heading="Fiscal footprint"
            observation={startingContext?.fiscal ?? null}
            firstYear={firstMovementYear}
            openingWindow={contextDataset?.opening_window_years ?? 5}
            unavailableReason={contextNeedsRefresh ? "Context is being refreshed after the first coded year changed." : undefined}
          />
          <ContextMeasure
            heading="Private-sector regulatory quality"
            observation={startingContext?.market_institutions ?? null}
            firstYear={firstMovementYear}
            openingWindow={contextDataset?.opening_window_years ?? 5}
            unavailableReason={contextNeedsRefresh ? "Context is being refreshed after the first coded year changed." : startingContext?.market_institutions_note}
            unavailableSourceUrl={contextNeedsRefresh ? undefined : startingContext?.market_institutions_source_url}
          />
        </div>
        {startingContext?.historical_context && (
          <div className="mt-3 rounded border border-rule bg-white p-4 text-[13px] leading-[1.55] text-muted">
            <strong className="text-ink">Documented {startingContext.historical_context.as_of_year} context:</strong>{" "}
            {startingContext.historical_context.summary}
            <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px]">
              {startingContext.historical_context.sources.map((source) => (
                <a key={source.url} href={source.url} className="text-accent hover:underline">
                  {source.label}
                </a>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Composite trajectory with movement annotations */}
      <div className="mb-3 flex flex-wrap items-center gap-3 text-[11.5px] text-muted">
        <span className="font-semibold uppercase tracking-wider">coded movement direction</span>
        <span className="inline-flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: "#9e2f2f" }} />
          net stateward
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: "#2c7a4f" }} />
          net marketward
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: "#b7791f" }} />
          mixed or near zero
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: "#636363" }} />
          authoritarian regime
        </span>
      </div>
      <div className="mb-10 rounded border border-rule bg-white p-5">
        <h2 className="m-0 mb-3 text-[16px] font-semibold">
          Composite movement-direction trajectory
        </h2>
        <DriftChart
          series={compositeSeries}
          years={data.years}
          startYears={{ [iso3]: firstMovementYear }}
          labels={{ [iso3]: countryName(iso3) }}
          movements={country.movements.map((m) => ({
            country: iso3,
            year: m.year,
            label: m.leader_label || shortMovementLabel(m.name),
            tone: m.tone ?? "neutral",
          }))}
          height={300}
          zeroLineLabel="cumulative statist drift"
          caption="Cumulative candidate-coded direction across the valenced axes. Most steps are movement-start period proxies; reviewed event-year exceptions are listed below. A step is not an observed policy effect."
        />
      </div>

      {country.explicit_axis_timing.length > 0 && (
        <section className="mb-10">
          <h2 className="mb-3 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Reviewed timing exceptions ({country.explicit_axis_timing.length})
          </h2>
          <p className="mb-3 max-w-[820px] text-[13px] leading-[1.55] text-muted">
            These coded directions are attributed to documented decisions or
            policy events after the movement began. Their years do not measure
            when economic outcomes changed.
          </p>
          <div className="overflow-x-auto rounded border border-rule bg-white">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-rule bg-panel">
                  <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">Year</th>
                  <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">Axis</th>
                  <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">Attribution basis</th>
                </tr>
              </thead>
              <tbody>
                {country.explicit_axis_timing.map((event) => (
                  <tr key={`${event.movement_id}-${event.axis}`} className="border-b border-rule last:border-0">
                    <td className="p-3 align-top tabular-nums text-muted">{event.attribution_year}</td>
                    <td className="p-3 align-top font-mono text-xs text-ink">{event.axis}</td>
                    <td className="p-3 align-top text-muted">{event.basis}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

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
                startYears={Object.fromEntries(
                  Object.keys(series).map((axis) => [axis, firstMovementYear])
                )}
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
