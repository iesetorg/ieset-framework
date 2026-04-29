"use client";

import { useMemo, useState } from "react";

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
}: {
  movements: AtlasMovement[];
  paths: CountryPath[];
  yearMin: number;
  yearMax: number;
}) {
  const [year, setYear] = useState(yearMax);
  const [hover, setHover] = useState<{
    iso3: string;
    name: string;
    x: number;
    y: number;
  } | null>(null);

  // Movements active at the slider year, indexed by ISO3.
  const activeByCountry = useMemo(() => {
    const map = new Map<string, AtlasMovement[]>();
    for (const m of movements) {
      if (m.start > year || m.end < year) continue;
      for (const iso3 of m.countries) {
        const list = map.get(iso3) ?? [];
        list.push(m);
        map.set(iso3, list);
      }
    }
    return map;
  }, [movements, year]);

  const clusterByCountry = useMemo(() => {
    const out = new Map<
      string,
      { cluster: ClusterId; bd: { cluster: ClusterId; score: number; n: number }[] }
    >();
    for (const [iso3, list] of activeByCountry) {
      // dominantCluster applies per-scope weights:
      //   national=1.0, supranational=0.25, subnational=0.0
      // EU regs still tilt member-state colour; they just don't drown out
      // the national government signal. Subnational policies are skipped.
      out.set(iso3, dominantCluster(list));
    }
    return out;
  }, [activeByCountry]);

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
          onChange={(e) => setYear(parseInt(e.target.value, 10))}
          className="flex-1 min-w-[280px] accent-accent"
        />
        <div className="flex-none text-right text-[12px] text-muted">
          <div>
            <strong className="font-semibold text-ink">{totalActive}</strong>{" "}
            countries
          </div>
          <div>
            <strong className="font-semibold text-ink">{totalMovements}</strong>{" "}
            active movements
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="overflow-hidden rounded border border-rule bg-white">
        <svg viewBox={`0 0 ${W} ${H}`} className="block h-auto w-full">
          <rect width={W} height={H} fill="#fafaf8" />
          {paths.map((p) => {
            const r = p.iso3 ? clusterByCountry.get(p.iso3) : undefined;
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
                className={r ? "cursor-pointer" : ""}
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
          <span>no school signal</span>
        </span>
      </div>

      {/* Hover tooltip */}
      {hover &&
        (() => {
          const list = activeByCountry.get(hover.iso3) ?? [];
          if (list.length === 0) {
            return (
              <div
                className="pointer-events-none fixed z-50 rounded border border-rule bg-white px-3 py-1.5 text-[12px] text-muted shadow-lg"
                style={{ left: hover.x + 14, top: hover.y + 14 }}
              >
                {hover.name}{" "}
                <span className="text-faint">
                  ({hover.iso3}) · no movements at {year}
                </span>
              </div>
            );
          }
          const c = clusterByCountry.get(hover.iso3);
          return (
            <div
              className="pointer-events-none fixed z-50 max-w-[340px] rounded border border-rule bg-white p-3 text-[12.5px] shadow-lg"
              style={{ left: hover.x + 14, top: hover.y + 14 }}
            >
              <div className="mb-1.5 flex items-baseline justify-between gap-3">
                <strong className="text-ink">{hover.name}</strong>
                <span className="font-mono text-[10.5px] text-faint">
                  {hover.iso3}
                </span>
              </div>
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
