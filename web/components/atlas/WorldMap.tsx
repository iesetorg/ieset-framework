"use client";

import { useMemo, useState } from "react";
import { historicalEventsAtYear, isNationalPrimary, countryMatchesHistorySearch, normalizeHistorySearch, constitutionalLayerBounds,
  type AtlasCoverage, type AtlasPolicyRecord, type ConstitutionalHistory, type CountryHistoricalContext } from "@/lib/atlas-history";
import {
  governmentNeedsCoding,
  indexAtlasMovements,
  RESULT_LABELS,
  GOVERNMENT_LABELS,
  type ElectionReview,
} from "@/lib/atlas-elections";

import {
  CLUSTERS,
  EMPTY_COLOR,
  MIXED_COLOR,
  NONE_COLOR,
  colorForCluster,
  type ClusterId,
} from "@/lib/position-clusters";

export interface AtlasMovement {
  movement_id: string;
  name: string;
  countries: string[];
  start: number;
  end: number; // "ongoing" → currentYear
  cluster: ClusterId;
  cluster_score: number;
  policy_coding_ready?: boolean;
  /** "subnational" movements (state, province, municipal) are excluded from
   *  country-level cluster computation but still listed in the country
   *  hover panel. Default omitted = national. */
  scope?: "national" | "subnational" | "supranational";
  country_drift_role?: "primary" | "context_only";
}

export interface CountryPath {
  id: string;
  iso3: string | null;
  name: string;
  d: string;
}

const W = 960;
const H = 520;

// Per-movement weight by scope:
//   national      → 1.00 (a country's government is the primary signal)
//   supranational → 0.10 (EU regs etc. apply across many members; they
//                          should nudge each member's colour, not dominate
//                          it. A typical EU member-state has ~4 EU regs
//                          active simultaneously (GDPR, REACH, Green Deal,
//                          CSRD), so even at 0.10× the combined nudge can
//                          reach ~0.5, which tilts close cases without
//                          overriding a clear national signal.)
//   subnational   → 0.00 (state climate regimes etc. don't speak for the
//                          country and are excluded from the country-level
//                          cluster computation; still listed in the hover)
function scopeWeight(scope: AtlasMovement["scope"]): number {
  if (scope === "subnational") return 0;
  if (scope === "supranational") return 0.1;
  return 1.0;
}

// Pick the cluster with the highest aggregate score across active movements
// in a country. Returns "none" when no movement has any aligned positions,
// and "mixed" when two clusters tie within a small margin.
function dominantCluster(
  movements: AtlasMovement[]
): { cluster: ClusterId; bd: { cluster: ClusterId; score: number; n: number }[] } {
  if (movements.length === 0) return { cluster: "none", bd: [] };
  const scores = new Map<ClusterId, { score: number; n: number }>();
  for (const m of movements) {
    if (m.cluster === "none") continue;
    const w = scopeWeight(m.scope);
    if (w === 0) continue;
    const cur = scores.get(m.cluster) ?? { score: 0, n: 0 };
    cur.score += m.cluster_score * w;
    cur.n += 1;
    scores.set(m.cluster, cur);
  }
  if (scores.size === 0) return { cluster: "none", bd: [] };
  const ranked = [...scores.entries()]
    .map(([cluster, v]) => ({ cluster, score: v.score, n: v.n }))
    .sort((a, b) => b.score - a.score);
  const top = ranked[0];
  const second = ranked[1];
  // tie-break: top must beat second by at least 0.5 (one half-aligned movement) to claim the country
  if (second && top.score - second.score < 0.5) {
    return { cluster: "mixed", bd: ranked };
  }
  return { cluster: top.cluster, bd: ranked };
}

