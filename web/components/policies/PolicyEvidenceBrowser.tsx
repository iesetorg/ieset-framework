"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import type { PolicyBrowserClientRow } from "@/lib/policy-browser";

function verdictTone(bucket: string) {
  if (bucket === "supported") return "bg-[#dff1e4] text-[#2c7a4f]";
  if (bucket === "partial") return "bg-[#fdf1da] text-[#9a6818]";
  if (bucket === "refuted") return "bg-[#f3d9d9] text-[#9e2f2f]";
  return "bg-[#ece9e2] text-[#57554e]";
}

function postureLabel(posture: string) {
  if (posture === "promising") return "promising";
  if (posture === "caution") return "caution";
  if (posture === "evidence_gap") return "evidence gap";
  return "mixed";
}

function postureTone(posture: string) {
  if (posture === "promising") return "border-[#bcdcc4] bg-[#f2faf4] text-[#245f3e]";
  if (posture === "caution") return "border-[#e3b6b6] bg-[#fbf1f0] text-[#8b2929]";
  if (posture === "evidence_gap") return "border-[#d8d3c8] bg-[#f7f5f0] text-[#57554e]";
  return "border-[#ecd6a6] bg-[#fff8e8] text-[#7c5415]";
}

export function PolicyEvidenceBrowser() {
  const [rows, setRows] = useState<PolicyBrowserClientRow[]>([]);
  const [loadingState, setLoadingState] = useState<"loading" | "ready" | "error">("loading");
  const [query, setQuery] = useState("");
  const [country, setCountry] = useState("");
  const [axis, setAxis] = useState("");
  const [posture, setPosture] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function loadRows() {
      let response = await fetch("/api/policy-browser-client.json");
      if (!response.ok) {
        response = await fetch("/api/policy-browser-client");
      }
      if (!response.ok) {
        throw new Error(`Policy browser API returned ${response.status}`);
      }
      return response.json() as Promise<{ rows?: PolicyBrowserClientRow[] }>;
    }

    loadRows()
      .then((payload) => {
        if (cancelled) return;
        setRows(payload.rows ?? []);
        setLoadingState("ready");
      })
      .catch(() => {
        if (cancelled) return;
        setLoadingState("error");
      })
    return () => {
      cancelled = true;
    };
  }, []);

  const countries = useMemo(() => {
    const set = new Set<string>();
    for (const row of rows) for (const c of row.countries) set.add(c);
    return [...set].sort();
  }, [rows]);

  const axes = useMemo(() => {
    const set = new Set<string>();
    for (const row of rows) for (const a of row.axes) set.add(a.axis);
    return [...set].sort();
  }, [rows]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return rows.filter((row) => {
      if (country && !row.countries.includes(country)) return false;
      if (axis && !row.axes.some((a) => a.axis === axis)) return false;
      if (posture && row.posture !== posture) return false;
      if (!q) return true;
      const haystack = [
        row.policy_id,
        row.title,
        row.countries.join(" "),
        row.axes.map((a) => a.axis).join(" "),
        row.schools.join(" "),
        row.search_terms.join(" "),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(q);
    });
  }, [rows, query, country, axis, posture]);

  return (
    <div>
      <div className="mb-4 grid gap-3 rounded border border-rule bg-panel p-3 md:grid-cols-[1fr_auto_auto_auto]">
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search policies, axes, schools, or hypotheses"
          className="min-w-[220px] rounded border border-rule-strong bg-white px-3 py-2 text-[13px] text-ink placeholder:text-faint focus:border-accent focus:outline-none"
        />
        <select
          value={country}
          onChange={(e) => setCountry(e.target.value)}
          className="rounded border border-rule-strong bg-white px-2 py-2 font-mono text-[12px] text-ink focus:border-accent focus:outline-none"
        >
          <option value="">all countries</option>
          {countries.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <select
          value={axis}
          onChange={(e) => setAxis(e.target.value)}
          className="max-w-[280px] rounded border border-rule-strong bg-white px-2 py-2 font-mono text-[12px] text-ink focus:border-accent focus:outline-none"
        >
          <option value="">all axes</option>
          {axes.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
        <select
          value={posture}
          onChange={(e) => setPosture(e.target.value)}
          className="rounded border border-rule-strong bg-white px-2 py-2 text-[12px] text-ink focus:border-accent focus:outline-none"
        >
          <option value="">all postures</option>
          <option value="promising">promising</option>
          <option value="mixed">mixed</option>
          <option value="caution">caution</option>
          <option value="evidence_gap">evidence gap</option>
        </select>
      </div>

      <div className="mb-3 flex items-center justify-between text-[12px] text-muted">
        <span>
          {loadingState === "loading" ? "Loading policy evidence cards" : `${filtered.length} of ${rows.length} policy evidence cards`}
        </span>
        {(query || country || axis || posture) && (
          <button
            type="button"
            onClick={() => {
              setQuery("");
              setCountry("");
              setAxis("");
              setPosture("");
            }}
            className="rounded border border-rule-strong bg-white px-2 py-1 text-[12px] text-ink hover:bg-panel"
          >
            clear filters
          </button>
        )}
      </div>

      {loadingState === "error" && (
        <div className="rounded border border-rule bg-panel px-4 py-3 text-[13px] text-muted">
          Could not load the policy-browser index. Rebuild the web app or regenerate the index.
        </div>
      )}

      <div className="grid gap-3">
        {filtered.slice(0, 120).map((row) => (
          <article key={row.policy_id} className="rounded border border-rule bg-white p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <Link href={`/p/${row.policy_id}`} className="text-[16px] font-semibold text-ink hover:text-accent">
                  {row.title}
                </Link>
                <div className="mt-1 flex flex-wrap gap-2 font-mono text-[10.5px] text-faint">
                  <span>{row.policy_id}</span>
                  {row.year != null && <span>{row.year}</span>}
                  {row.countries.slice(0, 6).map((c) => (
                    <button key={c} type="button" onClick={() => setCountry(c)} className="hover:text-accent">
                      {c}
                    </button>
                  ))}
                </div>
              </div>
              <span className={`rounded border px-2 py-1 text-[11px] font-semibold ${postureTone(row.posture)}`}>
                {postureLabel(row.posture)}
              </span>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              {["supported", "partial", "refuted", "inconclusive"].map((bucket) => {
                const count = row.verdict_counts[bucket] ?? 0;
                if (!count) return null;
                return (
                  <span key={bucket} className={`rounded px-2 py-1 text-[11px] font-semibold ${verdictTone(bucket)}`}>
                    {bucket}: {count}
                  </span>
                );
              })}
              <span className="rounded bg-panel px-2 py-1 text-[11px] text-muted">
                tested {row.tested_hypothesis_count}/{row.linked_hypothesis_count}
              </span>
              <span className="rounded bg-panel px-2 py-1 text-[11px] text-muted">
                evidence: {row.best_available_evidence}
              </span>
            </div>

            <div className="mt-3 flex flex-wrap gap-1.5">
              {row.axes.slice(0, 8).map((a) => (
                <button
                  key={`${row.policy_id}-${a.axis}`}
                  type="button"
                  onClick={() => setAxis(a.axis)}
                  className="rounded border border-rule bg-panel px-2 py-1 font-mono text-[10.5px] text-muted hover:border-accent hover:text-accent"
                  title={a.channel}
                >
                  {a.axis}
                </button>
              ))}
            </div>

            {row.top_hypotheses.length > 0 && (
              <div className="mt-3 grid gap-1.5">
                {row.top_hypotheses.slice(0, 3).map((h) => (
                  <Link
                    key={h.hypothesis_id}
                    href={`/h/${h.hypothesis_id}`}
                    className="flex items-center justify-between gap-3 rounded border border-rule bg-panel px-3 py-2 text-[12px] hover:border-accent hover:no-underline"
                  >
                    <span className="font-mono text-ink">{h.hypothesis_id}</span>
                    <span className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${verdictTone(h.bucket)}`}>
                      {h.bucket}
                    </span>
                  </Link>
                ))}
              </div>
            )}

            {row.watch_points.length > 0 && (
              <div className="mt-3 text-[12px] leading-[1.45] text-muted">
                <span className="sc mr-2 text-[10px] text-faint">watch</span>
                {row.watch_points.slice(0, 4).join(" · ")}
              </div>
            )}
          </article>
        ))}
      </div>

      {filtered.length > 120 && (
        <div className="mt-4 rounded border border-rule bg-panel px-4 py-3 text-[13px] text-muted">
          Showing first 120 matches. Tighten the filters to inspect the rest.
        </div>
      )}
    </div>
  );
}
