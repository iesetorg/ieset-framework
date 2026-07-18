import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";

import {
  loadAllAxes,
  loadAxes,
  loadAllHypotheses,
  loadRunArtifacts,
} from "@/lib/content";
import { loadAllPolicies, type Policy } from "@/lib/policies";
import { hypothesesForAxis } from "@/lib/matching";
import { verdictTone } from "@/lib/verdict";
import { Badge } from "@/components/badges/Badge";

export async function generateStaticParams() {
  const axes = await loadAllAxes();
  return axes.map((a) => ({ id: a.id }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const axesMap = await loadAxes();
  const axis = axesMap[id];
  if (!axis) return { title: id };
  return {
    title: `Axis: ${id}`,
    description: axis.description?.slice(0, 200),
    alternates: {
      canonical: `https://framework.ieset.org/a/${encodeURIComponent(id)}/`,
    },
  };
}

interface MatchedPolicy {
  policy: Policy;
  direction: string;
  magnitude?: string;
  intended?: boolean;
  rationale?: string;
}

const DIR_ORDER = ["+", "-", "mixed", "0"];

function directionSymbol(d: string): string {
  if (d === "+") return "↑";
  if (d === "-") return "↓";
  if (d === "mixed") return "~";
  return "—";
}

function directionLabel(d: string): string {
  if (d === "+") return "increased";
  if (d === "-") return "decreased";
  if (d === "mixed") return "mixed";
  return "unchanged";
}

function directionColor(d: string): { bg: string; fg: string } {
  if (d === "+") return { bg: "#dff1e4", fg: "#2c7a4f" };
  if (d === "-") return { bg: "#f3d9d9", fg: "#9e2f2f" };
  if (d === "mixed") return { bg: "#fdf1da", fg: "#b7791f" };
  return { bg: "#f3f3f1", fg: "#636363" };
}

export default async function AxisPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const axesMap = await loadAxes();
  const axis = axesMap[id];
  if (!axis) return notFound();

  const [policies, allHyps, hypIdsForAxis] = await Promise.all([
    loadAllPolicies(),
    loadAllHypotheses(),
    hypothesesForAxis(id),
  ]);
  const hypById = new Map(allHyps.map((h) => [h.hypothesis_id, h]));

  type HypMatch = {
    id: string;
    claim: string;
    verdict?: string;
    tone: "green" | "amber" | "red" | "muted";
  };
  const toneOf = (v: string | undefined): HypMatch["tone"] => verdictTone(v);
  const hypMatches: HypMatch[] = [];
  for (const hid of hypIdsForAxis) {
    const h = hypById.get(hid);
    if (!h) continue;
    const run = await loadRunArtifacts(hid);
    hypMatches.push({
      id: hid,
      claim: h.claim.split(/(?<=[.!?])\s+/)[0],
      verdict: run.verdict,
      tone: toneOf(run.verdict),
    });
  }

  const matches: MatchedPolicy[] = [];
  for (const p of policies) {
    for (const a of p.axes_moved ?? []) {
      if (a.axis === id) {
        matches.push({
          policy: p,
          direction: a.direction,
          magnitude: a.magnitude,
          intended: a.intended,
          rationale: a.rationale,
        });
      }
    }
  }

  // Group by direction
  const byDir = new Map<string, MatchedPolicy[]>();
  for (const m of matches) {
    const list = byDir.get(m.direction) ?? [];
    list.push(m);
    byDir.set(m.direction, list);
  }

  const orderedDirs = [
    ...DIR_ORDER.filter((d) => byDir.has(d)),
    ...[...byDir.keys()].filter((d) => !DIR_ORDER.includes(d)),
  ];

  const shortLabel = id
    .split(".")
    .slice(-1)[0]
    .replace(/_/g, " ");

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <div className="mb-3 flex items-center gap-3 text-[13px] text-muted">
        <Link href="/a" className="text-muted hover:text-ink hover:no-underline">
          Axes
        </Link>
        <span>·</span>
        <span className="capitalize">{axis.channel}</span>
        <span>·</span>
        <span className="font-mono text-[11px] text-faint">{id}</span>
      </div>

      <h1 className="m-0 mb-3 text-[30px] font-semibold capitalize leading-[1.2] tracking-[-0.02em] md:text-[34px]">
        {shortLabel}
      </h1>

      {axis.description && (
        <p className="mb-6 max-w-[780px] text-[16px] leading-[1.6] text-muted">
          {axis.description.trim().replace(/\s+/g, " ")}
        </p>
      )}

      {/* Direction semantics */}
      {axis.direction_semantics && (
        <section className="mb-8">
          <h2 className="mb-3 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Direction semantics
          </h2>
          <dl className="grid grid-cols-[80px_1fr] gap-x-5 gap-y-3 text-[14px]">
            {Object.entries(axis.direction_semantics).map(([dir, meaning]) => {
              const c = directionColor(dir);
              return (
                <div key={dir} className="contents">
                  <dt className="flex items-center gap-2">
                    <span
                      className="inline-flex h-6 w-6 items-center justify-center rounded text-sm font-bold"
                      style={{ background: c.bg, color: c.fg }}
                    >
                      {directionSymbol(dir)}
                    </span>
                    <span className="font-mono text-[12px] text-muted">
                      {dir}
                    </span>
                  </dt>
                  <dd className="text-ink">{meaning}</dd>
                </div>
              );
            })}
          </dl>
        </section>
      )}

      {/* Hypotheses that test this axis */}
      {hypMatches.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-2 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Hypotheses that test this axis
          </h2>
          <p className="mb-4 text-[13px] text-muted">
            Inferred from the hypothesis-axis index. These are the empirical
            tests in the library whose outcomes speak to policies moving on{" "}
            <span className="lowercase">{shortLabel}</span>. Verdict badges
            show the current state of evidence.
          </p>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            {hypMatches.map((hm) => {
              const toneBar =
                hm.tone === "green"
                  ? "bg-green"
                  : hm.tone === "amber"
                  ? "bg-amber"
                  : hm.tone === "red"
                  ? "bg-red"
                  : "bg-faint";
              return (
                <Link
                  key={hm.id}
                  href={`/h/${hm.id}`}
                  className="group block overflow-hidden rounded border border-rule bg-white hover:border-rule-strong hover:no-underline"
                >
                  <div className={toneBar} style={{ height: 3 }} />
                  <div className="flex items-start gap-3 p-3.5">
                    <div className="flex-1 min-w-0">
                      <div className="text-[13.5px] font-medium leading-snug text-ink group-hover:text-accent">
                        {hm.claim}
                      </div>
                      <div className="mt-0.5 font-mono text-[10.5px] text-faint">
                        {hm.id}
                      </div>
                    </div>
                    <div className="flex-none">
                      {hm.tone === "green" && <Badge variant="green" dot>supported</Badge>}
                      {hm.tone === "amber" && <Badge variant="amber" dot>partial</Badge>}
                      {hm.tone === "red" && <Badge variant="red" dot>refuted</Badge>}
                      {hm.tone === "muted" && <Badge variant="muted">pending</Badge>}
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </section>
      )}

      {/* Source publishers */}
      {axis.source_publishers && axis.source_publishers.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Source publishers
          </h2>
          <div className="flex flex-wrap gap-2 text-[12.5px]">
            {axis.source_publishers.map((p) => (
              <span
                key={p}
                className="rounded bg-code-bg px-2 py-[3px] font-mono text-[11.5px] text-ink"
              >
                {p}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Matching policies */}
      <section className="mb-8">
        <h2 className="mb-2 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
          Policies that moved this axis
        </h2>
        <p className="mb-5 text-[13px] text-muted">
          {matches.length} {matches.length === 1 ? "policy" : "policies"} in the
          library moved on this axis. Grouped by direction — this is the raw
          substrate for finding historical analogues of a proposed reform on{" "}
          <span className="lowercase">{shortLabel}</span>.
        </p>

        {matches.length === 0 && (
          <div className="rounded border border-rule bg-panel p-5 text-[14px] text-muted">
            No policies in the library have been coded on this axis yet.
          </div>
        )}

        {orderedDirs.map((dir) => {
          const list = byDir.get(dir)!;
          const c = directionColor(dir);
          return (
            <div key={dir} className="mb-6">
              <div className="mb-2 flex items-center gap-2">
                <span
                  className="inline-flex h-7 w-7 items-center justify-center rounded text-base font-bold"
                  style={{ background: c.bg, color: c.fg }}
                >
                  {directionSymbol(dir)}
                </span>
                <span className="sc text-[10px]">
                  {directionLabel(dir)} · {list.length}
                </span>
              </div>
              <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                {list
                  .sort(
                    (a, b) =>
                      (typeof b.policy.timeframe.start === "number"
                        ? b.policy.timeframe.start
                        : 0) -
                      (typeof a.policy.timeframe.start === "number"
                        ? a.policy.timeframe.start
                        : 0)
                  )
                  .map((m, i) => (
                    <Link
                      key={m.policy.policy_id + i}
                      href={`/p/${m.policy.policy_id}`}
                      className="group block rounded border border-rule bg-white p-3.5 hover:border-rule-strong hover:no-underline"
                    >
                      <div className="flex items-start justify-between gap-2 text-[13.5px]">
                        <div className="font-medium leading-snug text-ink group-hover:text-accent">
                          {m.policy.title}
                        </div>
                      </div>
                      <div className="mt-1 flex flex-wrap items-center gap-2 text-[11.5px] text-muted">
                        <span className="font-mono text-[10.5px] text-faint">
                          {m.policy.countries.join(", ")}
                        </span>
                        <span>·</span>
                        <span>
                          {m.policy.timeframe.start}
                          {m.policy.timeframe.end &&
                          m.policy.timeframe.end !== m.policy.timeframe.start
                            ? `–${
                                m.policy.timeframe.end === "ongoing"
                                  ? "present"
                                  : m.policy.timeframe.end
                              }`
                            : ""}
                        </span>
                        {m.magnitude && (
                          <>
                            <span>·</span>
                            <span>{m.magnitude}</span>
                          </>
                        )}
                        {m.intended === false && (
                          <>
                            <span>·</span>
                            <span className="text-amber">unintended</span>
                          </>
                        )}
                      </div>
                      {m.rationale && (
                        <div className="mt-1.5 text-[12.5px] leading-[1.45] text-muted">
                          {m.rationale.trim().replace(/\s+/g, " ").slice(0, 180)}
                          {m.rationale.length > 180 ? "…" : ""}
                        </div>
                      )}
                    </Link>
                  ))}
              </div>
            </div>
          );
        })}
      </section>
    </div>
  );
}
