import Link from "next/link";

import {
  loadDrift,
  loadDriftStartingContext,
  countryName,
} from "@/lib/drift";
import { DriftChart } from "@/components/charts/DriftChartLoader";
import { InteractiveDriftChart } from "@/components/charts/InteractiveDriftChartLoader";

export const metadata = {
  title: "Positional drift — movement direction across the coded corpus",
  description:
    "Candidate-coded movement direction by country across the full corpus. Most steps are attributed to movement starts, not policy enactment dates.",
  alternates: { canonical: "https://framework.ieset.org/drift/" },
};

interface RegionSpec {
  id: string;
  label: string;
  countries: string[];
  blurb?: string;
}

/**
 * Hand-curated region panels. A dynamic fallback below keeps new corpus
 * countries visible until their geographic placement has been reviewed.
 */
const REGIONS: RegionSpec[] = [
  {
    id: "liberal_democracies",
    label: "Liberal democracies — North America, Europe, Oceania, Japan, Korea, Israel",
    countries: [
      "USA",
      "GBR",
      "DEU",
      "FRA",
      "ITA",
      "ESP",
      "NLD",
      "BEL",
      "IRL",
      "AUT",
      "PRT",
      "GRC",
      "SWE",
      "NOR",
      "DNK",
      "FIN",
      "CHE",
      "POL",
      "CZE",
      "SVK",
      "HUN",
      "BGR",
      "AUS",
      "NZL",
      "CAN",
      "JPN",
      "KOR",
      "ISR",
    ],
    blurb:
      "The 'managerial flywheel' panel — countries with the most institutional density and longest free-market priors. If the creep hypothesis is universal, this is where it should be most visible.",
  },
  {
    id: "latin_america",
    label: "Latin America",
    countries: [
      "MEX",
      "BRA",
      "ARG",
      "CHL",
      "COL",
      "PER",
      "VEN",
      "BOL",
      "ECU",
      "URY",
      "CUB",
      "SLV",
      "NIC",
      "CRI",
    ],
    blurb:
      "Punctuated by stabilisation episodes, populist swings, and commodity cycles. Drift is non-monotonic by design — the boom-bust pattern is the story.",
  },
  {
    id: "asia",
    label: "Asia-Pacific (non-OECD)",
    countries: [
      "CHN",
      "IND",
      "IDN",
      "VNM",
      "THA",
      "PHL",
      "MYS",
      "PAK",
      "BGD",
      "LKA",
      "KHM",
      "LAO",
      "MMR",
      "AFG",
      "PNG",
      "SGP",
      "TWN",
    ],
    blurb:
      "Most countries here started at high state-share and drifted market-ward via reform episodes (Deng, 1991 India, Doi Moi). Drift index measures direction not level.",
  },
  {
    id: "mena",
    label: "Middle East & North Africa",
    countries: [
      "TUR",
      "IRN",
      "EGY",
      "SAU",
      "ARE",
      "LBN",
      "KWT",
      "DZA",
      "MAR",
      "TUN",
      "IRQ",
      "SYR",
    ],
    blurb:
      "Mixed regime types; Turkey + Iran show fiscal heterodox cycles, Gulf states show state-led developmental architecture, Egypt shows IMF-conditioned austerity moves.",
  },
  {
    id: "africa",
    label: "Sub-Saharan Africa",
    countries: [
      "ZAF",
      "NGA",
      "KEN",
      "GHA",
      "ETH",
      "TZA",
      "RWA",
      "BWA",
      "ZMB",
      "ZWE",
      "AGO",
      "CIV",
      "COD",
      "SEN",
    ],
    blurb:
      "Structural-adjustment-era market moves followed by partial reversals; Ethiopia's Abiy reforms + Nigeria's Tinubu naira+subsidy package + Zimbabwean collapse all show up.",
  },
  {
    id: "post_communist",
    label: "Post-communist transitions + defunct states",
    countries: ["RUS", "SUN", "YUG", "CSK", "ROU", "BLR", "UKR", "KAZ"],
    blurb:
      "Soviet Union and Yugoslavia included as historical priors; Russia + Romania track post-1989 transition trajectories.",
  },
];

