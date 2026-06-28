"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import {
  axisHint,
  axisLabel,
  countryLabel,
  countryShortLabel,
  directionGlyph,
  directionLabel,
  evidenceStrengthHint,
  evidenceStrengthLabel,
  linkTypeLabel,
  postureLabel,
} from "@/lib/policy-labels";
import type { PolicyBrowserClientRow } from "@/lib/policy-browser";
import {
  POLICY_QUERY_EXAMPLES,
  analyzePolicyQuery,
  scorePolicyQuery,
} from "@/lib/policy-query";

const VERDICT_BUCKETS = ["supported", "partial", "refuted", "inconclusive", "missing"];
const EVIDENCE_STRENGTHS = ["strong", "moderate", "screening", "unresolved"];

function verdictTone(bucket: string) {
  if (bucket === "supported") return "bg-[#dff1e4] text-[#2c7a4f]";
  if (bucket === "partial") return "bg-[#fdf1da] text-[#9a6818]";
  if (bucket === "refuted") return "bg-[#f3d9d9] text-[#9e2f2f]";
  return "bg-[#ece9e2] text-[#57554e]";
}

function postureTone(posture: string) {
  if (posture === "promising") return "border-[#bcdcc4] bg-[#f2faf4] text-[#245f3e]";
  if (posture === "caution") return "border-[#e3b6b6] bg-[#fbf1f0] text-[#8b2929]";
  if (posture === "evidence_gap") return "border-[#d8d3c8] bg-[#f7f5f0] text-[#57554e]";
  return "border-[#ecd6a6] bg-[#fff8e8] text-[#7c5415]";
}

function evidenceTone(strength: string) {
  if (strength === "strong") return "border-[#bcdcc4] bg-[#f2faf4] text-[#245f3e]";
  if (strength === "moderate") return "border-[#c9d4e6] bg-[#f3f7fc] text-[#38577a]";
  if (strength === "screening") return "border-[#ecd6a6] bg-[#fff8e8] text-[#7c5415]";
  return "border-[#d8d3c8] bg-[#f7f5f0] text-[#57554e]";
}

function linkTypeTone(linkType?: string) {
  if (linkType === "explicit") return "border-[#bcdcc4] bg-[#f2faf4] text-[#245f3e]";
  if (linkType === "inferred") return "border-[#ecd6a6] bg-[#fff8e8] text-[#7c5415]";
  return "border-[#d8d3c8] bg-[#f7f5f0] text-[#57554e]";
}

function strengthScore(strength: string) {
  if (strength === "strong") return 3;
  if (strength === "moderate") return 2;
  if (strength === "screening") return 1;
  return 0;
}

function cleanClaim(claim?: string) {
  return (claim ?? "").replace(/\s+/g, " ").trim();
}

function claimPreview(claim: string) {
  if (claim.length <= 280) return claim;
  return `${claim.slice(0, 280).trimEnd()}...`;
}

function compareRows(sort: string, a: PolicyBrowserClientRow, b: PolicyBrowserClientRow) {
  if (sort === "newest") return (b.year ?? -Infinity) - (a.year ?? -Infinity);
  if (sort === "oldest") return (a.year ?? Infinity) - (b.year ?? Infinity);
  if (sort === "strongest") {
    return (
      strengthScore(b.best_available_evidence) - strengthScore(a.best_available_evidence) ||
      b.tested_hypothesis_count - a.tested_hypothesis_count ||
      a.policy_id.localeCompare(b.policy_id)
    );
  }
  if (sort === "most_caution") {
    return (
      (b.verdict_counts.refuted ?? 0) - (a.verdict_counts.refuted ?? 0) ||
      b.tested_hypothesis_count - a.tested_hypothesis_count ||
      a.policy_id.localeCompare(b.policy_id)
    );
  }
  if (sort === "most_promising") {
    return (
      (b.verdict_counts.supported ?? 0) - (a.verdict_counts.supported ?? 0) ||
      b.tested_hypothesis_count - a.tested_hypothesis_count ||
      a.policy_id.localeCompare(b.policy_id)
    );
  }
  return (
    b.tested_hypothesis_count - a.tested_hypothesis_count ||
    b.linked_hypothesis_count - a.linked_hypothesis_count ||
    a.policy_id.localeCompare(b.policy_id)
  );
}

