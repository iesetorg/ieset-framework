"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

interface PositionAlignment {
  position_id: string;
  alignment: string;
  notes?: string;
}

export interface MovementRow {
  movement_id: string;
  name: string;
  countries: string[];
  timeframe: { start: number; end: number | string };
  coalition?: string;
  position_alignments?: PositionAlignment[];
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

export function MovementFilterTable({ rows }: { rows: MovementRow[] }) {
  const [query, setQuery] = useState("");
  const [country, setCountry] = useState("");

  const allCountries = useMemo(() => {
    const set = new Set<string>();
    for (const m of rows) for (const c of m.countries) set.add(c);
    return [...set].sort();
  }, [rows]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q && !country) return rows;
    return rows.filter((m) => {
      if (country && !m.countries.includes(country)) return false;
      if (!q) return true;
      const haystack = [
        m.name,
        m.movement_id,
        m.coalition ?? "",
        m.countries.join(" "),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(q);
    });
  }, [rows, query, country]);

  return (
    <div>
      {/* Filter bar */}
      <div className="mb-4 flex flex-wrap items-center gap-3 rounded border border-rule bg-panel px-3 py-2.5">
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by name, country code, coalition…"
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

        {(query || country) && (
          <button
            type="button"
            onClick={() => {
              setQuery("");
              setCountry("");
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
                Movement
              </th>
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Country
              </th>
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Period
              </th>
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Schools aligned / opposed
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((m) => (
              <tr
                key={m.movement_id}
                className="border-b border-rule last:border-0 hover:bg-panel"
              >
                <td className="p-3 align-top">
                  <Link
                    href={`/m/${m.movement_id}`}
                    className="font-medium text-ink hover:underline"
                  >
                    {m.name}
                  </Link>
                  <div className="mt-0.5 font-mono text-[10.5px] text-faint">
                    {m.movement_id}
                  </div>
                  {m.coalition && (
                    <div className="mt-1 text-[12px] text-muted">
                      {m.coalition}
                    </div>
                  )}
                </td>
                <td className="p-3 align-top">
                  <div className="flex flex-wrap gap-1">
                    {m.countries.map((c) => (
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
                <td className="p-3 align-top text-muted">
                  {m.timeframe.start}–
                  {m.timeframe.end === "ongoing" ? "present" : m.timeframe.end}
                </td>
                <td className="p-3 align-top">
                  {(m.position_alignments?.length ?? 0) === 0 ? (
                    <span className="text-[11.5px] text-faint">—</span>
                  ) : (
                    <div className="flex flex-wrap gap-1">
                      {m.position_alignments!.map((a) => {
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
                            title={a.notes ?? a.alignment}
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
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="p-6 text-center text-[13px] text-muted">
            No movements match the current filter.
          </div>
        )}
      </div>
    </div>
  );
}