const KEY_AXES_FOR_DRIFT: Array<{ axis: string; label: string; caption: string }> = [
  {
    axis: "fiscal.transfer_expansion",
    label: "Transfer expansion",
    caption:
      "Per-country cumulative direction on fiscal.transfer_expansion. + = larger transfer footprint (entitlements, social transfers, pension generosity).",
  },
  {
    axis: "fiscal.spending_level",
    label: "Spending level",
    caption:
      "Per-country cumulative direction on fiscal.spending_level. + = higher spending share of GDP.",
  },
  {
    axis: "fiscal.tax_progressivity",
    label: "Tax progressivity",
    caption:
      "Per-country cumulative direction on fiscal.tax_progressivity. + = more progressive (higher top rates, larger tax-base widening).",
  },
  {
    axis: "regulatory.labour_market_flexibility",
    label: "Labour-market flexibility (inverse — higher line = more rigid)",
    caption:
      "Per-country cumulative direction on regulatory.labour_market_flexibility, inverted so that a rising line means falling flexibility (more dismissal protection, more rigid bargaining).",
  },
];

// Cap the number of trajectories drawn in any one composite chart so the
// chart stays legible. Within a region we pick the top-N by movement_count
// (the most-coded — and therefore best-anchored — entries).
const PER_PANEL_LIMIT = 12;