function matchScoreLabel(score: number) {
  if (score >= 60) return "very close";
  if (score >= 42) return "close";
  if (score >= 26) return "related";
  return "weak";
}

export function PolicyEvidenceBrowser() {
  const [rows, setRows] = useState<PolicyBrowserClientRow[]>([]);
  const [loadingState, setLoadingState] = useState<"loading" | "ready" | "error">("loading");
  const [query, setQuery] = useState("");
  const [country, setCountry] = useState("");
  const [axis, setAxis] = useState("");
  const [posture, setPosture] = useState("");
  const [evidence, setEvidence] = useState("");
  const [coverage, setCoverage] = useState("");
  const [sort, setSort] = useState("tested");

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
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const countries = useMemo(() => {
    const set = new Set<string>();
    for (const row of rows) for (const c of row.countries) set.add(c);
    return [...set].sort((a, b) => countryShortLabel(a).localeCompare(countryShortLabel(b)));
  }, [rows]);

  const axes = useMemo(() => {
    const set = new Set<string>();
    for (const row of rows) for (const a of row.axes) set.add(a.axis);
    return [...set].sort((a, b) => axisLabel(a).localeCompare(axisLabel(b)));
  }, [rows]);

  const coverageOptions = useMemo(() => {
    const set = new Set<string>();
    for (const row of rows) set.add(row.coverage);
    return [...set].sort();
  }, [rows]);

  const queryAnalysis = useMemo(() => analyzePolicyQuery(query), [query]);
  const queryActive = Boolean(queryAnalysis.normalized);

  const matchById = useMemo(() => {
    const matches = new Map<string, ReturnType<typeof scorePolicyQuery>>();
    if (!queryAnalysis.normalized) return matches;
    for (const row of rows) {
      matches.set(row.policy_id, scorePolicyQuery(row, queryAnalysis));
    }
    return matches;
  }, [rows, queryAnalysis]);

  const filtered = useMemo(() => {
    const matches = rows.filter((row) => {
      if (country && !row.countries.includes(country)) return false;
      if (axis && !row.axes.some((a) => a.axis === axis)) return false;
      if (posture && row.posture !== posture) return false;
      if (evidence && row.best_available_evidence !== evidence) return false;
      if (coverage && row.coverage !== coverage) return false;
      if (!queryActive) return true;
      return (matchById.get(row.policy_id)?.score ?? 0) > 0;
    });
    return matches.sort((a, b) => {
      if (queryActive) {
        const scoreDelta = (matchById.get(b.policy_id)?.score ?? 0) - (matchById.get(a.policy_id)?.score ?? 0);
        if (Math.abs(scoreDelta) > 0.001) return scoreDelta;
      }
      return compareRows(sort, a, b);
    });
  }, [rows, queryActive, matchById, country, axis, posture, evidence, coverage, sort]);

  const hasFilters = Boolean(query || country || axis || posture || evidence || coverage);

  return (
    <div>
      <div className="mb-4 rounded border border-rule bg-[#fbfaf6] p-4">
        <div className="grid gap-3 xl:grid-cols-[minmax(300px,1.2fr)_minmax(320px,1fr)]">
          <div>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search a policy idea or paste a policy announcement"
              rows={4}
              className="min-h-[96px] w-full resize-y rounded border border-rule-strong bg-white px-3 py-2 text-[13px] leading-[1.45] text-ink placeholder:text-faint focus:border-accent focus:outline-none"
            />
            <div className="mt-2 flex flex-wrap gap-1.5">
              {POLICY_QUERY_EXAMPLES.map((example) => (
                <button
                  key={example.label}
                  type="button"
                  onClick={() => setQuery(example.query)}
                  className="rounded border border-rule bg-white px-2 py-1 text-[11px] text-muted hover:border-accent hover:text-accent"
                >
                  {example.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <select
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              className="rounded border border-rule-strong bg-white px-2 py-2 text-[12px] text-ink focus:border-accent focus:outline-none"
              aria-label="Country filter"
            >
              <option value="">all countries</option>
              {countries.map((c) => (
                <option key={c} value={c}>
                  {countryLabel(c)}
                </option>
              ))}
            </select>
            <select
              value={axis}
              onChange={(e) => setAxis(e.target.value)}
              className="rounded border border-rule-strong bg-white px-2 py-2 text-[12px] text-ink focus:border-accent focus:outline-none"
              aria-label="Policy axis filter"
            >
              <option value="">all policy axes</option>
              {axes.map((a) => (
                <option key={a} value={a}>
                  {axisLabel(a)} - {a}
                </option>
              ))}
            </select>
            <select
              value={posture}
              onChange={(e) => setPosture(e.target.value)}
              className="rounded border border-rule-strong bg-white px-2 py-2 text-[12px] text-ink focus:border-accent focus:outline-none"
              aria-label="Evidence posture filter"
            >
              <option value="">all postures</option>
              <option value="promising">{postureLabel("promising")}</option>
              <option value="mixed">{postureLabel("mixed")}</option>
              <option value="caution">{postureLabel("caution")}</option>
              <option value="evidence_gap">{postureLabel("evidence_gap")}</option>
            </select>
            <select
              value={evidence}
              onChange={(e) => setEvidence(e.target.value)}
              className="rounded border border-rule-strong bg-white px-2 py-2 text-[12px] text-ink focus:border-accent focus:outline-none"
              aria-label="Evidence strength filter"
            >
              <option value="">all evidence strength</option>
              {EVIDENCE_STRENGTHS.map((strength) => (
                <option key={strength} value={strength}>
                  {evidenceStrengthLabel(strength)}
                </option>
              ))}
            </select>
            <select
              value={coverage}
              onChange={(e) => setCoverage(e.target.value)}
              className="rounded border border-rule-strong bg-white px-2 py-2 text-[12px] text-ink focus:border-accent focus:outline-none"
              aria-label="Coverage filter"
            >
              <option value="">all coverage</option>
              {coverageOptions.map((value) => (
                <option key={value} value={value}>
                  {value.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </div>
        </div>

        {queryActive && (
          <div className="mt-3 border-t border-rule pt-3">
            <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted">
              <span className="sc text-[10px] text-faint">detected</span>
              {queryAnalysis.intents.length > 0 ? (
                queryAnalysis.intents.slice(0, 5).map((intent) => (
                  <span key={intent.id} className="rounded border border-rule bg-white px-2 py-1">
                    {intent.label}
                  </span>
                ))
              ) : (
                <span className="rounded border border-rule bg-white px-2 py-1">plain text</span>
              )}
              {queryAnalysis.isAnnouncementLike && (
                <span className="rounded border border-[#d8c99f] bg-[#fff8e8] px-2 py-1 text-[#6f5018]">
                  announcement
                </span>
              )}
              {queryAnalysis.countryHints.slice(0, 4).map((hint) => (
                <button
                  key={hint.code}
                  type="button"
                  onClick={() => setCountry(hint.code)}
                  className="rounded border border-rule bg-white px-2 py-1 hover:border-accent hover:text-accent"
                  title={countryLabel(hint.code)}
                >
                  {hint.code}
                </button>
              ))}
            </div>

            {queryAnalysis.axes.length > 0 && (
              <div className="mt-2 flex flex-wrap items-center gap-1.5 text-[11px] text-muted">
                <span className="sc mr-1 text-[10px] text-faint">axis fingerprint</span>
                {queryAnalysis.axes.slice(0, 8).map((move) => (
                  <button
                    key={`${move.axis}-${move.direction}-${move.sourceIntentId}`}
                    type="button"
                    onClick={() => setAxis(move.axis)}
                    className="rounded border border-rule bg-white px-2 py-1 hover:border-accent hover:text-accent"
                    title={move.reason}
                  >
                    <span className="font-mono font-semibold">{directionGlyph(move.direction)}</span>{" "}
                    {axisLabel(move.axis)}
                    <span className="ml-1 text-faint">({move.magnitude})</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2 text-[11px] text-muted">
            <span className="rounded border border-rule bg-white px-2 py-1">direct links are curated policy-hypothesis joins</span>
            <span className="rounded border border-rule bg-white px-2 py-1">inferred analogues are axis-level neighbors</span>
            <span className="rounded border border-rule bg-white px-2 py-1">open a hypothesis before treating a card as causal evidence</span>
          </div>
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            className="rounded border border-rule-strong bg-white px-2 py-2 text-[12px] text-ink focus:border-accent focus:outline-none"
            aria-label="Sort policy evidence cards"
          >
            <option value="tested">sort: most tested</option>
            <option value="strongest">sort: strongest design</option>
            <option value="most_promising">sort: most supported</option>
            <option value="most_caution">sort: most refuted</option>
            <option value="newest">sort: newest first</option>
            <option value="oldest">sort: oldest first</option>
          </select>
        </div>
      </div>

      <div className="mb-3 flex items-center justify-between text-[12px] text-muted">
        <span>
          {loadingState === "loading" ? "Loading policy evidence cards" : `${filtered.length} of ${rows.length} policy evidence cards`}
        </span>
        {hasFilters && (
          <button
            type="button"
            onClick={() => {
              setQuery("");
              setCountry("");
              setAxis("");
              setPosture("");
              setEvidence("");
              setCoverage("");
              setSort("tested");
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
        {filtered.slice(0, 120).map((row) => {
          const explicitLinks = row.link_type_counts?.explicit ?? 0;
          const inferredLinks = row.link_type_counts?.inferred ?? 0;
          const match = queryActive ? matchById.get(row.policy_id) : undefined;
          const unresolvedCount =
            (row.verdict_counts.inconclusive ?? 0) +
            (row.verdict_counts.blocked ?? 0) +
            (row.verdict_counts.missing ?? 0) +
            (row.verdict_counts.other ?? 0);

          return (
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
                      <button key={c} type="button" onClick={() => setCountry(c)} className="hover:text-accent" title={countryLabel(c)}>
                        {countryShortLabel(c)} ({c})
                      </button>
                    ))}
                  </div>
                </div>
                <div className="flex flex-wrap items-start justify-end gap-2">
                  {match && match.score > 0 && (
                    <span
                      className="rounded border border-[#c9d4e6] bg-[#f3f7fc] px-2 py-1 text-[11px] font-semibold text-[#38577a]"
                      title={`axis ${match.axisScore.toFixed(1)} / text ${match.textScore.toFixed(1)} / evidence ${match.evidenceScore.toFixed(1)}`}
                    >
                      {matchScoreLabel(match.score)}
                    </span>
                  )}
                  <span className={`rounded border px-2 py-1 text-[11px] font-semibold ${postureTone(row.posture)}`}>
                    {postureLabel(row.posture)}
                  </span>
                </div>
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                {VERDICT_BUCKETS.map((bucket) => {
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
                {unresolvedCount > 0 && (
                  <span className="rounded bg-panel px-2 py-1 text-[11px] text-muted">
                    unresolved {unresolvedCount}
                  </span>
                )}
                <span
                  className={`rounded border px-2 py-1 text-[11px] font-semibold ${evidenceTone(row.best_available_evidence)}`}
                  title={evidenceStrengthHint(row.best_available_evidence)}
                >
                  {evidenceStrengthLabel(row.best_available_evidence)}
                </span>
                {(explicitLinks > 0 || inferredLinks > 0) && (
                  <span className="rounded bg-panel px-2 py-1 text-[11px] text-muted">
                    links: {explicitLinks} direct / {inferredLinks} inferred
                  </span>
                )}
              </div>

              <div className="mt-3 flex flex-wrap gap-1.5">
                {row.axes.slice(0, 8).map((a) => (
                  <button
                    key={`${row.policy_id}-${a.axis}`}
                    type="button"
                    onClick={() => setAxis(a.axis)}
                    className="rounded border border-rule bg-panel px-2 py-1 text-[10.5px] text-muted hover:border-accent hover:text-accent"
                    title={`${a.axis}: ${axisHint(a.axis)} Direction: ${directionLabel(a.direction)}. Magnitude: ${a.magnitude || "unspecified"}. Intent: ${
                      a.intended === true ? "intended" : a.intended === false ? "side effect" : "unknown"
                    }.`}
                  >
                    <span className="font-mono font-semibold">{directionGlyph(a.direction)}</span>{" "}
                    <span>{axisLabel(a.axis)}</span>
                    {a.magnitude && <span className="ml-1 text-faint"> ({a.magnitude})</span>}
                  </button>
                ))}
              </div>

              {match && (match.matchedAxes.length > 0 || match.matchedTerms.length > 0) && (
                <div className="mt-2 flex flex-wrap items-center gap-1.5 text-[11px] text-muted">
                  <span className="sc mr-1 text-[10px] text-faint">query match</span>
                  {match.matchedAxes.slice(0, 5).map((a) => (
                    <button
                      key={`${row.policy_id}-${a.axis}-${a.queryDirection}-${a.rowDirection}`}
                      type="button"
                      onClick={() => setAxis(a.axis)}
                      className={`rounded border px-2 py-1 ${
                        a.sameDirection
                          ? "border-[#bcdcc4] bg-[#f2faf4] text-[#245f3e]"
                          : "border-[#ecd6a6] bg-[#fff8e8] text-[#7c5415]"
                      }`}
                      title={`${a.intentLabel}: query ${directionLabel(a.queryDirection)}, policy ${directionLabel(a.rowDirection)}`}
                    >
                      <span className="font-mono font-semibold">{directionGlyph(a.rowDirection)}</span>{" "}
                      {axisLabel(a.axis)}
                      {!a.sameDirection && <span className="ml-1 text-faint">contrast</span>}
                    </button>
                  ))}
                  {match.matchedTerms.slice(0, Math.max(0, 5 - match.matchedAxes.length)).map((term) => (
                    <span key={`${row.policy_id}-${term}`} className="rounded border border-rule bg-panel px-2 py-1">
                      {term}
                    </span>
                  ))}
                </div>
              )}

              {row.top_hypotheses.length > 0 ? (
                <div className="mt-3 grid gap-1.5">
                  {row.top_hypotheses.slice(0, 3).map((h) => {
                    const claim = cleanClaim(h.claim);
                    return (
                      <Link
                        key={h.hypothesis_id}
                        href={`/h/${h.hypothesis_id}`}
                        className="grid gap-2 rounded border border-rule bg-panel px-3 py-2 text-[12px] hover:border-accent hover:no-underline md:grid-cols-[1fr_auto]"
                      >
                        <span>
                          <span className="block leading-[1.45] text-ink">
                            {claim ? claimPreview(claim) : h.hypothesis_id}
                          </span>
                          {claim && <span className="mt-1 block font-mono text-[10px] text-faint">{h.hypothesis_id}</span>}
                        </span>
                        <span className="flex flex-wrap items-start justify-end gap-1.5">
                          <span className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold ${linkTypeTone(h.link_type)}`}>
                            {linkTypeLabel(h.link_type)}
                          </span>
                          {h.evidence_strength && (
                            <span className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold ${evidenceTone(h.evidence_strength)}`}>
                              {evidenceStrengthLabel(h.evidence_strength)}
                            </span>
                          )}
                          <span className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${verdictTone(h.bucket)}`}>
                            {h.bucket}
                          </span>
                        </span>
                      </Link>
                    );
                  })}
                </div>
              ) : (
                <div className="mt-3 rounded border border-dashed border-rule bg-panel px-3 py-2 text-[12px] text-muted">
                  No linked hypotheses yet. This policy needs a preregistered test before it should influence any school score.
                </div>
              )}

              {row.watch_points.length > 0 && (
                <div className="mt-3 text-[12px] leading-[1.45] text-muted">
                  <span className="sc mr-2 text-[10px] text-faint">watch</span>
                  {row.watch_points.slice(0, 4).join(" / ")}
                </div>
              )}
            </article>
          );
        })}
      </div>

      {loadingState === "ready" && filtered.length === 0 && (
        <div className="rounded border border-rule bg-panel px-4 py-3 text-[13px] text-muted">
          No matching policy evidence cards. Try clearing one filter or using a broader policy phrase.
        </div>
      )}

      {filtered.length > 120 && (
        <div className="mt-4 rounded border border-rule bg-panel px-4 py-3 text-[13px] text-muted">
          Showing first 120 matches. Tighten the filters to inspect the rest.
        </div>
      )}
    </div>
  );
}
