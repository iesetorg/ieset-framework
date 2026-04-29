"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { AxisChip } from "@/components/badges/AxisChip";
import type { Axis } from "@/lib/content";

interface PositionAlignment {
  position_id: string;
  alignment: string;
  notes?: string;
}

/**
 * Slimmed-down policy shape passed from the server page to this client
 * filter. We deliberately don't ship the full Policy back to the browser —
 * just the fields the table actually renders, plus the year we filter on.
 */
export interface PolicyRow {
  policy_id: string;
  title: string;
  countries: string[];
  start_year: number; // timeframe.start — the canonical year for filtering
  enacted_label: string; // "2020-09" or "2023" — what we display in the Enacted col
  axes_moved: { axis: string; direction: string }[];
}

function alignmentTone(alignment: string) {
  if (alignment === "aligned")
    return { bg: "#dff1e4", fg: "#2c7a4f", ring: "#bcdcc4", glyph: "✓" };
  if (alignment === "partially_aligned")
    return { bg: "#fdf1da", fg: "#b7791f", ring: "#ecd6a6", glyph: "~" };
  if (alignment === "opposed")
    return { bg: "#f3d9d9", fg: "#9e2f2f", ring: "#e3b6b6", glyph: "✗" };
  return { bg: "#f3f3f1", fg: "#636363", ring: "#dcdad4", glyph: "·" };
}

function channelFor(axis: string, axesMap: Record<string, Axis>): string {
  return axesMap[axis]?.channel ?? axis.split(".")[0];
}

function shapeColors(channel: string) {
  if (channel === "fiscal") return { bg: "#1f3f63", tint: "#eef3fb" };
  if (channel === "regulatory") return { bg: "#4d2a5e", tint: "#f3eef6" };
  if (channel === "monetary") return { bg: "#7a4419", tint: "#fdf2e9" };
  if (channel === "institutional") return { bg: "#234d2c", tint: "#eef6ef" };
  return { bg: "#444", tint: "#f3f3f1" };
}

function shapeGlyph(direction: string): string {
  if (direction === "+") return "↑";
  if (direction === "-") return "↓";
  if (direction === "mixed") return "~";
  return "—";
}