export function WorldMap({
  movements,
  paths,
  yearMin,
  yearMax,
  electionReviews,
  asOf,
  coverage,
  policies,
  constitutionalHistory,
  historicalSupplements,
}: {
  movements: AtlasMovement[];
  paths: CountryPath[];
  yearMin: number;
  yearMax: number;
  electionReviews: ElectionReview[];
  asOf: string;
  coverage: AtlasCoverage[];
  policies: AtlasPolicyRecord[];
  constitutionalHistory: ConstitutionalHistory | null;
  historicalSupplements: CountryHistoricalContext[];
}) {
  const [year, setYear] = useState(yearMax);
  const [query, setQuery] = useState("");
  const [layer, setLayer] = useState<"movements" | "constitutional">("movements");
  const [countryQuery, setCountryQuery] = useState("");
  const [earlierQuery, setEarlierQuery] = useState("");
  const [countryLimit, setCountryLimit] = useState(40);
  const [selectedHistoryCountry, setSelectedHistoryCountry] = useState<string | null>(null);
  const [policyLimit, setPolicyLimit] = useState(20);
  const [eventLimit, setEventLimit] = useState(20);
  const [movementLimit, setMovementLimit] = useState(20);
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);
  const [hover, setHover] = useState<{
    iso3: string;
    name: string;
    x: number;
    y: number;
  } | null>(null);

  const historyByCountry = useMemo(() => new Map(
    (constitutionalHistory?.countries ?? []).map(country => [country.iso3, country])
  ), [constitutionalHistory]);
  const supplementsByCountry = useMemo(() => {
    const rows = new Map<string, CountryHistoricalContext[]>();
    for (const supplement of historicalSupplements) rows.set(supplement.iso3, [...(rows.get(supplement.iso3) ?? []), supplement]);
    return rows;
  }, [historicalSupplements]);
  const contextAtYear = useMemo(() => {
    const events = new Map<string, ReturnType<typeof historicalEventsAtYear>>();
    for (const context of [...(constitutionalHistory?.countries ?? []), ...historicalSupplements]) {
      const matching = historicalEventsAtYear(context, year);
      if (matching.length) events.set(context.iso3, [...(events.get(context.iso3) ?? []), ...matching]);
    }
    return events;
  }, [constitutionalHistory, historicalSupplements, year]);
  const visibleCountries = useMemo(() => coverage.filter(country =>
    countryMatchesHistorySearch(country, historyByCountry.get(country.iso3), countryQuery)
      || (supplementsByCountry.get(country.iso3) ?? []).some(context => countryMatchesHistorySearch(country, context, countryQuery))
  ), [coverage, countryQuery, historyByCountry, supplementsByCountry]);
  const historicalCoverageSummary = useMemo(() => {
    const rows = (constitutionalHistory?.countries ?? []).filter(country => country.events.length > 0);
    const supplementRows = historicalSupplements.filter(country => country.events.length > 0);
    const years = [...rows, ...supplementRows].flatMap(country => country.events.map(event => event.start_year));
    return { countries: rows.length, supplementCountries: new Set(supplementRows.map(row => row.iso3)).size,
      earliest: years.length ? Math.min(...years) : null };
  }, [constitutionalHistory, historicalSupplements]);
  const earlierPolities = useMemo(() => (constitutionalHistory?.historical_entities ?? []).filter(entity =>
    normalizeHistorySearch([entity.source_country, ...entity.source_country_names].join(" "))
      .includes(normalizeHistorySearch(earlierQuery.trim())))
    .sort((a, b) => a.source_country.localeCompare(b.source_country)), [constitutionalHistory, earlierQuery]);
  const selectedCoverage = coverage.find(country => country.iso3 === selectedHistoryCountry);
  const selectedContext = selectedHistoryCountry ? historyByCountry.get(selectedHistoryCountry) : undefined;
  const selectedSupplements = useMemo(() => selectedHistoryCountry ? supplementsByCountry.get(selectedHistoryCountry) ?? [] : [],
    [supplementsByCountry, selectedHistoryCountry]);
  const selectedPolicies = useMemo(() => policies.filter(policy => policy.countries.includes(selectedHistoryCountry ?? "")
    && (policy.scope ?? "national") === "national")
    .sort((a, b) => a.year - b.year || a.title.localeCompare(b.title)), [policies, selectedHistoryCountry]);
  const selectedMovements = useMemo(() => movements.filter(movement => movement.countries.includes(selectedHistoryCountry ?? "")
    && isNationalPrimary(movement)).sort((a, b) => a.start - b.start || a.name.localeCompare(b.name)), [movements, selectedHistoryCountry]);
  const selectedEvents = useMemo(() => [
    ...(selectedContext?.events ?? []).map(event => ({ ...event, sourceKind: "CCP source event" })),
    ...selectedSupplements.flatMap(context => context.events.map(event => ({ ...event, sourceKind: "Primary-source supplement" }))),
  ].sort((a, b) => a.start_year - b.start_year || a.id.localeCompare(b.id)), [selectedContext, selectedSupplements]);
  const geometryCountries = useMemo(() => new Set(paths.map(path => path.iso3).filter(Boolean)), [paths]);
  const contextLayer = layer === "constitutional";
  const contextBounds = constitutionalLayerBounds(constitutionalHistory, historicalSupplements, yearMax);
  const sliderMin = contextLayer ? contextBounds.start : yearMin;
  const sliderMax = contextLayer ? contextBounds.end : yearMax;

  function changeLayer(next: "movements" | "constitutional") {
    setLayer(next);
    const min = next === "constitutional" ? contextBounds.start : yearMin;
    const max = next === "constitutional" ? contextBounds.end : yearMax;
    setYear(current => Math.max(min, Math.min(max, current)));
  }
  function openCountryHistory(iso3: string) {
    setSelectedHistoryCountry(iso3);
    setPolicyLimit(20); setEventLimit(20); setMovementLimit(20); setHover(null);
    requestAnimationFrame(() => {
      document.getElementById("atlas-history-detail")?.scrollIntoView({ behavior: "smooth", block: "start" });
      document.getElementById("atlas-history-country-heading")?.focus({ preventScroll: true });
    });
  }

  // Movements active at the slider year, indexed by ISO3.
  const activeByCountry = useMemo(
    () => indexAtlasMovements(movements, electionReviews, year, asOf),
    [movements, electionReviews, year, asOf]
  );
  const reviewsByCountry = useMemo(
    () => new Map(electionReviews.map(review => [review.iso3, review])),
    [electionReviews]
  );
  const uncodedGovernments = useMemo(() => new Set(electionReviews
    .filter(review => governmentNeedsCoding(review, activeByCountry.get(review.iso3) ?? [], year, asOf))
    .map(review => review.iso3)), [electionReviews, activeByCountry, year, asOf]);
  const visibleReviews = useMemo(() => {
    const search = query.trim().toLocaleLowerCase();
    return electionReviews.filter(review => [review.country, review.iso3, review.election_type,
      review.result_summary, review.government_summary].join(" ").toLocaleLowerCase().includes(search));
  }, [electionReviews, query]);
  const checkedDates = [...new Set(electionReviews.map(review => review.checked_on))].sort();
  const reviewDateLabel = checkedDates.length === 1 ? checkedDates[0]
    : checkedDates.length ? `${checkedDates[0]}–${checkedDates[checkedDates.length - 1]}` : null;

  function openCountryReview(iso3: string) {
    const review = reviewsByCountry.get(iso3);
    if (!review) return;
    setQuery(review.country);
    setSelectedCountry(iso3);
    setHover(null);
    document.getElementById("atlas-election-results")?.scrollIntoView({ behavior: "smooth", block: "start" });
    requestAnimationFrame(() => document.getElementById(`atlas-election-${iso3}`)?.focus({ preventScroll: true }));
  }

  const clusterByCountry = useMemo(() => {
    const out = new Map<
      string,
      { cluster: ClusterId; bd: { cluster: ClusterId; score: number; n: number }[] }
    >();
    for (const [iso3, list] of activeByCountry) {
      // dominantCluster applies per-scope weights:
      //   national=1.0, supranational=0.1, subnational=0.0
      // EU regs still tilt member-state colour; they just don't drown out
      // the national government signal. Subnational policies are skipped.
      out.set(iso3, dominantCluster(list));
    }
    // A reviewed new government has no inherited ideology colour while its
    // own policy movement or its referenced policy records are still missing.
    for (const iso3 of uncodedGovernments) out.set(iso3, { cluster: "none", bd: [] });
    return out;
  }, [activeByCountry, uncodedGovernments]);

  const totalActive = activeByCountry.size;
  const totalMovements = useMemo(() => {
    const set = new Set<string>();
    for (const list of activeByCountry.values())
      for (const m of list) set.add(m.movement_id);
    return set.size;
  }, [activeByCountry]);

  const clusterCounts = useMemo(() => {
    const counts: Partial<Record<ClusterId, number>> = {};
    for (const r of clusterByCountry.values()) {
      counts[r.cluster] = (counts[r.cluster] ?? 0) + 1;
    }
    return counts;
  }, [clusterByCountry]);

  return (
    <div className="relative">
      <div className="mb-4 rounded border border-rule bg-panel px-4 py-3 text-[13px] leading-relaxed">
        {reviewDateLabel ? <>
          <strong>{electionReviews.length} countries reviewed · checked {reviewDateLabel}</strong>
          <p className="mt-1 text-muted">This is a dated, selective review, not worldwide verification.
            In the current-year view, verified handovers or retirement dates hide explicitly superseded movements.
            Earlier years retain annual coverage, including governments that changed during the year.</p>
          <a href="#atlas-election-results" className="mt-1 inline-block underline">Read election results and sources</a>
        </> : <p>No election reviews are available. The map shows authored movement dates only.</p>}
      </div>
      <p className="mb-4 max-w-[860px] text-sm leading-relaxed text-muted">
        The map uses present-day borders for navigation. Historical polities and predecessor states
        may not share those borders. A blank year means no matching record in this library, not an
        absence of government, policy, or constitutional history. Country timelines below also include
        small territories and historical states without map shapes.
      </p>
      <div className="mb-3 flex flex-wrap items-center gap-2" aria-label="Atlas layer">
        <button type="button" aria-pressed={!contextLayer} onClick={() => changeLayer("movements")}
          className={`rounded border px-3 py-2 text-sm ${!contextLayer ? "border-accent bg-panel font-semibold" : "border-rule bg-white"}`}>Policy movements</button>
        <button type="button" aria-pressed={contextLayer} disabled={!constitutionalHistory && !historicalSupplements.length} onClick={() => changeLayer("constitutional")}
          className={`rounded border px-3 py-2 text-sm disabled:opacity-50 ${contextLayer ? "border-accent bg-panel font-semibold" : "border-rule bg-white"}`}>Constitutional history</button>
        <a href="#atlas-country-history" className="ml-auto text-sm underline">Browse every country and territory</a>
      </div>
      {contextLayer && constitutionalHistory && <p className="mb-3 rounded border border-rule bg-panel p-3 text-sm leading-relaxed text-muted">
        <a className="underline" href={constitutionalHistory.dataset.source_url} target="_blank" rel="noreferrer">{constitutionalHistory.dataset.name} · v{constitutionalHistory.dataset.version}</a>
        {" "}covers {constitutionalHistory.dataset.coverage_start}–{constitutionalHistory.dataset.coverage_end}.
        {historicalSupplements.length > 0 && <> Additional primary-source events are shown with their own sources and dates.</>}
        {" "}Highlighted countries have a dated source event in the selected year. Events do not classify ideology
        or establish uninterrupted constitutional coverage; individual country observation ranges can be shorter.
      </p>}
      {/* Year scrubber */}
      <div className="mb-3 flex flex-wrap items-center gap-4 rounded border border-rule bg-panel px-4 py-3">
        <div className="flex-none">
          <div className="sc text-[10px] text-muted">year</div>
          <div className="text-[28px] font-semibold leading-none tracking-tight text-ink tabular-nums">
            {year}
          </div>
        </div>
        <input
          type="range"
          min={sliderMin}
          max={sliderMax}
          value={year}
          aria-label="Atlas year"
          onChange={(e) => setYear(parseInt(e.target.value, 10))}
          className="min-w-0 flex-1 basis-[180px] accent-accent"
        />
        <label className="text-xs text-muted">Go to year
          <input key={`${layer}-${year}`} type="number" min={sliderMin} max={sliderMax} defaultValue={year} aria-label="Go to atlas year"
            onBlur={event => { const value = Number(event.target.value); if (Number.isInteger(value)) setYear(Math.max(sliderMin, Math.min(sliderMax, value))); }}
            onKeyDown={event => { if (event.key === "Enter") event.currentTarget.blur(); }}
            className="ml-2 w-20 rounded border border-rule bg-white px-2 py-1 text-sm text-ink" />
        </label>
        <div className="flex-none text-right text-[12px] text-muted">
          <div><strong className="font-semibold text-ink">{contextLayer ? contextAtYear.size : totalActive}</strong>{" "}
            countries with {contextLayer ? "source events" : "authored movements"}</div>
          <div><strong className="font-semibold text-ink">{contextLayer ? [...contextAtYear.values()].reduce((n, events) => n + events.length, 0) : totalMovements}</strong>{" "}
            {contextLayer ? "events" : "movements"} in this year</div>
          <div>Available years: {sliderMin}–{sliderMax}</div>
        </div>
      </div>

      {/* Map */}
      <div className="overflow-hidden rounded border border-rule bg-white">
        <svg viewBox={`0 0 ${W} ${H}`} className="block h-auto w-full" aria-label={contextLayer ? "World map of dated constitutional events" : "World map of authored policy movements"}>
          <rect width={W} height={H} fill="#fafaf8" />
          {paths.map((p) => {
            const r = p.iso3 ? clusterByCountry.get(p.iso3) : undefined;
            const review = p.iso3 ? reviewsByCountry.get(p.iso3) : undefined;
            const fill = contextLayer ? p.iso3 && contextAtYear.has(p.iso3) ? "#735589" : EMPTY_COLOR
              : r ? colorForCluster(r.cluster) : EMPTY_COLOR;
            const open = () => {
              if (!p.iso3) return;
              if (!contextLayer && year === yearMax && review) openCountryReview(review.iso3);
              else openCountryHistory(p.iso3);
            };
            return (
              <path
                key={p.id}
                d={p.d}
                fill={fill}
                stroke="#ffffff"
                strokeWidth={0.5}
                className={p.iso3 ? "cursor-pointer focus:outline focus:outline-2 focus:outline-accent" : ""}
                role={p.iso3 ? "button" : undefined}
                tabIndex={p.iso3 ? 0 : undefined}
                aria-label={p.iso3 ? `${p.name}: ${!contextLayer && year === yearMax && review ? "read election review" : "read country history"}` : undefined}
                onClick={open}
                onKeyDown={event => {
                  if (p.iso3 && (event.key === "Enter" || event.key === " ")) { event.preventDefault(); open(); }
                }}
                onMouseEnter={(e) =>
                  setHover({
                    iso3: p.iso3 ?? p.id,
                    name: p.name,
                    x: e.clientX,
                    y: e.clientY,
                  })
                }
                onMouseMove={(e) =>
                  setHover((h) =>
                    h ? { ...h, x: e.clientX, y: e.clientY } : h
                  )
                }
                onMouseLeave={() => setHover(null)}
              />
            );
          })}
        </svg>
      </div>

      {/* Cluster legend */}
      {contextLayer ? <p className="mt-3 text-xs text-muted"><span className="mr-2 inline-block h-3 w-5 rounded-sm" style={{ background: "#735589" }} />Dated constitutional event · grey means no recorded event at this year</p> : <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-[11.5px] text-muted">
        <span className="sc text-[10px]">dominant ideology</span>
        {CLUSTERS.map((c) => {
          const n = clusterCounts[c.id] ?? 0;
          return (
            <span key={c.id} className="inline-flex items-center gap-1.5">
              <span
                className="inline-block h-[10px] w-[18px] rounded-sm"
                style={{ background: c.color }}
              />
              <span>{c.label}</span>
              {n > 0 && (
                <span className="font-mono text-[10.5px] text-faint">
                  {n}
                </span>
              )}
            </span>
          );
        })}
        <span className="inline-flex items-center gap-1.5">
          <span
            className="inline-block h-[10px] w-[18px] rounded-sm"
            style={{ background: MIXED_COLOR }}
          />
          <span>mixed</span>
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span
            className="inline-block h-[10px] w-[18px] rounded-sm"
            style={{ background: NONE_COLOR }}
          />
          <span>no school signal / government coding incomplete</span>
        </span>
      </div>}

      <section id="atlas-country-history" aria-labelledby="atlas-country-heading" className="mt-8 scroll-mt-40 md:scroll-mt-24">
        <h2 id="atlas-country-heading" className="text-xl font-semibold">Country history and coverage</h2>
        <p className="mt-2 max-w-[900px] text-sm leading-relaxed text-muted">
          Search all {coverage.length} countries, territories, and historical entries. The earliest national movement
          is the library’s starting point for that country, not the beginning of its history. National coverage excludes
          subnational, supranational, and duplicate context records. Dated policies and constitutional events remain separate.
        </p>
        {historicalCoverageSummary.earliest !== null && <p className="mt-3 text-sm font-medium">{historicalCoverageSummary.countries} entries have CCP constitutional events{historicalCoverageSummary.supplementCountries > 0 ? ` · ${historicalCoverageSummary.supplementCountries} entries have primary-source supplements` : ""} · earliest sourced event {historicalCoverageSummary.earliest}.</p>}
        {constitutionalHistory?.dataset.citation && <p className="mt-2 max-w-[900px] text-xs leading-relaxed text-muted">
          <a className="underline" href={constitutionalHistory.dataset.source_url} target="_blank" rel="noreferrer">{constitutionalHistory.dataset.citation}</a>
          {" "}Most countries have annual source rows only through 2019. Later additions record selected events;
          missing later years remain unknown.
        </p>}
        <div id="atlas-history-detail" className="scroll-mt-40 md:scroll-mt-24">
          {selectedCoverage ? <article className="my-5 rounded border border-rule bg-panel p-4 md:p-5" aria-label={`${selectedCoverage.name} history`}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 id="atlas-history-country-heading" tabIndex={-1} className="text-lg font-semibold outline-none">{selectedCoverage.name} <span className="text-sm font-normal text-muted">{selectedCoverage.iso3}</span></h3>
              {reviewsByCountry.has(selectedCoverage.iso3) && <button type="button" className="text-sm underline" onClick={() => openCountryReview(selectedCoverage.iso3)}>Read recent election review</button>}
            </div>
            <p className="mt-2 text-sm text-muted">
              {selectedCoverage.first_national_year === null ? "No primary national movement is authored yet."
                : `Authored national movement intervals run from ${selectedCoverage.first_national_year} to ${selectedCoverage.last_national_year}; these are selective records, not complete annual history.`}
              {!geometryCountries.has(selectedCoverage.iso3) && " This entry has no shape in the map above."}
            </p>
            {selectedCoverage.gaps.length > 0 && <p className="mt-2 text-sm text-muted">Internal years without a national movement record: {selectedCoverage.gaps.map(gap => gap.start === gap.end ? gap.start : `${gap.start}–${gap.end}`).join(", ")}. Years before the first and after the last record are also unobserved.</p>}
            <div className="mt-4 grid gap-5 lg:grid-cols-3">
              <section aria-label="National movement timeline">
                <h4 className="font-semibold">National movements · {selectedMovements.length}</h4>
                <p className="mt-1 text-xs text-muted">Authored policy bundles; candidate status and evidence remain on each record.</p>
                <ol className="mt-3 space-y-3 text-sm">
                  {selectedMovements.slice(0, movementLimit).map(movement => <li key={movement.movement_id}>
                    <span className="block text-xs text-muted">{movement.start}–{movement.end}</span>
                    <a className="underline" href={`/m/${movement.movement_id}/`}>{movement.name}</a>
                  </li>)}
                </ol>
                {selectedMovements.length === 0 && <p className="mt-3 text-sm text-muted">No national movement record. This does not imply policy inactivity.</p>}
                {selectedMovements.length > movementLimit && <button type="button" className="mt-3 text-sm underline" onClick={() => setMovementLimit(n => n + 20)}>Show 20 more movements</button>}
              </section>
              <section aria-label="Dated national policies">
                <h4 className="font-semibold">Dated national policies · {selectedPolicies.length}</h4>
                <p className="mt-1 text-xs text-muted">Individual records do not create a movement interval or a map colour.</p>
                <ol className="mt-3 space-y-3 text-sm">
                  {selectedPolicies.slice(0, policyLimit).map(policy => <li key={policy.policy_id}>
                    <span className="block text-xs text-muted">{policy.year} · {policy.status} · {policy.date_basis === "enacted_date" ? "enacted-date year" : "period-start proxy"}</span>
                    <a className="underline" href={`/p/${policy.policy_id}/`}>{policy.title}</a>
                  </li>)}
                </ol>
                {selectedPolicies.length === 0 && <p className="mt-3 text-sm text-muted">No dated national policy record is authored yet.</p>}
                {selectedPolicies.length > policyLimit && <button type="button" className="mt-3 text-sm underline" onClick={() => setPolicyLimit(n => n + 20)}>Show 20 more policies</button>}
              </section>
              <section aria-label="Constitutional source chronology">
                <h4 className="font-semibold">Constitutional source chronology · {selectedEvents.length}</h4>
                {selectedContext || selectedSupplements.length > 0 ? <>
                  {selectedContext && <>
                    <p className="mt-1 text-xs leading-relaxed text-muted"><strong>CCP source:</strong> {selectedContext.summary}</p>
                    {selectedContext.mapping_note && <p className="mt-2 text-xs leading-relaxed text-muted">{selectedContext.mapping_note}</p>}
                    {selectedContext.coverage.start_year !== null && selectedContext.coverage.end_year !== null && <p className="mt-2 text-xs text-muted">Observed CCP source rows: {selectedContext.coverage.start_year}–{selectedContext.coverage.end_year}. Event dates are discrete; gaps are not filled.</p>}
                  </>}
                  {selectedSupplements.map(supplement => <div key={supplement.title} className="mt-2 text-xs leading-relaxed text-muted"><p><strong>Primary-source supplement:</strong> {supplement.summary}</p>{supplement.mapping_note && <p className="mt-1">{supplement.mapping_note}</p>}<p className="mt-1">Sources consulted: {supplement.checked_on}.</p></div>)}
                  <ol className="mt-3 space-y-3 text-sm">
                    {selectedEvents.slice(0, eventLimit).map(event => <li key={event.id}>
                      <span className="block text-xs text-muted">{event.sourceKind} · {event.start_year}{event.end_year !== undefined && event.end_year !== event.start_year ? `–${event.end_year}` : ""}</span>
                      <strong className="font-medium">{event.title}</strong>
                      <p className="mt-1 text-xs leading-relaxed text-muted">{event.summary}</p>
                      <div className="mt-1 text-xs">{event.sources.map((source, index) => <span key={`${source.url}-${index}`}>{index > 0 ? " · " : ""}<a className="underline" href={source.url} target="_blank" rel="noreferrer">{source.title}</a></span>)}</div>
                    </li>)}
                  </ol>
                  {selectedEvents.length === 0 && <p className="mt-3 text-sm text-muted">No mapped event in this source. This is not evidence that the country lacked a constitution.</p>}
                  {selectedEvents.length > eventLimit && <button type="button" className="mt-3 text-sm underline" onClick={() => setEventLimit(n => n + 20)}>Show 20 more events</button>}
                  {selectedContext && <p className="mt-3 text-xs text-muted">CCP dataset retrieved: {selectedContext.checked_on}.</p>}
                </> : <p className="mt-3 text-sm text-muted">No sourced constitutional chronology is available for this entry.</p>}
              </section>
            </div>
          </article> : <p className="my-4 rounded border border-rule bg-panel p-3 text-sm text-muted">Select a country below to read its dated movements, policies, and sourced historical context.</p>}
        </div>
        <label htmlFor="atlas-country-search" className="mt-4 block text-sm font-medium">Find any country, territory, or historical state</label>
        <input id="atlas-country-search" type="search" value={countryQuery}
          onChange={event => { setCountryQuery(event.target.value); setCountryLimit(40); }}
          placeholder="Name or ISO3 code, including countries without records"
          className="mt-1 w-full max-w-xl rounded border border-rule bg-white px-3 py-2 text-sm" />
        <p className="my-3 text-xs text-muted" aria-live="polite">{visibleCountries.length} matching entries · showing {Math.min(countryLimit, visibleCountries.length)}. No shared historical starting year is assumed.</p>
        <div className="overflow-x-auto rounded border border-rule">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Country-specific authored coverage, including countries with no authored national movements</caption>
            <thead className="bg-panel text-xs text-muted"><tr><th className="p-3">Country or territory</th><th className="p-3">First national movement</th><th className="p-3">National movements</th><th className="p-3">Dated national policies</th><th className="p-3">Constitutional history</th><th className="p-3">Coverage limits</th></tr></thead>
            <tbody>{visibleCountries.slice(0, countryLimit).map(country => <tr key={country.iso3} className="border-t border-rule bg-white align-top">
              <th className="p-3 font-medium"><button type="button" className="text-left underline" onClick={() => openCountryHistory(country.iso3)}>{country.name}</button><span className="mt-1 block text-xs font-normal text-muted">{country.iso3}{country.kind === "historical" ? " · historical polity" : country.kind === "disputed" ? " · supplemental disputed entry" : ""}{!geometryCountries.has(country.iso3) ? " · no map shape" : ""}</span></th>
              <td className="p-3 tabular-nums">{country.first_national_year ?? "Not authored"}</td>
              <td className="p-3 tabular-nums">{country.national_movement_count}</td>
              <td className="p-3">{country.national_policy_count}{country.first_policy_year !== null && <span className="block text-xs text-muted">earliest {country.first_policy_year}</span>}</td>
              <td className="p-3 text-xs text-muted">{(() => {
                const context = historyByCountry.get(country.iso3);
                const supplementEvents = (supplementsByCountry.get(country.iso3) ?? []).flatMap(source => source.events);
                const events = [...(context?.events ?? []), ...supplementEvents];
                if (events.length) return <><span className="block font-medium text-ink">Earliest event {Math.min(...events.map(event => event.start_year))}</span>{context?.events.length ?? 0} CCP events{supplementEvents.length > 0 ? ` · ${supplementEvents.length} primary-source events` : ""}{(!context || context.status === "not_covered" || context.status === "unmapped") && <span className="block">CCP coverage remains absent.</span>}</>;
                return !context || context.status === "not_covered" || context.status === "unmapped" ? "Not covered by CCP" : "No event in observed CCP rows";
              })()}</td>
              <td className="max-w-xs p-3 text-xs leading-relaxed text-muted">{country.first_national_year === null ? "No national movement history authored." : <>
                {country.gaps.length ? `${country.gaps.length} internal gap${country.gaps.length === 1 ? "" : "s"}. ` : "No internal date gaps between these authored intervals. "}
                {country.last_national_year !== null && country.last_national_year < yearMax ? `Last interval ends ${country.last_national_year}. ` : ""}
                {country.intervals.some(interval => interval.start <= year && interval.end >= year) ? `An authored interval includes ${year}.` : `No national interval includes ${year}.`}
              </>}{country.supranational_movement_count + country.subnational_movement_count + country.context_only_movement_count > 0 && <span className="mt-1 block">Additional scope/context records: {country.supranational_movement_count} supranational, {country.subnational_movement_count} subnational, {country.context_only_movement_count} context only.</span>}</td>
            </tr>)}</tbody>
          </table>
        </div>
        {visibleCountries.length === 0 && <p className="py-4 text-sm text-muted">No country or territory matches this search.</p>}
        {visibleCountries.length > countryLimit && <button type="button" className="mt-3 text-sm underline" onClick={() => setCountryLimit(n => n + 40)}>Show 40 more entries</button>}
      </section>

      {(constitutionalHistory?.historical_entities?.length ?? 0) > 0 && <section aria-labelledby="atlas-earlier-polities-heading" className="mt-8">
        <h2 id="atlas-earlier-polities-heading" className="text-xl font-semibold">Earlier polities and other source entities</h2>
        <p className="mt-2 max-w-[900px] text-sm leading-relaxed text-muted">These source-native records are kept separately where there is no reviewed mapping to the country inventory. They do not colour a modern successor on the map.</p>
        <label htmlFor="atlas-earlier-search" className="mt-4 block text-sm font-medium">Find an earlier polity</label>
        <input id="atlas-earlier-search" type="search" value={earlierQuery} onChange={event => setEarlierQuery(event.target.value)}
          placeholder="For example, Prussia or Hanover" className="mt-1 w-full max-w-xl rounded border border-rule bg-white px-3 py-2 text-sm" />
        <p className="my-3 text-xs text-muted" aria-live="polite">{earlierPolities.length} of {constitutionalHistory?.historical_entities?.length} source entities</p>
        <div className="grid gap-3 md:grid-cols-2">
          {earlierPolities.map(entity => <details key={entity.source_cowcode} className="rounded border border-rule bg-white p-4">
            <summary className="cursor-pointer text-sm font-medium">{entity.source_country}<span className="mt-1 block text-xs font-normal text-muted">{entity.events.length} dated events{entity.coverage.start_year !== null && entity.coverage.end_year !== null ? ` · source rows ${entity.coverage.start_year}–${entity.coverage.end_year}` : ""}</span></summary>
            <p className="mt-3 text-xs leading-relaxed text-muted">{entity.summary}</p>
            {entity.mapping_note && <p className="mt-2 text-xs leading-relaxed text-muted">{entity.mapping_note}</p>}
            <ol className="mt-3 space-y-3 text-sm">
              {entity.events.map(event => <li key={event.id}><span className="block text-xs text-muted">{event.start_year}</span><strong className="font-medium">{event.title}</strong><p className="mt-1 text-xs text-muted">{event.summary}</p><div className="mt-1 text-xs">{event.sources.map((source, index) => <span key={`${source.url}-${index}`}>{index ? " · " : ""}<a className="underline" href={source.url} target="_blank" rel="noreferrer">{source.title}</a></span>)}</div></li>)}
            </ol>
            {!entity.events.length && <p className="mt-3 text-sm text-muted">No dated event in these observed source rows.</p>}
            <p className="mt-3 text-xs text-muted">Dataset retrieved: {entity.checked_on}.</p>
          </details>)}
        </div>
        {!earlierPolities.length && <p className="py-4 text-sm text-muted">No source entity matches this search.</p>}
      </section>}

      <section id="atlas-election-results" aria-labelledby="atlas-election-heading" className="mt-8 scroll-mt-40 md:scroll-mt-24">
        <h2 id="atlas-election-heading" className="text-xl font-semibold">Recent election reviews</h2>
        <p className="mt-2 max-w-[800px] text-sm leading-relaxed text-muted">
          Election results and government formation are separate checks. These dated reviews stay
          visible when you explore older map years. A linked movement is an authored policy record,
          and may still be a candidate; a verified election does not validate its policy claims.
          Select a reviewed country on the map or search below.
        </p>
        <label htmlFor="atlas-election-search" className="mt-4 block text-sm font-medium">Find a country or election</label>
        <input id="atlas-election-search" type="search" value={query}
          onChange={e => { setQuery(e.target.value); setSelectedCountry(null); }}
          placeholder="Country, result, or government"
          className="mt-1 w-full max-w-xl rounded border border-rule bg-white px-3 py-2 text-sm" />
        <p className="my-3 text-xs text-muted" aria-live="polite">{visibleReviews.length} of {electionReviews.length} reviewed countries</p>
        <div className="grid gap-3 md:grid-cols-2">
          {visibleReviews.map(review => (
            <details key={review.iso3} open={selectedCountry === review.iso3 || !!query.trim()}
              className="rounded border border-rule bg-white p-4">
              <summary id={`atlas-election-${review.iso3}`} className="cursor-pointer text-sm leading-relaxed">
                <strong>{review.country}</strong> <span className="text-muted">· {review.election_date}</span>
                <span className="mt-1 block text-xs text-muted">{RESULT_LABELS[review.result_status]} · {GOVERNMENT_LABELS[review.government_status]}</span>
              </summary>
              <div className="mt-3 space-y-3 text-sm leading-relaxed">
                <p><strong>{review.election_type}:</strong> {review.result_summary}</p>
                <p><strong>Government:</strong> {review.government_summary}</p>
                {review.government_start_date && <p className="text-xs text-muted">Government start date: {review.government_start_date}</p>}
                {review.coverage_note && <p className="border-l-2 border-rule pl-3 text-muted">{review.coverage_note}</p>}
                {governmentNeedsCoding(review, movements, yearMax, asOf) &&
                  <p className="font-medium">Current government policy coding is incomplete: its movement or referenced policy records are missing. Its current map colour is left unclassified.</p>}
                {review.movement_ids.length > 0 && <p>
                  <span className="text-muted">Authored movement: </span>
                  {review.movement_ids.map((id, index) => <span key={id}>
                    {index > 0 ? "; " : ""}<a className="underline" href={`/m/${id}/`}>{movements.find(m => m.movement_id === id)?.name ?? id}</a>
                  </span>)}
                </p>}
                <div className="text-xs text-muted">
                  <p>Checked {review.checked_on}. Sources:</p>
                  <ul className="mt-1 list-disc space-y-1 pl-4">
                    {review.sources.map(source => <li key={source.url}><a className="break-words underline" href={source.url} target="_blank" rel="noreferrer">{source.title}</a></li>)}
                  </ul>
                </div>
              </div>
            </details>
          ))}
        </div>
        {visibleReviews.length === 0 && <p className="py-4 text-sm text-muted">No reviewed country matches this search.</p>}
      </section>

      {/* Hover tooltip */}
      {hover &&
        (() => {
          if (contextLayer) {
            const events = contextAtYear.get(hover.iso3) ?? [];
            return <div className="pointer-events-none fixed z-50 max-w-[340px] rounded border border-rule bg-white p-3 text-xs shadow-lg"
              style={{ left: Math.max(16, Math.min(hover.x + 14, window.innerWidth - 356)), top: hover.y + 14 }}>
              <strong>{hover.name}</strong><p className="mt-1 text-muted">{events.length ? `${events.length} dated constitutional event${events.length === 1 ? "" : "s"} in ${year}` : `No recorded constitutional event at ${year}.`}</p>
              {events.slice(0, 5).map(event => <p className="mt-1" key={event.id}>{event.title}</p>)}
              <p className="mt-2 text-muted">Click to read country history and source limits.</p>
            </div>;
          }
          const list = activeByCountry.get(hover.iso3) ?? [];
          const uncoded = uncodedGovernments.has(hover.iso3);
          const review = reviewsByCountry.get(hover.iso3);
          const tooltipStyle = {
            left: Math.max(16, Math.min(hover.x + 14, window.innerWidth - 356)),
            top: hover.y + 14,
            maxWidth: "min(340px, calc(100vw - 32px))",
          };
          if (list.length === 0) {
            return (
              <div
                className="pointer-events-none fixed z-50 rounded border border-rule bg-white px-3 py-1.5 text-[12px] text-muted shadow-lg"
                style={tooltipStyle}
              >
                {hover.name}{" "}
                <span className="text-faint">
                  ({hover.iso3}) · {uncoded ? "current government policy coding incomplete" : `no authored movements at ${year}`}
                </span>
                {review && year === yearMax ? <div>Click for election review · checked {review.checked_on}</div> : <div>Click for country history</div>}
              </div>
            );
          }
          const c = clusterByCountry.get(hover.iso3);
          return (
            <div
              className="pointer-events-none fixed z-50 max-w-[340px] rounded border border-rule bg-white p-3 text-[12.5px] shadow-lg"
              style={tooltipStyle}
            >
              <div className="mb-1.5 flex items-baseline justify-between gap-3">
                <strong className="text-ink">{hover.name}</strong>
                <span className="font-mono text-[10.5px] text-faint">
                  {hover.iso3}
                </span>
              </div>
              {review && year === yearMax ? <p className="mb-2 text-[11.5px] text-muted">Click for election review · checked {review.checked_on}</p> : <p className="mb-2 text-[11.5px] text-muted">Click for country history</p>}
              {uncoded && <p className="mb-2 text-[11.5px] font-medium">Current government policy coding is incomplete. Listed episodes do not classify its programme.</p>}
              {c && (
                <div className="mb-2 flex items-center gap-1.5">
                  <span
                    className="inline-block h-[10px] w-[16px] rounded-sm"
                    style={{ background: colorForCluster(c.cluster) }}
                  />
                  <span className="text-[11.5px] font-medium text-ink">
                    {c.cluster === "mixed"
                      ? "Mixed"
                      : c.cluster === "none"
                      ? "No school signal"
                      : CLUSTERS.find((x) => x.id === c.cluster)?.label}
                  </span>
                  {c.bd.length > 1 && (
                    <span className="text-[10.5px] text-faint">
                      {c.bd
                        .slice(0, 3)
                        .map(
                          (b) =>
                            `${
                              CLUSTERS.find((x) => x.id === b.cluster)?.label ??
                              b.cluster
                            }: ${b.n}`
                        )
                        .join(" · ")}
                    </span>
                  )}
                </div>
              )}
              <ul className="m-0 space-y-1 p-0">
                {list.slice(0, 6).map((m) => (
                  <li key={m.movement_id} className="leading-snug">
                    <span
                      className="mr-1 inline-block h-[8px] w-[8px] rounded-sm align-middle"
                      style={{ background: colorForCluster(m.cluster) }}
                    />
                    <span className="text-ink">{m.name}</span>{" "}
                    <span className="text-faint">
                      {m.start}–{m.end >= 9000 ? "now" : m.end}
                    </span>
                  </li>
                ))}
                {list.length > 6 && (
                  <li className="text-faint">+{list.length - 6} more</li>
                )}
              </ul>
            </div>
          );
        })()}
    </div>
  );
}
