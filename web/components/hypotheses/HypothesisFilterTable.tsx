"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { AxisChip } from "@/components/badges/AxisChip";
import { Badge } from "@/components/badges/Badge";
import type { Axis } from "@/lib/content";
import type { EvidenceTier } from "@/lib/types";
import type { VerdictTone } from "@/lib/verdict";

type SchoolOutcome = "aligned" | "partial" | "opposed" | "untested";

export interface HypothesisFilterRow {
  hypothesis_id: string;
  claim: string;
  topic: string;
  status: string;
  evidence_type?: string;
  evidence_tier: EvidenceTier;
  is_public: boolean;
  verdict?: string;
  verdict_label: string;
  verdict_tone: VerdictTone;
  axes: { axis: string; score: number }[];
  schools: {
    position_id: string;
    school: string;
    expected_verdict: "supported" | "falsified" | "mixed";
    polarity: "aligned" | "inverted";
  }[];
  sample?: {
    countries: string[];
    period: [number, number];
    temporal_structure?: string;
  };
}

function alignmentTone(alignment: SchoolOutcome) {
  if (alignment === "aligned")
    return { bg: "#dff1e4", fg: "#2c7a4f", ring: "#bcdcc4", glyph: "✓" };
  if (alignment === "partial")
    return { bg: "#fdf1da", fg: "#b7791f", ring: "#ecd6a6", glyph: "~" };
  if (alignment === "opposed")
    return { bg: "#f3d9d9", fg: "#9e2f2f", ring: "#e3b6b6", glyph: "✗" };
  return { bg: "#f3f3f1", fg: "#636363", ring: "#dcdad4", glyph: "·" };
}

function schoolOutcome(
  expected: "supported" | "falsified" | "mixed",
  actual: string | undefined
): SchoolOutcome {
  if (!actual) return "untested";
  const v = actual.toLowerCase();
  const hypSupp = v.startsWith("supported");
  const hypRef =
    v.startsWith("refuted") ||
    v.startsWith("weakened") ||
    v.startsWith("not supported") ||
    v.startsWith("not_supported");
  const hypPart =
    v.startsWith("partial") ||
    v.startsWith("partially") ||
    v.startsWith("mixed") ||
    v.startsWith("weakly");
  if (expected === "supported" && hypSupp) return "aligned";
  if (expected === "supported" && hypRef) return "opposed";
  if (expected === "falsified" && hypRef) return "aligned";
  if (expected === "falsified" && hypSupp) return "opposed";
  if (hypPart || expected === "mixed") return "partial";
  return "untested";
}

function verdictVariant(tone: VerdictTone): "green" | "amber" | "red" | "muted" {
  if (tone === "green") return "green";
  if (tone === "amber") return "amber";
  if (tone === "red") return "red";
  return "muted";
}

function channelFor(axis: string, axesMap: Record<string, Axis>): string {
  return axesMap[axis]?.channel ?? axis.split(".")[0];
}

function topicLabel(topic: string): string {
  return topic.replace(/_/g, " ");
}

function evidenceLabel(evidence: string | undefined): string {
  return evidence ? evidence.replace(/_/g, " ") : "unspecified";
}

function evidenceTierVariant(
  tier: EvidenceTier
): "green" | "amber" | "muted" {
  if (tier === "featured") return "green";
  if (tier === "calibration") return "amber";
  return "muted";
}

function normalize(text: string): string {
  return text.toLowerCase().replace(/[_-]/g, " ");
}

function rowMatchesYear(
  row: HypothesisFilterRow,
  from: number | null,
  to: number | null
): boolean {
  if (from === null && to === null) return true;
  if (!row.sample) return false;
  const [start, end] = row.sample.period;
  if (from !== null && end < from) return false;
  if (to !== null && start > to) return false;
  return true;
}