export function PolicyFilterTable({
  rows,
  axesMap,
  policyPositions,
}: {
  rows: PolicyRow[];
  axesMap: Record<string, Axis>;
  policyPositions: Record<string, PositionAlignment[]>;
}) {
  const [query, setQuery] = useState("");
  const [country, setCountry] = useState("");
  const [yearFrom, setYearFrom] = useState("");
  const [yearTo, setYearTo] = useState("");

  const allCountries = useMemo(() => {
    const set = new Set<string>();
    for (const p of rows) for (const c of p.countries) set.add(c);
    return [...set].sort();
  }, [rows]);

  // Year span across the corpus, used for placeholders so users know the
  // available range without having to guess.
  const [minYear, maxYear] = useMemo(() => {
    let lo = Infinity;
    let hi = -Infinity;
    for (const p of rows) {
      if (p.start_year < lo) lo = p.start_year;
      if (p.start_year > hi) hi = p.start_year;
    }
    return [Number.isFinite(lo) ? lo : 1900, Number.isFinite(hi) ? hi : 2025];
  }, [rows]);

  const yearFromNum = yearFrom.trim() ? Number(yearFrom) : null;
  const yearToNum = yearTo.trim() ? Number(yearTo) : null;
  const yearFromValid = yearFromNum !== null && Number.isFinite(yearFromNum);
  const yearToValid = yearToNum !== null && Number.isFinite(yearToNum);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q && !country && !yearFromValid && !yearToValid) return rows;
    return rows.filter((p) => {
      if (country && !p.countries.includes(country)) return false;
      if (yearFromValid && p.start_year < (yearFromNum as number)) return false;
      if (yearToValid && p.start_year > (yearToNum as number)) return false;
      if (!q) return true;
      const haystack = [p.title, p.policy_id, p.countries.join(" ")]
        .join(" ")
        .toLowerCase();
      return haystack.includes(q);
    });
  }, [
    rows,
    query,
    country,
    yearFromNum,
    yearToNum,
    yearFromValid,
    yearToValid,
  ]);

  const anyFilter =
    query !== "" || country !== "" || yearFrom !== "" || yearTo !== "";

  return (
    <div>
      {/* Filter bar */}
      <div className="mb-4 flex flex-wrap items-center gap-3 rounded border border-rule bg-panel px-3 py-2.5">
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by title, policy id, country code…"
          className="flex-1 min-w-[220px] rounded border border-rule-strong bg-white px-3 py-1.5 text-[13.5px] text-ink placeholder:text-faint focus:border-accent focus:outline-none"
        />

        <label className="flex items-center gap-2 text-[12px] text-muted">
          <span className="sc text-[10px]">country</span>
          <select
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            className="rounded border border-rule-strong bg-white px-2 py-1.5 font-mono text-[12px] text-ink focus:border-accent focus:outline-none"
          >
            <option value="">all ({allCountries.length})</option>
            {allCountries.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>

        <label className="flex items-center gap-2 text-[12px] text-muted">
          <span className="sc text-[10px]">year</span>
          <input
            type="number"
            inputMode="numeric"
            value={yearFrom}
            onChange={(e) => setYearFrom(e.target.value)}
            placeholder={String(minYear)}
            min={1700}
            max={2100}
            aria-label="From year"
            className="w-[64px] rounded border border-rule-strong bg-white px-1.5 py-1.5 font-mono text-[12px] text-ink placeholder:text-faint focus:border-accent focus:outline-none"
          />
          <span aria-hidden className="text-faint">
            –
          </span>
          <input
            type="number"
            inputMode="numeric"
            value={yearTo}
            onChange={(e) => setYearTo(e.target.value)}
            placeholder={String(maxYear)}
            min={1700}
            max={2100}
            aria-label="To year"
            className="w-[64px] rounded border border-rule-strong bg-white px-1.5 py-1.5 font-mono text-[12px] text-ink placeholder:text-faint focus:border-accent focus:outline-none"
          />
        </label>

        {anyFilter && (
          <button
            type="button"
            onClick={() => {
              setQuery("");
              setCountry("");
              setYearFrom("");
              setYearTo("");
            }}
            className="rounded border border-rule-strong bg-white px-2.5 py-1.5 text-[12px] text-ink hover:bg-white"
          >
            clear
          </button>
        )}

        <span className="ml-auto text-[12px] text-muted">
          {filtered.length} of {rows.length}
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded border border-rule bg-white">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-rule bg-panel">
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Title
              </th>
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Country
              </th>
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Enacted
              </th>
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Shape
              </th>
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Axes
              </th>
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Schools aligned / opposed
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p) => {
              const positions = policyPositions[p.policy_id] ?? [];
              return (
                <tr
                  key={p.policy_id}
                  className="border-b border-rule last:border-b-0 hover:bg-panel"
                >
                  <td className="p-3 align-top">
                    <Link
                      href={`/p/${p.policy_id}`}
                      className="font-medium text-ink hover:text-accent"
                    >
                      {p.title}
                    </Link>
                    <div className="mt-0.5 font-mono text-[10.5px] text-faint">
                      {p.policy_id}
                    </div>
                  </td>
                  <td className="p-3 align-top">
                    <div className="flex flex-wrap gap-1">
                      {p.countries.map((c) => (
                        <button
                          key={c}
                          type="button"
                          onClick={() => setCountry(c)}
                          className={`rounded px-1.5 py-[1px] font-mono text-[11px] hover:bg-accent-soft ${
                            country === c
                              ? "bg-accent-soft text-accent"
                              : "text-muted"
                          }`}
                          title={`Filter to ${c}`}
                        >
                          {c}
                        </button>
                      ))}
                    </div>
                  </td>
                  <td className="p-3 align-top text-[13px] text-muted">
                    {p.enacted_label}
                  </td>
                  <td className="p-3 align-top">
                    <div className="flex flex-wrap gap-[3px]">
                      {p.axes_moved.map((a, i) => {
                        const ch = channelFor(a.axis, axesMap);
                        const colors = shapeColors(ch);
                        return (
                          <span
                            key={`${a.axis}-shape-${i}`}
                            className="inline-flex h-[18px] w-[18px] items-center justify-center rounded-sm text-[12px] font-bold leading-none ring-1 ring-inset"
                            style={{
                              background: colors.tint,
                              color: colors.bg,
                              borderColor: colors.bg,
                            }}
                            title={`${a.axis} ${a.direction}`}
                            aria-label={`${a.axis} ${a.direction}`}
                          >
                            {shapeGlyph(a.direction)}
                          </span>
                        );
                      })}
                    </div>
                  </td>
                  <td className="p-3 align-top">
                    <div className="flex flex-wrap gap-1">
                      {p.axes_moved.map((a, i) => (
                        <AxisChip
                          key={`${a.axis}-${i}`}
                          axisId={a.axis}
                          axisDef={axesMap[a.axis]}
                          direction={a.direction}
                          noExplain
                        />
                      ))}
                    </div>
                  </td>
                  <td className="p-3 align-top">
                    {positions.length === 0 ? (
                      <span className="text-[11.5px] text-faint">—</span>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {positions.map((a) => {
                          const tone = alignmentTone(a.alignment);
                          return (
                            <Link
                              key={a.position_id}
                              href={`/pos/${a.position_id}`}
                              className="inline-flex items-center gap-1.5 rounded px-1.5 py-[2px] text-[11.5px] font-medium leading-snug ring-1 ring-inset hover:no-underline"
                              style={{
                                background: tone.bg,
                                color: tone.fg,
                                borderColor: tone.ring,
                              }}
                              title={`${a.position_id}: ${a.alignment} (derived from parent movement)`}
                            >
                              <span
                                className="inline-flex h-[13px] w-[13px] items-center justify-center rounded-sm text-[9px] font-bold leading-none"
                                style={{ background: tone.fg, color: tone.bg }}
                                aria-hidden
                              >
                                {tone.glyph}
                              </span>
                              <span className="font-mono text-[11px]">
                                {a.position_id}
                              </span>
                            </Link>
                          );
                        })}
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="p-6 text-center text-[13px] text-muted">
            No policies match the current filter.
          </div>
        )}
      </div>
    </div>
  );
}

