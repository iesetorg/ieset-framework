import Link from "next/link";

import { loadDrift, countryName } from "@/lib/drift";
import { loadAllPolicies } from "@/lib/policies";
import { DriftChart } from "@/components/charts/DriftChartLoader";
import { InteractiveDriftChart } from "@/components/charts/InteractiveDriftChartLoader";

export const metadata = {
  title: "Positional drift — how country policy mixes shift across decades",
  description:
    "Movement-coded policy direction by country across the full authored corpus. A constructed cumulative index, with country-specific coverage starts and no measured annual policy level.",
  alternates: { canonical: "https://framework.ieset.org/drift/" },
};

interface RegionSpec {
  id: string;
  label: string;
  countries: string[];
  blurb?: string;
}

/**
 * Curated region panels and picker presets. The picker adds any countries
 * absent from these panels to an automatic "Other countries" group.
 * Within each panel we show the top-N most-coded countries for legibility.
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
  const historicalPolicies = (await loadAllPolicies())
    .filter(
      (policy) =>
        policy.scope === "national" &&
        Number.isInteger(policy.timeframe.start) &&
        policy.timeframe.start < data.year_min &&
        (policy.references?.length ?? 0) > 0
    )
    .sort(
      (a, b) =>
        a.timeframe.start - b.timeframe.start ||
        a.policy_id.localeCompare(b.policy_id)
    );
  const historicalPolicyYears = Array.from(
    new Set(historicalPolicies.map((policy) => policy.timeframe.start))
  );
  const compositeCountryCount = Object.values(driftData.countries).filter(
    (country) => country.composite_first_year !== null
  ).length;

  // Keep every country selectable even as the movement corpus grows. A code
  // listed in more than one curated region appears only in the first picker
  // group; countries outside the curated regions go into a sorted final group.
  const pickerSeen = new Set<string>();
  const pickerGroups = REGIONS.map(({ id, label, countries }) => ({
    id,
    label,
    iso3s: countries.filter((iso3) => {
      if (
        driftData.countries[iso3]?.composite_first_year == null ||
        pickerSeen.has(iso3)
      ) return false;
      pickerSeen.add(iso3);
      return true;
    }),
  }));
  const otherCountries = Object.keys(driftData.countries)
    .filter(
      (iso3) =>
        !pickerSeen.has(iso3) &&
        driftData.countries[iso3].composite_first_year !== null
    )
    .sort();
  if (otherCountries.length > 0) {
    pickerGroups.push({
      id: "other_countries",
      label: "Other countries",
      iso3s: otherCountries,
    });
  }

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
    starts: Record<string, number>;
    countries: string[];
  } {
    const entries = regionEntries(spec)
      .filter(({ c }) => c.composite_first_year !== null)
      .slice(0, PER_PANEL_LIMIT);
    const series: Record<string, number[]> = {};
    const starts: Record<string, number> = {};
    for (const { iso3, c } of entries) {
      series[iso3] = c.statist_drift;
      starts[iso3] = c.composite_first_year!;
    }
    return { series, starts, countries: entries.map((e) => e.iso3) };
  }

  // Per-axis charts use the liberal-democracy panel only (74 lines on one
  // axis chart would be unreadable).
  const liberalSpec = REGIONS[0];
  const liberalCountries = regionEntries(liberalSpec)
    .slice(0, PER_PANEL_LIMIT)
    .map((e) => e.iso3);

  function seriesForAxis(axis: string, invert: boolean = false) {
    const series: Record<string, number[]> = {};
    const starts: Record<string, number> = {};
    for (const iso3 of liberalCountries) {
      const country = driftData.countries[iso3];
      const traj = country?.axes[axis];
      const firstYear = country?.axis_first_year[axis];
      if (!traj || firstYear === undefined) continue;
      series[iso3] = invert ? traj.map((v) => -v) : traj;
      starts[iso3] = firstYear;
    }
    return { series, starts };
  }

  // The leaderboard separates the full coded sum from the slope over the
  // latest decade. A country that enters the corpus during that decade uses
  // only years after its first valenced axis step; a one-year series has no slope.
  const RECENT_WINDOW_YEARS = 10;
  const fullLeaderboard = Object.entries(data.countries)
    .filter(([, c]) => c.composite_first_year !== null)
    .map(([iso3, c]) => {
      const traj = c.statist_drift;
      const final = traj[traj.length - 1] ?? 0;
      const firstCodedYear = c.composite_first_year!;
      const recentStartYear = Math.max(data.year_max - RECENT_WINDOW_YEARS, firstCodedYear);
      const recentStartIndex = recentStartYear - data.year_min;
      const span = data.year_max - recentStartYear;
      const recent_slope = span > 0 ? (final - traj[recentStartIndex]) / span : null;
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
        Positional drift across the movement corpus
      </h1>
      <p className="mb-6 max-w-[820px] text-[17px] leading-[1.55] text-muted">
        Authored movements are coded on directional framework axes. Each
        axis step is placed at the movement start unless a documented policy
        decision year is coded; cumulative lines show the net direction of
        those steps within each country. The
        composite sums pro-state axes and subtracts pro-market axes. Higher
        values indicate more stateward coded movement; lower values indicate
        more marketward coded movement. These are constructed scores, not
        annual observations of legislation, spending, or regulation.
      </p>

      {historicalPolicies.length > 0 && (
        <section className="mb-8 rounded border border-rule bg-white p-5" aria-label="Historical policy context">
          <div className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-accent">
            Earliest cited policy context
          </div>
          <h2 className="m-0 mb-2 text-[20px] font-semibold">
            Policy context begins in {historicalPolicies[0].timeframe.start}; scored drift begins in {data.year_min}
          </h2>
          <p className="mb-4 max-w-[850px] text-[13.5px] leading-[1.55] text-muted">
            These national policy records extend the map&apos;s historical context.
            They are linked below and marked on the main chart as policy-only years.
            The drift score starts with authored movements in {data.year_min};
            no value is assigned to the earlier interval. Each card shows
            its review status. <Link href="/policy-browser/" className="text-accent hover:underline">Browse the policy database</Link>.
          </p>
          <ol className="grid gap-3 md:grid-cols-3">
            {historicalPolicies.map((policy) => (
              <li key={policy.policy_id} className="border-l-2 border-amber-600 bg-panel p-3">
                <div className="font-mono text-[15px] font-semibold tabular-nums">
                  {policy.timeframe.start}
                </div>
                <Link href={`/p/${policy.policy_id}`} className="text-[13px] font-semibold text-accent hover:underline">
                  {policy.title}
                </Link>
                <div className="mt-1 text-[11px] text-muted">
                  policy only · {policy.status} · {policy.countries.map(countryName).join(", ")}
                </div>
              </li>
            ))}
            <li className="border-l-2 border-accent bg-panel p-3">
              <div className="font-mono text-[15px] font-semibold tabular-nums">
                {data.year_min}
              </div>
              <div className="text-[13px] font-semibold">Movement-coded drift begins</div>
              <div className="mt-1 text-[11px] text-muted">First year in the scored movement series</div>
            </li>
          </ol>
        </section>
      )}

      <div className="mb-8 rounded border border-rule bg-panel p-5 text-[14px] leading-[1.6] text-muted">
        <strong className="text-ink">Coverage:</strong> scored movement years span the
        earliest to latest authored movement ({data.year_min}–{data.year_max}).
        Each composite line begins at its first valenced axis step; earlier
        movements without one do not establish a composite score. Earlier
        blank space is missing coding coverage, not a zero policy level.
        A flat segment means no further <em>coded</em> shift in that interval.
        The index measures direction, not absolute policy levels, and countries
        do not share a measured {data.year_min} baseline. State and municipal
        and EU-wide movements are excluded from country totals. EU-wide
        records remain in the movement corpus and the atlas; their member
        applicability, decision dates, and overlapping policy stacks need
        review before they can be shown as a separate EU layer here. Some
        national umbrella and term records also have overlapping policy links
        under source review; their country totals may change as duplicated
        steps are resolved.
      </div>

      <p className="mb-8 max-w-[860px] text-[13px] leading-[1.55] text-muted">
        The three historical drift result cards are legacy same-commit records
        from the previous 1976–2025 constructed series. They are marked
        <strong className="text-ink"> needs rerun</strong> against this longer
        corpus; the extended chart does not update their verdicts.
      </p>

      <div className="mb-10 grid grid-cols-2 gap-6 rounded border border-rule bg-white p-5 text-[13.5px] md:grid-cols-4">
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-wider text-muted">
            Countries with movements
          </div>
          <div className="mt-0.5 text-[24px] font-semibold tabular-nums">
            {Object.keys(data.countries).length}
          </div>
        </div>
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-wider text-muted">
            Movement years
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
            Composite-coded countries
          </div>
          <div className="mt-0.5 text-[24px] font-semibold tabular-nums">
            {compositeCountryCount}
          </div>
        </div>
      </div>

      {/* Headline two-column leaderboard — every country, statist vs market */}
      <h2 className="mt-8 mb-3 text-[22px] font-semibold tracking-[-0.01em]">
        All {fullLeaderboard.length} composite-coded countries — cumulative direction & recent slope
      </h2>
      <p className="mb-3 max-w-[860px] text-[14px] text-muted">
        Two numbers per country. <strong className="text-ink">Cumulative</strong>{" "}
        is the sum of valenced axis steps since each country&apos;s first
        such step. <strong className="text-ink">
        Recent (up to {RECENT_WINDOW_YEARS}y)
        </strong>{" "}
        is the average annual change in that constructed score over at most
        the last {RECENT_WINDOW_YEARS} years. A blank means fewer than two
        covered years.
      </p>
      <div className="mb-5 max-w-[860px] rounded border border-rule bg-panel p-4 text-[13px] leading-[1.55] text-muted">
        <strong className="text-ink">Reading the columns:</strong> an older
        coded step remains in the cumulative sum, while newer coded steps can
        change its recent direction. A flat recent score means no net new
        coded shift in the window; it does not establish policy stasis.
        Scores depend on which movements have been authored and their axis
        weights, so compare coverage before comparing countries.
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
                            Recent (up to {RECENT_WINDOW_YEARS}y)
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
                                {recent === null ? (
                                  "—"
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
                          {stable.length === 1 ? "" : "ies"} with net zero
                          valenced axis score (possibly offsetting steps):{" "}
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
        Click ISO3 codes to toggle countries with a scored composite. Region
        buttons swap to a fixed regional set in one click. Each line begins
        with that country&apos;s first valenced axis step; countries with only
        unscored movement records remain in the country atlas.
      </p>
      <div className="mb-12 rounded border border-rule bg-white p-5">
        <InteractiveDriftChart
          allSeries={Object.fromEntries(
            Object.entries(driftData.countries)
              .filter(([, c]) => c.composite_first_year !== null)
              .map(([iso3, c]) => [iso3, c.statist_drift])
          )}
          years={data.years}
          historicalPolicyYears={historicalPolicyYears}
          caption={historicalPolicyYears.length > 0
            ? `Dashed markers show cited policy-only years before ${data.year_min}. No country line or drift value is plotted for those years.`
            : undefined}
          seriesStarts={Object.fromEntries(
            Object.entries(driftData.countries)
              .filter(([, c]) => c.composite_first_year !== null)
              .map(([iso3, c]) => [iso3, c.composite_first_year!])
          )}
          labels={Object.fromEntries(
            Object.keys(driftData.countries)
              .filter((iso3) => driftData.countries[iso3].composite_first_year !== null)
              .map((iso3) => [iso3, iso3])
          )}
          initialSelection={["DEU", "USA", "GBR", "FRA", "ITA", "CAN", "AUS", "NZL"]}
          height={460}
          zeroLineLabel="cumulative statist drift"
          groups={pickerGroups}
        />
      </div>

      {/* Region-by-region composite charts */}
      <h2 className="mt-8 mb-3 text-[20px] font-semibold tracking-[-0.01em]">
        Composite statist-drift by region
      </h2>
      <p className="mb-6 max-w-[780px] text-[14px] text-muted">
        One chart per region; up to {PER_PANEL_LIMIT} countries with a coded
        composite per panel for legibility. The full {fullLeaderboard.length}-country
        composite leaderboard appears above.
      </p>
      <div className="space-y-8">
        {REGIONS.map((spec) => {
          const { series, starts, countries } = compositeSeriesFor(spec);
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
                seriesStarts={starts}
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
          const { series, starts } = seriesForAxis(spec.axis, invert);
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
                seriesStarts={starts}
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
