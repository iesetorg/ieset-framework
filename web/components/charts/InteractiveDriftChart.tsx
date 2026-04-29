"use client";

import { useMemo, useState } from "react";

import { DriftChart } from "./DriftChart";

/**
 * Wrapper around DriftChart that lets the reader pick which countries are
 * drawn. Server-side passes the full series + labels for every country in
 * scope; the user picks an arbitrary subset client-side.
 *
 * The "snake chart" idea: each country is a snake winding up/down through
 * year x cumulative-drift space. With many countries selected at once, the
 * chart resembles a tangle of snakes — but each is independently pickable.
 */

interface InteractiveDriftChartProps {
  /** All series the user can pick from. Keys are stable ISO3 codes. */
  allSeries: Record<string, number[]>;
  /** Years aligned to each series. */
  years: number[];
  /** Map ISO3 → display name. */
  labels: Record<string, string>;
  /** ISO3 codes selected by default. */
  initialSelection?: string[];
  /** Pixel height of the chart. */
  height?: number;
  /** Optional zero-line label. */
  zeroLineLabel?: string;
  /** Optional caption shown below the chart. */
  caption?: string;
  /** Optional pre-grouped chip rows so the picker reads as
   *  "Liberal democracies", "Latin America", etc. instead of one giant list. */
  groups?: Array<{ id: string; label: string; iso3s: string[] }>;
}

export function InteractiveDriftChart({
  allSeries,
  years,
  labels,
  initialSelection,
  height = 420,
  zeroLineLabel,
  caption,
  groups,
}: InteractiveDriftChartProps) {
  const allKeys = useMemo(() => Object.keys(allSeries), [allSeries]);
  const defaultSelection = useMemo(
    () =>
      new Set(
        initialSelection && initialSelection.length > 0
          ? initialSelection
          : allKeys.slice(0, 8)
      ),
    [initialSelection, allKeys]
  );
  const [selected, setSelected] = useState<Set<string>>(defaultSelection);

  const filteredSeries = useMemo(() => {
    const out: Record<string, number[]> = {};
    for (const k of selected) {
      if (allSeries[k]) out[k] = allSeries[k];
    }
    return out;
  }, [allSeries, selected]);

  function toggle(iso3: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(iso3)) next.delete(iso3);
      else next.add(iso3);
      return next;
    });
  }

  function setOnly(iso3s: string[]) {
    setSelected(new Set(iso3s));
  }

  function clearAll() {
    setSelected(new Set());
  }

  function selectAll() {
    setSelected(new Set(allKeys));
  }

  // Group rendering — if groups are provided, lay them out as labelled rows
  // of toggle chips. Otherwise render one big alphabetical list.
  const groupRows = groups
    ? groups
    : [{ id: "all", label: "Countries", iso3s: allKeys.slice().sort() }];

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-2 text-[12px]">
        <span className="font-semibold uppercase tracking-wider text-muted">
          Pick countries
        </span>
        <button
          type="button"
          onClick={selectAll}
          className="rounded border border-rule-strong bg-white px-2 py-[3px] hover:bg-panel"
        >
          select all
        </button>
        <button
          type="button"
          onClick={clearAll}
          className="rounded border border-rule-strong bg-white px-2 py-[3px] hover:bg-panel"
        >
          clear
        </button>
        {groups?.map((g) => (
          <button
            key={g.id}
            type="button"
            onClick={() => setOnly(g.iso3s)}
            className="rounded border border-rule-strong bg-white px-2 py-[3px] hover:bg-panel"
          >
            only {g.label.toLowerCase()}
          </button>
        ))}
        <span className="ml-auto text-muted">{selected.size} selected</span>
      </div>

      <div className="mb-4 space-y-2">
        {groupRows.map((g) => (
          <div key={g.id}>
            {groups && (
              <div className="mb-1 text-[10.5px] font-semibold uppercase tracking-wider text-muted">
                {g.label}
              </div>
            )}
            <div className="flex flex-wrap gap-1.5">
              {g.iso3s.map((iso3) => {
                const isSelected = selected.has(iso3);
                return (
                  <button
                    key={iso3}
                    type="button"
                    onClick={() => toggle(iso3)}
                    className={
                      "rounded border px-2 py-[3px] text-[11.5px] tabular-nums transition-colors " +
                      (isSelected
                        ? "border-accent bg-accent text-white"
                        : "border-rule bg-white text-muted hover:border-rule-strong hover:text-ink")
                    }
                    title={labels[iso3] ?? iso3}
                  >
                    <span className="font-mono">{iso3}</span>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {Object.keys(filteredSeries).length > 0 ? (
        <DriftChart
          series={filteredSeries}
          years={years}
          labels={labels}
          height={height}
          zeroLineLabel={zeroLineLabel}
          caption={caption}
        />
      ) : (
        <div className="rounded border border-rule bg-panel p-6 text-center text-[14px] text-muted">
          No countries selected. Pick one or more above.
        </div>
      )}
    </div>
  );
}
