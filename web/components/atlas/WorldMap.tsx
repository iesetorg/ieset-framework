"use client";

import { useMemo, useState } from "react";
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
}: {
  movements: AtlasMovement[];
  paths: CountryPath[];
  yearMin: number;
  yearMax: number;
  electionReviews: ElectionReview[];
  asOf: string;
}) {
  const [year, setYear] = useState(yearMax);
  const [query, setQuery] = useState("");
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);
  const [hover, setHover] = useState<{
    iso3: string;
    name: string;
    x: number;
    y: number;
  } | null>(null);

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
          min={yearMin}
          max={yearMax}
          value={year}
          aria-label="Atlas year"
          onChange={(e) => setYear(parseInt(e.target.value, 10))}
          className="min-w-0 flex-1 basis-[180px] accent-accent"
        />
        <div className="flex-none text-right text-[12px] text-muted">
          <div>
            <strong className="font-semibold text-ink">{totalActive}</strong>{" "}
            countries with authored movements
          </div>
          <div>
            <strong className="font-semibold text-ink">{totalMovements}</strong>{" "}
            movements in this year
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="overflow-hidden rounded border border-rule bg-white">
        <svg viewBox={`0 0 ${W} ${H}`} className="block h-auto w-full" aria-label="World map of authored policy movements">
          <rect width={W} height={H} fill="#fafaf8" />
          {paths.map((p) => {
            const r = p.iso3 ? clusterByCountry.get(p.iso3) : undefined;
            const review = p.iso3 ? reviewsByCountry.get(p.iso3) : undefined;
            const fill = r
              ? colorForCluster(r.cluster)
              : EMPTY_COLOR;
            return (
              <path
                key={p.id}
                d={p.d}
                fill={fill}
                stroke="#ffffff"
                strokeWidth={0.5}
                className={review ? "cursor-pointer focus:outline focus:outline-2 focus:outline-accent" : ""}
                role={review ? "button" : undefined}
                tabIndex={review ? 0 : undefined}
                aria-label={review ? `${p.name}: read election review, checked ${review.checked_on}` : undefined}
                onClick={() => { if (review) openCountryReview(review.iso3); }}
                onKeyDown={(e) => {
                  if (review && (e.key === "Enter" || e.key === " ")) {
                    e.preventDefault(); openCountryReview(review.iso3);
                  }
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
      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-[11.5px] text-muted">
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
      </div>

      <section id="atlas-election-results" aria-labelledby="atlas-election-heading" className="mt-8 scroll-mt-6">
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
                {review && <div>Click for election review · checked {review.checked_on}</div>}
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
              {review && <p className="mb-2 text-[11.5px] text-muted">Click for election review · checked {review.checked_on}</p>}
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
