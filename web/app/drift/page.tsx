import Link from "next/link";

import { loadDrift, countryName } from "@/lib/drift";
import { DriftChart } from "@/components/charts/DriftChartLoader";
import { InteractiveDriftChart } from "@/components/charts/InteractiveDriftChartLoader";

export const metadata = {
  title: "Positional drift — how country policy mixes shift across decades",
  description:
    "Statist drift index per country. The framework codes every government's axes_summary; cumulating across the corpus shows how each country has drifted toward more state or more market, year by year.",
};

interface RegionSpec {
  id: string;
  label: string;
  countries: string[];
  blurb?: string;
}

/**
 * Region panels — every country in the drift dataset belongs to exactly one
 * panel. Within each panel we show the top-N most-coded countries to keep the
 * chart legible.
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

  // Per-axis charts use the liberal-democracy panel only (74 lines on one
  // axis chart would be unreadable).
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

  // Full leaderboard — every country in the corpus, with cumulative drift
  // since corpus start AND the slope over the most recent decade. Without
  // the recent-decade column the table is misleading: countries like Canada
  // look like 'market drift' purely because Mulroney + Chretien's 1984-2006
  // deficit slaying dwarfs Trudeau Jr's recent statist moves in the cumulative
  // sum. The recent-slope column shows the direction the country is *currently*
  // moving, which often tells the opposite story.
  const RECENT_WINDOW_YEARS = 10;
  const fullLeaderboard = Object.entries(data.countries)
    .map(([iso3, c]) => {
      const traj = c.statist_drift;
      const final = traj[traj.length - 1] ?? 0;
      // Slope over the last RECENT_WINDOW_YEARS years (≈ per-year rate).
      const window = Math.min(RECENT_WINDOW_YEARS, traj.length - 1);
      const recent_slope =
        window > 0 ? (traj[traj.length - 1] - traj[traj.length - 1 - window]) / window : 0;
      return {
        iso3,
        name: countryName(iso3),
        movements: c.movement_count,
        final,
        recent_slope,
      };
    })
    .sort((a, b) => b.final - a.final);

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-accent-soft px-3 py-1 text-[11px] font-medium uppercase tracking-wider text-accent">
        method note
      </div>
      <h1 className="m-0 mb-3 text-[34px] font-semibold tracking-[-0.02em] md:text-[40px]">
        Positional drift — has the policy mix moved toward more state, year by year?
      </h1>
      <p className="mb-6 max-w-[820px] text-[17px] leading-[1.55] text-muted">
        Every government in the corpus is coded on the framework axes
        (fiscal/regulatory/monetary/institutional, ±/0/mixed × magnitude).
        Cumulating those moves over time inside each country produces a drift
        trajectory — whether the policy mix has expanded the state or pulled
        back from it. The composite statist-drift index sums the pro-state axes
        (spending, transfers, tax progressivity, sectoral subsidy, regulation,
        monetary expansion) minus the pro-market axes (labour-market
        flexibility, product-market competition, trade openness, central-bank
        independence). A higher line means the country has shifted toward a
        larger or more redistributive state since the corpus&apos;s start; a lower
        line means it has shifted away.
      </p>

      <div className="mb-8 rounded border border-rule bg-panel p-5 text-[14px] leading-[1.6] text-muted">
        <strong className="text-ink">Important:</strong> this measures the{" "}
        <em>direction</em> of policy moves over time, not the absolute level.
        Greece and Italy show negative drift partly because the EU memoranda
        forced sustained austerity and privatisations — they moved toward
        market-orthodox policy from a much higher starting level. Conversely,
        Germany&apos;s strongly positive drift reflects Energiewende, Bürgergeld,
        Sondervermögen, and the post-2019 spending wave — choices made from a
        relatively constrained baseline. Read each line as &quot;net direction
        of legislated policy since {data.year_min}.&quot;
      </div>

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
            Year range
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
            {REGIONS.length}
          </div>
        </div>
      </div>

      {/* Headline two-column leaderboard — every country, statist vs market */}
      <h2 className="mt-8 mb-3 text-[22px] font-semibold tracking-[-0.01em]">
        All {fullLeaderboard.length} countries — cumulative direction & recent slope
      </h2>
      <p className="mb-3 max-w-[860px] text-[14px] text-muted">
        Two numbers per country. <strong className="text-ink">Cumulative</strong>{" "}
        is the legislated drift since {data.year_min} — the sum of every
        movement&apos;s axes_summary moves up to today. <strong className="text-ink">
        Recent ({RECENT_WINDOW_YEARS}y)
        </strong>{" "}
        is the slope over the last {RECENT_WINDOW_YEARS} years — what direction
        the country is moving <em>now</em>.
      </p>
      <div className="mb-5 max-w-[860px] rounded border border-rule bg-panel p-4 text-[13px] leading-[1.55] text-muted">
        <strong className="text-ink">Why these can disagree:</strong> Canada
        sits near the top of the &quot;cumulative market drift&quot; column at
        −39, but its <em>recent</em> slope is +0.10/yr — i.e., mildly statist.
        That&apos;s because Mulroney + Chrétien-Martin&apos;s 1984–2006 deficit
        slaying (GST 1991, NAFTA 1994, the canonical Paul Martin 1995 budget)
        was the largest fiscal consolidation in modern OECD history; Trudeau
        Jr&apos;s 2015–2025 statist moves haven&apos;t been large enough to
        offset it cumulatively. Same pattern for the UK (cumulative −2,
        recent +3.2/yr — Brexit-era fiscal expansion + Truss + Starmer all
        statist), Australia (cumulative −15, recent +1.9/yr — Albanese), and
        New Zealand (cumulative −28, recent +0.4/yr — Ardern net statist
        before Luxon partial reversal). The cumulative column tells you{" "}
        <em>where the country sits</em> relative to its {data.year_min} baseline; the
        recent column tells you <em>where it&apos;s headed</em>.
      </div>
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
                            Recent ({RECENT_WINDOW_YEARS}y)
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {rows.map((row) => {
                          const recent = row.recent_slope;
                          const recentColor =
                            recent > 0.5
                              ? "text-red"
                              : recent < -0.5
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
                                  {row.movements} moves
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
                                {recent >= 0 ? "+" : ""}
                                {recent.toFixed(2)}
                                <span className="ml-0.5 text-[10px] text-faint">
                                  /yr
                                </span>
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
                          {stable.length === 1 ? "" : "ies"} at 0 (no axes_summary
                          moves coded yet):{" "}
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
        swap to a fixed regional set in one click. Each line is the country&apos;s
        cumulative composite drift from {data.year_min}.
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
          labels={Object.fromEntries(
            Object.keys(driftData.countries).map((iso3) => [iso3, iso3])
          )}
          initialSelection={["DEU", "USA", "GBR", "FRA", "ITA", "CAN", "AUS", "NZL"]}
          height={460}
          zeroLineLabel="cumulative statist drift"
          groups={REGIONS.map((r) => ({
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
        leaderboard sits below.
      </p>
      <div className="space-y-8">
        {REGIONS.map((spec) => {
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
        Drawn only for the liberal-democracy panel because 74 lines on one
        axis chart would be unreadable.
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
          Sweden tax-reform-of-the-century, NZ Rogernomics). Both patterns
          appear above — neither view wins by inspection alone.
        </p>
        <p className="m-0 text-muted">
          That next layer lives in the hypothesis library as pre-registered
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