export function HypothesisFilterTable({
  rows,
  axesMap,
}: {
  rows: HypothesisFilterRow[];
  axesMap: Record<string, Axis>;
}) {
  const [query, setQuery] = useState("");
  const [verdict, setVerdict] = useState("");
  const [topic, setTopic] = useState("");
  const [school, setSchool] = useState("");
  const [country, setCountry] = useState("");
  const [channel, setChannel] = useState("");
  const [evidence, setEvidence] = useState("");
  const [tier, setTier] = useState("");
  const [linkage, setLinkage] = useState("");
  const [visibility, setVisibility] = useState("");
  const [yearFrom, setYearFrom] = useState("");
  const [yearTo, setYearTo] = useState("");

  const facets = useMemo(() => {
    const topics = new Set<string>();
    const schools = new Map<string, string>();
    const countries = new Set<string>();
    const channels = new Set<string>();
    const evidenceTypes = new Set<string>();

    for (const row of rows) {
      topics.add(row.topic);
      if (row.evidence_type) evidenceTypes.add(row.evidence_type);
      for (const s of row.schools) schools.set(s.position_id, s.school);
      for (const c of row.sample?.countries ?? []) countries.add(c);
      for (const a of row.axes) channels.add(channelFor(a.axis, axesMap));
    }

    return {
      topics: [...topics].sort(),
      schools: [...schools.entries()].sort((a, b) => a[0].localeCompare(b[0])),
      countries: [...countries].sort(),
      channels: [...channels].sort(),
      evidenceTypes: [...evidenceTypes].sort(),
    };
  }, [axesMap, rows]);

  const [minYear, maxYear] = useMemo(() => {
    let lo = Infinity;
    let hi = -Infinity;
    for (const row of rows) {
      if (!row.sample) continue;
      lo = Math.min(lo, row.sample.period[0]);
      hi = Math.max(hi, row.sample.period[1]);
    }
    return [Number.isFinite(lo) ? lo : 1900, Number.isFinite(hi) ? hi : 2026];
  }, [rows]);

  const yearFromNum = yearFrom.trim() ? Number(yearFrom) : null;
  const yearToNum = yearTo.trim() ? Number(yearTo) : null;
  const validYearFrom =
    yearFromNum !== null && Number.isFinite(yearFromNum) ? yearFromNum : null;
  const validYearTo =
    yearToNum !== null && Number.isFinite(yearToNum) ? yearToNum : null;

  const filtered = useMemo(() => {
    const q = normalize(query.trim());

    return rows.filter((row) => {
      if (verdict && row.verdict_tone !== verdict) return false;
      if (topic && row.topic !== topic) return false;
      if (school && !row.schools.some((s) => s.position_id === school))
        return false;
      if (country && !(row.sample?.countries ?? []).includes(country))
        return false;
      if (channel && !row.axes.some((a) => channelFor(a.axis, axesMap) === channel))
        return false;
      if (evidence && row.evidence_type !== evidence) return false;
      if (tier && row.evidence_tier !== tier) return false;
      if (visibility === "public" && !row.is_public) return false;
      if (visibility === "pending" && row.is_public) return false;
      if (linkage === "school-linked" && row.schools.length === 0) return false;
      if (linkage === "school-unlinked" && row.schools.length > 0) return false;
      if (linkage === "axis-linked" && row.axes.length === 0) return false;
      if (linkage === "axis-unlinked" && row.axes.length > 0) return false;
      if (!rowMatchesYear(row, validYearFrom, validYearTo)) return false;
      if (!q) return true;

      const haystack = normalize(
        [
          row.claim,
          row.hypothesis_id,
          row.topic,
          row.status,
          row.evidence_type ?? "",
          row.evidence_tier,
          row.verdict_label,
          row.verdict ?? "",
          row.sample?.countries.join(" ") ?? "",
          row.sample?.temporal_structure ?? "",
          row.axes.map((a) => a.axis).join(" "),
          row.schools.map((s) => `${s.position_id} ${s.school}`).join(" "),
        ].join(" ")
      );
      return haystack.includes(q);
    });
  }, [
    axesMap,
    channel,
    country,
    evidence,
    tier,
    linkage,
    query,
    rows,
    school,
    topic,
    validYearFrom,
    validYearTo,
    verdict,
    visibility,
  ]);

  const counts = useMemo(() => {
    const out = { green: 0, amber: 0, red: 0, muted: 0 };
    for (const row of filtered) out[row.verdict_tone] += 1;
    return out;
  }, [filtered]);

  const hasFilter =
    query ||
    verdict ||
    topic ||
    school ||
    country ||
    channel ||
    evidence ||
    tier ||
    linkage ||
    visibility ||
    yearFrom ||
    yearTo;

  const clearFilters = () => {
    setQuery("");
    setVerdict("");
    setTopic("");
    setSchool("");
    setCountry("");
    setChannel("");
    setEvidence("");
    setTier("");
    setLinkage("");
    setVisibility("");
    setYearFrom("");
    setYearTo("");
  };

  return (
    <div>
      <div className="mb-4 rounded border border-rule bg-panel p-3">
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search claim, id, school, axis, country, verdict..."
            className="min-w-[260px] flex-1 rounded border border-rule-strong bg-white px-3 py-2 text-[13.5px] text-ink placeholder:text-faint focus:border-accent focus:outline-none"
          />

          <label className="flex items-center gap-2 text-[12px] text-muted">
            <span className="sc text-[10px]">verdict</span>
            <select
              aria-label="Filter by verdict"
              value={verdict}
              onChange={(e) => setVerdict(e.target.value)}
              className="rounded border border-rule-strong bg-white px-2 py-2 text-[12px] text-ink focus:border-accent focus:outline-none"
            >
              <option value="">all</option>
              <option value="green">supported</option>
              <option value="amber">partial / mixed</option>
              <option value="red">refuted / weakened</option>
              <option value="muted">pending / inconclusive</option>
            </select>
          </label>

          <label className="flex items-center gap-2 text-[12px] text-muted">
            <span className="sc text-[10px]">topic</span>
            <select
              aria-label="Filter by topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="max-w-[190px] rounded border border-rule-strong bg-white px-2 py-2 text-[12px] text-ink focus:border-accent focus:outline-none"
            >
              <option value="">all ({facets.topics.length})</option>
              {facets.topics.map((t) => (
                <option key={t} value={t}>
                  {topicLabel(t)}
                </option>
              ))}
            </select>
          </label>

          <label className="flex items-center gap-2 text-[12px] text-muted">
            <span className="sc text-[10px]">school</span>
            <select
              aria-label="Filter by school"
              value={school}
              onChange={(e) => setSchool(e.target.value)}
              className="max-w-[190px] rounded border border-rule-strong bg-white px-2 py-2 font-mono text-[12px] text-ink focus:border-accent focus:outline-none"
            >
              <option value="">all ({facets.schools.length})</option>
              {facets.schools.map(([id, name]) => (
                <option key={id} value={id}>
                  {id} - {name}
                </option>
              ))}
            </select>
          </label>

          <span className="ml-auto text-[12px] text-muted">
            <strong className="text-ink">{filtered.length}</strong> of{" "}
            {rows.length}
          </span>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-[12px] text-muted">
            <span className="sc text-[10px]">country</span>
            <select
              aria-label="Filter by country"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              className="rounded border border-rule-strong bg-white px-2 py-1.5 font-mono text-[12px] text-ink focus:border-accent focus:outline-none"
            >
              <option value="">all ({facets.countries.length})</option>
              {facets.countries.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>

          <label className="flex items-center gap-2 text-[12px] text-muted">
            <span className="sc text-[10px]">channel</span>
            <select
              aria-label="Filter by axis channel"
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
              className="rounded border border-rule-strong bg-white px-2 py-1.5 text-[12px] text-ink focus:border-accent focus:outline-none"
            >
              <option value="">all</option>
              {facets.channels.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>

          <label className="flex items-center gap-2 text-[12px] text-muted">
            <span className="sc text-[10px]">evidence</span>
            <select
              aria-label="Filter by evidence type"
              value={evidence}
              onChange={(e) => setEvidence(e.target.value)}
              className="max-w-[190px] rounded border border-rule-strong bg-white px-2 py-1.5 text-[12px] text-ink focus:border-accent focus:outline-none"
            >
              <option value="">all</option>
              {facets.evidenceTypes.map((e) => (
                <option key={e} value={e}>
                  {evidenceLabel(e)}
                </option>
              ))}
            </select>
          </label>

          <label className="flex items-center gap-2 text-[12px] text-muted">
            <span className="sc text-[10px]">visibility</span>
            <select
              aria-label="Filter by public visibility"
              value={visibility}
              onChange={(e) => setVisibility(e.target.value)}
              className="rounded border border-rule-strong bg-white px-2 py-1.5 text-[12px] text-ink focus:border-accent focus:outline-none"
            >
              <option value="">all</option>
              <option value="public">public verdicts</option>
              <option value="pending">pending / not public</option>
            </select>
          </label>

          <label className="flex items-center gap-2 text-[12px] text-muted">
            <span className="sc text-[10px]">tier</span>
            <select
              aria-label="Filter by evidence tier"
              value={tier}
              onChange={(e) => setTier(e.target.value)}
              className="rounded border border-rule-strong bg-white px-2 py-1.5 text-[12px] text-ink focus:border-accent focus:outline-none"
            >
              <option value="">all</option>
              <option value="featured">featured</option>
              <option value="calibration">calibration</option>
              <option value="archive">archive</option>
            </select>
          </label>

          <label className="flex items-center gap-2 text-[12px] text-muted">
            <span className="sc text-[10px]">linkage</span>
            <select
              aria-label="Filter by linkage"
              value={linkage}
              onChange={(e) => setLinkage(e.target.value)}
              className="rounded border border-rule-strong bg-white px-2 py-1.5 text-[12px] text-ink focus:border-accent focus:outline-none"
            >
              <option value="">all</option>
              <option value="school-linked">linked to schools</option>
              <option value="school-unlinked">no school link</option>
              <option value="axis-linked">linked to axes</option>
              <option value="axis-unlinked">no axis link</option>
            </select>
          </label>

          <label className="flex items-center gap-2 text-[12px] text-muted">
            <span className="sc text-[10px]">period</span>
            <input
              type="number"
              inputMode="numeric"
              value={yearFrom}
              onChange={(e) => setYearFrom(e.target.value)}
              placeholder={String(minYear)}
              min={1700}
              max={2100}
              aria-label="From year"
              className="w-[72px] rounded border border-rule-strong bg-white px-2 py-1.5 font-mono text-[12px] text-ink placeholder:text-faint focus:border-accent focus:outline-none"
            />
            <span aria-hidden className="text-faint">
              -
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
              className="w-[72px] rounded border border-rule-strong bg-white px-2 py-1.5 font-mono text-[12px] text-ink placeholder:text-faint focus:border-accent focus:outline-none"
            />
          </label>

          {hasFilter && (
            <button
              type="button"
              onClick={clearFilters}
              className="rounded border border-rule-strong bg-white px-2.5 py-1.5 text-[12px] text-ink hover:bg-white"
            >
              clear filters
            </button>
          )}
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2 text-[11.5px] text-muted">
          <span className="sc mr-1 text-[10px]">within current view</span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-green" />
            {counts.green} supported
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-amber" />
            {counts.amber} partial
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-red" />
            {counts.red} refuted
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-faint" />
            {counts.muted} pending
          </span>
        </div>
      </div>

      <div className="overflow-x-auto rounded border border-rule bg-white">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-rule bg-panel">
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Hypothesis
              </th>
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Verdict
              </th>
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Axes
              </th>
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Schools predicting
              </th>
              <th className="p-3 text-left text-[10px] font-semibold uppercase tracking-wider text-muted">
                Sample
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((row) => (
              <tr
                key={row.hypothesis_id}
                className="border-b border-rule last:border-0 hover:bg-panel"
              >
                <td className="max-w-[520px] p-3 align-top">
                  <Link
                    href={`/h/${row.hypothesis_id}`}
                    className="font-medium text-ink hover:underline"
                  >
                    {row.claim.split(/(?<=[.!?])\s+/)[0]}
                  </Link>
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-[10.5px] text-faint">
                    {!row.is_public && (
                      <span className="rounded border border-rule bg-panel px-1.5 py-[1px] text-[10px] uppercase tracking-wide text-muted">
                        not public yet
                      </span>
                    )}
                    <button
                      type="button"
                      onClick={() => setQuery(row.hypothesis_id)}
                      className="font-mono hover:text-accent"
                      title="Search this hypothesis id"
                    >
                      {row.hypothesis_id}
                    </button>
                    <button
                      type="button"
                      onClick={() => setTopic(row.topic)}
                      className="capitalize hover:text-accent"
                      title={`Filter topic to ${topicLabel(row.topic)}`}
                    >
                      {topicLabel(row.topic)}
                    </button>
                    <button
                      type="button"
                      onClick={() => setEvidence(row.evidence_type ?? "")}
                      className="hover:text-accent"
                      title="Filter by evidence type"
                    >
                      {evidenceLabel(row.evidence_type)}
                    </button>
                    <Badge variant={evidenceTierVariant(row.evidence_tier)}>
                      {row.evidence_tier}
                    </Badge>
                  </div>
                </td>
                <td className="p-3 align-top">
                  <Badge variant={verdictVariant(row.verdict_tone)} dot>
                    {row.verdict_label}
                  </Badge>
                </td>
                <td className="p-3 align-top">
                  {row.axes.length === 0 ? (
                    <button
                      type="button"
                      onClick={() => setLinkage("axis-unlinked")}
                      className="text-[11.5px] text-faint hover:text-accent"
                    >
                      no axis link
                    </button>
                  ) : (
                    <div className="flex max-w-[360px] flex-wrap gap-1">
                      {row.axes.slice(0, 8).map((t) => (
                        <span key={t.axis} className="inline-flex gap-1">
                          <AxisChip
                            axisId={t.axis}
                            axisDef={axesMap[t.axis]}
                            noExplain
                          />
                        </span>
                      ))}
                      {row.axes.length > 8 && (
                        <span className="rounded bg-code-bg px-1.5 py-[2px] text-[11px] text-muted">
                          +{row.axes.length - 8}
                        </span>
                      )}
                    </div>
                  )}
                </td>
                <td className="p-3 align-top">
                  {row.schools.length === 0 ? (
                    <button
                      type="button"
                      onClick={() => setLinkage("school-unlinked")}
                      className="text-[11.5px] text-faint hover:text-accent"
                    >
                      no school link
                    </button>
                  ) : (
                    <div className="flex max-w-[360px] flex-wrap gap-1">
                      {row.schools.map((s) => {
                        const outcome = schoolOutcome(
                          s.expected_verdict,
                          row.verdict
                        );
                        const outTone = alignmentTone(outcome);
                        return (
                          <Link
                            key={s.position_id}
                            href={`/pos/${s.position_id}`}
                            className="inline-flex items-center gap-1.5 rounded px-1.5 py-[2px] text-[11.5px] font-medium leading-snug ring-1 ring-inset hover:no-underline"
                            style={{
                              background: outTone.bg,
                              color: outTone.fg,
                              borderColor: outTone.ring,
                            }}
                            title={`${s.school} expects ${s.expected_verdict}${
                              s.polarity === "inverted"
                                ? " (claim is inverted vs hypothesis)"
                                : ""
                            }${
                              row.verdict
                                ? ` · actual: ${row.verdict.toLowerCase()}`
                                : " · run pending"
                            }`}
                          >
                            <span
                              className="inline-flex h-[13px] w-[13px] items-center justify-center rounded-sm text-[9px] font-bold leading-none"
                              style={{
                                background: outTone.fg,
                                color: outTone.bg,
                              }}
                              aria-hidden
                            >
                              {outTone.glyph}
                            </span>
                            <span className="font-mono text-[11px]">
                              {s.position_id}
                            </span>
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </td>
                <td className="p-3 align-top text-[12px] text-muted">
                  {row.sample ? (
                    <div className="space-y-1">
                      <div className="flex flex-wrap gap-1">
                        {row.sample.countries.slice(0, 6).map((c) => (
                          <button
                            key={c}
                            type="button"
                            onClick={() => setCountry(c)}
                            className={`rounded px-1.5 py-[1px] font-mono text-[11px] hover:bg-accent-soft ${
                              country === c
                                ? "bg-accent-soft text-accent"
                                : "text-muted"
                            }`}
                            title={`Filter country to ${c}`}
                          >
                            {c}
                          </button>
                        ))}
                        {row.sample.countries.length > 6 && (
                          <span className="text-[11px] text-faint">
                            +{row.sample.countries.length - 6}
                          </span>
                        )}
                      </div>
                      <div>
                        {row.sample.period[0]}-{row.sample.period[1]}
                      </div>
                    </div>
                  ) : (
                    <span className="text-faint">no sample</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="p-8 text-center text-[13px] text-muted">
            No hypotheses match the current filters. Clear one filter or search
            a broader term.
          </div>
        )}
      </div>
    </div>
  );
}