export default async function DriftPage() {
  const data = await loadDrift();
  if (!data) {
    return (
      <div className="mx-auto max-w-content px-8 py-10">
        <h1>Drift data missing</h1>
        <p>
          Run <code>python3 scripts/compute_country_drift.py</code> first.
        </p>
      </div>
    );
  }
  const driftData = data;
  const contextDataset = await loadDriftStartingContext();
  const startYears = Object.fromEntries(
    Object.entries(data.countries).map(([iso3, c]) => [
      iso3,
      c.first_coded_year,
    ])
  );
  const assignedCountries = new Set(REGIONS.flatMap((r) => r.countries));
  const unassignedCountries = Object.keys(data.countries)
    .filter((iso3) => !assignedCountries.has(iso3))
    .sort();
  const regionSpecs: RegionSpec[] = unassignedCountries.length
    ? [
        ...REGIONS,
        {
          id: "other_countries",
          label: "Other countries in the corpus",
          countries: unassignedCountries,
          blurb:
            "These newly coded countries remain available in the picker and country pages while their regional placement is reviewed.",
        },
      ]
    : REGIONS;

  // For each region, work out which countries are in the corpus + sort by
  // movement_count desc + slice to the per-panel limit.
  function regionEntries(spec: RegionSpec) {
    return spec.countries
      .map((iso3) => {
        const c = driftData.countries[iso3];
        return c ? { iso3, c } : null;
      })
      .filter((x): x is { iso3: string; c: NonNullable<typeof x>["c"] } => !!x)
      .sort((a, b) => b.c.movement_count - a.c.movement_count);
  }

  function compositeSeriesFor(spec: RegionSpec): {
    series: Record<string, number[]>;
    countries: string[];
  } {
    const entries = regionEntries(spec).slice(0, PER_PANEL_LIMIT);
    const series: Record<string, number[]> = {};
    for (const { iso3, c } of entries) series[iso3] = c.statist_drift;
    return { series, countries: entries.map((e) => e.iso3) };
  }

  // Per-axis charts use the most-covered liberal democracies for legibility.
  const liberalSpec = REGIONS[0];
  const liberalCountries = regionEntries(liberalSpec)
    .slice(0, PER_PANEL_LIMIT)
    .map((e) => e.iso3);

  function seriesForAxis(axis: string, invert: boolean = false) {
    const out: Record<string, number[]> = {};
    for (const iso3 of liberalCountries) {
      const traj = driftData.countries[iso3]?.axes[axis];
      if (!traj) continue;
      out[iso3] = invert ? traj.map((v) => -v) : traj;
    }
    return out;
  }

  // Full leaderboard — cumulative direction from all coded movements and
  // attribution change across the latest ten years. Most undated entries are
  // movement-start proxies, not measured annual policy changes.
  const RECENT_WINDOW_YEARS = 10;
  const fullLeaderboard = Object.entries(data.countries)
    .map(([iso3, c]) => {
      const traj = c.statist_drift;
      const final = traj[traj.length - 1] ?? 0;
      const firstYear = startYears[iso3];
      // A full ten-year coverage window is required; recent one-event cases
      // should not be shown as a trend.
      const recent_slope =
        data.year_max - firstYear >= RECENT_WINDOW_YEARS
          ? (traj[traj.length - 1] - traj[traj.length - 1 - RECENT_WINDOW_YEARS]) /
            RECENT_WINDOW_YEARS
          : null;
      return {
        iso3,
        name: countryName(iso3),
        movements: c.movement_count,
        firstYear,
        final,
        recent_slope,
        fiscal_context: contextDataset?.countries[iso3]?.fiscal ?? null,
        fiscal_context_note: contextDataset?.countries[iso3]?.fiscal_note ?? null,
        market_context:
          contextDataset?.countries[iso3]?.market_institutions ?? null,
        market_context_note:
          contextDataset?.countries[iso3]?.market_institutions_note ?? null,
      };
    })
    .sort((a, b) => b.final - a.final);

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-accent-soft px-3 py-1 text-[11px] font-medium uppercase tracking-wider text-accent">
        method note
      </div>
      <h1 className="m-0 mb-3 text-[34px] font-semibold tracking-[-0.02em] md:text-[40px]">
        Positional drift — coded movement direction across history
      </h1>
      <p className="mb-6 max-w-[820px] text-[17px] leading-[1.55] text-muted">
        Movements in the corpus are candidate-coded on the framework axes
        (fiscal/regulatory/monetary/institutional, ±/0/mixed × magnitude).
        Cumulating their directional summaries inside each country produces
        a constructed drift trajectory. The composite statist-drift index sums the pro-state axes
        (spending, transfers, tax progressivity, sectoral subsidy, regulation,
        monetary expansion) minus the pro-market axes (labour-market
        flexibility, product-market competition, trade openness, central-bank
        independence). A higher line means the coding points toward a larger
        or more redistributive state; a lower line points the other way.
      </p>

      <div className="mb-8 rounded border border-rule bg-panel p-5 text-[14px] leading-[1.6] text-muted">
        <strong className="text-ink">How to read the coverage:</strong> the map
        spans every coded movement year, {data.year_min}–{data.year_max}. Each
        country&apos;s line starts at its first coded movement. Numeric zeros
        before that year are unobserved storage placeholders, not evidence
        of policy stability. Most axis directions
        are attributed to the movement&apos;s
        start year as a period-summary proxy, even when the summary mentions
        later acts. Only {data.timing_summary.explicit_axis_year_entries} reviewed
        axis entries use a specific event year. The timing audit flags{" "}
        {data.timing_summary.review_queue_entries} further entries for review,
        including {data.timing_summary.unresolved_later_year_rationale_entries}
        whose rationales mention later years. A mentioned year is not automatically an enactment
        date. These steps are not annual policy effects, absolute policy
        levels, measured outcomes, or verified implementation. Source movement
        records may be candidates rather than confirmed enacted policies.
        The three existing registered drift result cards used earlier
        1976–2025 snapshots; their verdicts await a rerun against this
        refreshed 1846–2026 map.
      </div>

      <p className="mb-8 max-w-[860px] text-[13px] leading-[1.55] text-muted">
        A line&apos;s starting height is its first coded movement, not the
        country&apos;s starting market/state position. Country pages place
        sourced fiscal observations and the World Bank&apos;s perception-based
        Regulatory Quality estimate beside the line. An observation counts as opening context only if it
        falls within five years at or before that country&apos;s first coded
        movement; later measurements are clearly dated as later reference
        points. The fiscal measure is not added to the drift score.
      </p>

      <div className="mb-10 grid grid-cols-2 gap-6 rounded border border-rule bg-white p-5 text-[13.5px] md:grid-cols-4">
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-wider text-muted">
            Countries
          </div>
          <div className="mt-0.5 text-[24px] font-semibold tabular-nums">
            {Object.keys(data.countries).length}
          </div>
        </div>
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-wider text-muted">
            Coded years
          </div>
          <div className="mt-0.5 text-[24px] font-semibold tabular-nums">
            {data.year_min}–{data.year_max}
          </div>
        </div>
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-wider text-muted">
            Axes coded
          </div>
          <div className="mt-0.5 text-[24px] font-semibold tabular-nums">
            {data.axes.length}
          </div>
        </div>
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-wider text-muted">
            Regional panels
          </div>
          <div className="mt-0.5 text-[24px] font-semibold tabular-nums">
            {regionSpecs.length}
          </div>
        </div>
      </div>

      {/* Headline two-column leaderboard — every country, statist vs market */}
      <h2 className="mt-8 mb-3 text-[22px] font-semibold tracking-[-0.01em]">
        All {fullLeaderboard.length} countries — full-corpus coding and recent attribution
      </h2>
      <p className="mb-3 max-w-[860px] text-[14px] text-muted">
        Two numbers per country. <strong className="text-ink">Cumulative</strong>{" "}
        sums its coded movement directions from its first movement through
        {data.year_max}. <strong className="text-ink">
        Recent attribution ({RECENT_WINDOW_YEARS}y)
        </strong>{" "}
        is the average annual change in the coded index over the last{" "}
        {RECENT_WINDOW_YEARS} years when a full window exists. Because most
        steps are movement-start proxies, it is not a policy-enactment rate,
        forecast, or observed outcome.
      </p>
      <div className="mb-5 max-w-[860px] rounded border border-rule bg-panel p-4 text-[13px] leading-[1.55] text-muted">
        <strong className="text-ink">Why these can disagree:</strong> older coded
        shifts remain in the cumulative total even when the last decade moves
        in the other direction. The UK line begins with its 1846 Corn Law
        repeal coding; countries first coded later begin at later dates.
      </div>
      <p className="mb-6 max-w-[900px] text-[13px] leading-[1.55] text-muted">
        <strong className="text-ink">Market/state starting context:</strong>{" "}
        The country rows also show the nearest sourced fiscal footprint and
        World Bank Regulatory Quality estimate available for each first coded
        year. Values within five years before or at that year are marked
        opening; later observations are dated and labelled. These are separate
        reference measures, not a combined market/state score or part of the
        drift line.
      </p>
      <div className="mb-10 grid grid-cols-1 gap-4 md:grid-cols-2">
        {(() => {
          const statist = fullLeaderboard.filter((r) => r.final > 0);
          const market = fullLeaderboard
            .filter((r) => r.final < 0)
            .sort((a, b) => a.final - b.final);
          const stable = fullLeaderboard.filter((r) => r.final === 0);
          return (
            <>
              {(() => {
                // Helper: render a single-column table panel.
                const renderPanel = (
                  rows: typeof fullLeaderboard,
                  headerLabel: string,
                  headerBg: string,
                  headerFg: string,
                  finalIsPositive: boolean
                ) => (
                  <div className="overflow-hidden rounded border border-rule bg-white">
                    <div
                      className="px-4 py-2 text-[11px] font-semibold uppercase tracking-wider"
                      style={{ background: headerBg, color: headerFg }}
                    >
                      {headerLabel} ({rows.length})
                    </div>
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-t border-rule bg-panel">
                          <th className="px-3 py-1 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                            Country
                          </th>
                          <th className="px-3 py-1 text-right text-[10px] font-semibold uppercase tracking-wider text-muted">
                            Cumulative
                          </th>
                          <th className="px-3 py-1 text-right text-[10px] font-semibold uppercase tracking-wider text-muted">
                            Recent attribution ({RECENT_WINDOW_YEARS}y)
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {rows.map((row) => {
                          const recent = row.recent_slope;
                          const recentColor =
                            recent !== null && recent > 0.5
                              ? "text-red"
                              : recent !== null && recent < -0.5
                              ? "text-green"
                              : "text-muted";
                          return (
                            <tr key={row.iso3} className="border-t border-rule">
                              <td className="px-3 py-2 align-top">
                                <Link
                                  href={`/country/${row.iso3}`}
                                  className="font-medium text-ink hover:underline"
                                >
                                  {row.name}
                                </Link>
                                <span className="ml-1.5 font-mono text-[10.5px] text-faint">
                                  {row.iso3}
                                </span>
                                <div className="text-[11px] text-muted">
                                  {row.movements} moves since {row.firstYear}
                                </div>
                                <div className="mt-1 space-y-0.5 text-[10.5px] leading-[1.45] text-faint">
                                  {row.fiscal_context ? (
                                    <div
                                      title={`${row.fiscal_context.label}. ${row.fiscal_context.caveat} Source: ${row.fiscal_context.publisher}.`}
                                    >
                                      Fiscal: {row.fiscal_context.value.toFixed(1)} {row.fiscal_context.unit} · {row.fiscal_context.observed_year}
                                      {row.fiscal_context.relation_to_first_coded_year === "opening" ? " opening" : " later"}
                                    </div>
                                  ) : (
                                    <div title={row.fiscal_context_note ?? undefined}>
                                      Fiscal context unavailable
                                    </div>
                                  )}
                                  {row.market_context ? (
                                    <div
                                      title={`${row.market_context.caveat} Source: ${row.market_context.publisher}.`}
                                    >
                                      Regulatory quality: {row.market_context.value.toFixed(2)} · {row.market_context.observed_year}
                                      {row.market_context.relation_to_first_coded_year === "opening" ? " opening" : " later"}
                                    </div>
                                  ) : (
                                    <div title={row.market_context_note ?? undefined}>
                                      Regulatory quality unavailable
                                    </div>
                                  )}
                                </div>
                              </td>
                              <td
                                className={`px-3 py-2 text-right align-top tabular-nums text-[13.5px] font-semibold ${
                                  finalIsPositive ? "text-red" : "text-green"
                                }`}
                              >
                                {row.final >= 0 ? "+" : ""}
                                {row.final.toFixed(1)}
                              </td>
                              <td
                                className={`px-3 py-2 text-right align-top tabular-nums text-[13px] font-medium ${recentColor}`}
                              >
                                {recent === null ? (
                                  <span title="Less than ten years since the first coded movement">n/a</span>
                                ) : (
                                  <>
                                    {recent >= 0 ? "+" : ""}
                                    {recent.toFixed(2)}
                                    <span className="ml-0.5 text-[10px] text-faint">
                                      /yr
                                    </span>
                                  </>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                );

                return (
                  <>
                    {renderPanel(
                      statist,
                      "Net statist drift",
                      "#f3d9d9",
                      "#9e2f2f",
                      true
                    )}
                    <div>
                      {renderPanel(
                        market,
                        "Net market drift",
                        "#dff1e4",
                        "#2c7a4f",
                        false
                      )}
                      {stable.length > 0 && (
                        <div className="mt-2 rounded border border-rule bg-panel p-2 text-[12px] text-muted">
                          {stable.length} country
                          {stable.length === 1 ? "" : "ies"} at net 0 on the
                          composite axes:{" "}
                          {stable.map((s) => s.iso3).join(", ")}
                        </div>
                      )}
                    </div>
                  </>
                );
              })()}
            </>
          );
        })()}
      </div>

      {/* Interactive country picker — pick any subset of the corpus */}
      <h2 className="mt-12 mb-3 text-[20px] font-semibold tracking-[-0.01em]">
        Pick countries — overlay any combination
      </h2>
      <p className="mb-4 max-w-[820px] text-[14px] text-muted">
        Click ISO3 codes to toggle countries on the chart. Region buttons
        swap to a fixed group in one click. The full corpus begins in{" "}
        {data.year_min}; each selected line starts at that country&apos;s first
        coded movement. Undated axis directions are placed at movement starts;
        only reviewed entries use specific event years.
      </p>
      <div className="mb-12 rounded border border-rule bg-white p-5">
        <InteractiveDriftChart
          allSeries={Object.fromEntries(
            Object.entries(driftData.countries).map(([iso3, c]) => [
              iso3,
              c.statist_drift,
            ])
          )}
          years={data.years}
          startYears={startYears}
          labels={Object.fromEntries(
            Object.keys(driftData.countries).map((iso3) => [iso3, iso3])
          )}
          initialSelection={["DEU", "USA", "GBR", "FRA", "ITA", "CAN", "AUS", "NZL"]}
          height={460}
          zeroLineLabel="cumulative statist drift"
          groups={regionSpecs.map((r) => ({
            id: r.id,
            label: r.label,
            iso3s: r.countries.filter((c) => c in driftData.countries),
          }))}
        />
      </div>

      {/* Region-by-region composite charts */}
      <h2 className="mt-8 mb-3 text-[20px] font-semibold tracking-[-0.01em]">
        Composite statist-drift by region
      </h2>
      <p className="mb-6 max-w-[780px] text-[14px] text-muted">
        One chart per region; up to {PER_PANEL_LIMIT} most-coded countries per
        panel for legibility. The full {Object.keys(data.countries).length}-country
        leaderboard is above; newly coded countries awaiting region assignment
        appear in the final group.
      </p>
      <div className="space-y-8">
        {regionSpecs.map((spec) => {
          const { series, countries } = compositeSeriesFor(spec);
          if (countries.length === 0) return null;
          return (
            <section
              key={spec.id}
              className="rounded border border-rule bg-white p-5"
            >
              <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
                <h3 className="m-0 text-[16px] font-semibold">{spec.label}</h3>
                <span className="text-[11.5px] text-muted">
                  {countries.length} of {spec.countries.length} in the corpus
                </span>
              </div>
              {spec.blurb && (
                <p className="m-0 mb-3 text-[13px] leading-[1.55] text-muted">
                  {spec.blurb}
                </p>
              )}
              <DriftChart
                series={series}
                years={data.years}
                startYears={startYears}
                labels={Object.fromEntries(countries.map((c) => [c, c]))}
                height={spec.id === "liberal_democracies" ? 420 : 320}
                zeroLineLabel="cumulative statist drift"
              />
            </section>
          );
        })}
      </div>

      <h2 className="mt-12 mb-3 text-[20px] font-semibold tracking-[-0.01em]">
        Drift on the four key axes (liberal-democracy panel)
      </h2>
      <p className="mb-6 max-w-[780px] text-[14px] text-muted">
        Each chart isolates one axis so the directional pattern is unambiguous.
        Drawn only for the twelve most-coded countries in the
        liberal-democracy panel so the lines remain legible.
      </p>

      <div className="space-y-8">
        {KEY_AXES_FOR_DRIFT.map((spec) => {
          const invert = spec.axis === "regulatory.labour_market_flexibility";
          const series = seriesForAxis(spec.axis, invert);
          return (
            <section
              key={spec.axis}
              className="rounded border border-rule bg-white p-5"
            >
              <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
                <h3 className="m-0 text-[15px] font-semibold">{spec.label}</h3>
                <Link
                  href={`/a/${spec.axis}`}
                  className="font-mono text-[11px] text-muted hover:text-ink hover:underline"
                >
                  {spec.axis}
                </Link>
              </div>
              <DriftChart
                series={series}
                years={data.years}
                startYears={startYears}
                labels={Object.fromEntries(liberalCountries.map((c) => [c, c]))}
                caption={spec.caption}
                height={320}
              />
            </section>
          );
        })}
      </div>

      <section className="mt-12 rounded border border-rule bg-panel p-6 text-[14px] leading-[1.6]">
        <h3 className="m-0 mb-3 text-[16px] font-semibold">
          Why this matters — the framework&apos;s working hypothesis
        </h3>
        <p className="m-0 mb-3 text-ink">
          A widely-held intuition is that liberal democracies experience{" "}
          <em>positional creep</em> — the median voter, the managerial class,
          and the bureaucracy each have asymmetric incentives to expand state
          activity (more transfers buys votes, more regulation enlarges
          managerial scope, more tax follows the spending). The drift index
          turns that intuition into a measurable, falsifiable pattern: if the
          creep is real, most liberal democracies should show net-positive
          composite drift over multi-decade horizons. If the creep is not
          universal, we should see countries with sustained net-negative drift
          (Mulroney Canada, Greek post-2010 memoranda, Israeli 1985, post-1990
          Sweden tax reform, NZ Rogernomics). Both patterns appear above;
          the registered hypothesis tests determine the verdict.
        </p>
        <p className="m-0 text-muted">
          That next layer lives in the hypothesis library as registered
          tests: the managerial-flywheel claim, the fiscal-rule dampening claim,
          and the initial-state reversion claim. Keeping them separate is
          deliberate: this page describes the coded policy trajectory, while the
          hypothesis pages say exactly what would count as support, partial
          support, or refutation.
        </p>
      </section>
    </div>
  );
}
