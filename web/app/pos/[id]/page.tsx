import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";

import {
  loadAllPositions,
  loadPosition,
  scoreAllPositions,
  loadAllHypotheses,
  loadRunArtifacts,
} from "@/lib/content";
import {
  axesForPosition,
  hypothesesForPosition,
  movementsForPosition,
} from "@/lib/matching";
import { loadAxes } from "@/lib/content";
import { verdictTone } from "@/lib/verdict";
import { AxisChip } from "@/components/badges/AxisChip";
import { Badge } from "@/components/badges/Badge";

export async function generateStaticParams() {
  const all = await loadAllPositions();
  return all.map((p) => ({ id: p.position_id }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const p = await loadPosition(id);
  if (!p) return { title: id };
  return {
    title: p.school,
    description: p.steelman?.slice(0, 200),
    alternates: {
      canonical: `https://framework.ieset.org/pos/${encodeURIComponent(id)}/`,
    },
  };
}

function outcomeTone(outcome: string): { bg: string; fg: string; label: string } {
  switch (outcome) {
    case "supports_position":
      return { bg: "#dff1e4", fg: "#2c7a4f", label: "supports" };
    case "refutes_position":
      return { bg: "#f3d9d9", fg: "#9e2f2f", label: "refutes" };
    case "partial_supports":
      return { bg: "#ecf6ef", fg: "#4a8b61", label: "partial +" };
    case "partial_refutes":
      return { bg: "#f7e8e6", fg: "#a35548", label: "partial −" };
    case "partial":
      return { bg: "#fdf1da", fg: "#b7791f", label: "test failed" };
    default:
      return { bg: "#f3f3f1", fg: "#636363", label: "untested" };
  }
}

export default async function PositionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const p = await loadPosition(id);
  if (!p) return notFound();

  const allScores = await scoreAllPositions();
  const myScore = allScores.find((s) => s.position_id === id);

  // Inferred evidence — hypotheses testing axes this school speaks to
  const [positionAxes, inferredMatches, allHyps, axesMap, alignedMovements] =
    await Promise.all([
      axesForPosition(id),
      hypothesesForPosition(id, 30),
      loadAllHypotheses(),
      loadAxes(),
      movementsForPosition(id),
    ]);
  const hypById = new Map(allHyps.map((h) => [h.hypothesis_id, h]));

  // Predictions the school already lists — skip these in "inferred" (they appear above)
  const alreadyListedHypIds = new Set(
    (p.falsifiable_specific_claims ?? [])
      .map((c) => c.linked_hypothesis_id)
      .filter((x): x is string => !!x)
  );

  type InferredCard = {
    id: string;
    claim: string;
    verdict: string;
    tone: "green" | "amber" | "red" | "muted";
    shared_axes: string[];
  };
  // verdictTone imported from @/lib/verdict
  const inferredCards: InferredCard[] = [];
  for (const m of inferredMatches) {
    if (alreadyListedHypIds.has(m.hypothesis_id)) continue;
    const h = hypById.get(m.hypothesis_id);
    if (!h) continue;
    const run = await loadRunArtifacts(m.hypothesis_id);
    // Hide untested hypotheses from the inferred-evidence list — they
    // reappear once their replication runs and a verdict lands.
    if (!run.verdict) continue;
    inferredCards.push({
      id: m.hypothesis_id,
      claim: h.claim.split(/(?<=[.!?])\s+/)[0],
      verdict: run.verdict,
      tone: verdictTone(run.verdict),
      shared_axes: m.shared_axes,
    });
  }

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <div className="mb-3 flex items-center gap-3 text-[13px] text-muted">
        <Link href="/pos" className="text-muted hover:text-ink hover:no-underline">
          Positions
        </Link>
        <span>·</span>
        <Link href="/scoreboard" className="text-muted hover:text-ink hover:no-underline">
          Scoreboard
        </Link>
        <span>·</span>
        <span className="font-mono text-[11px] text-faint">{p.position_id}</span>
      </div>
      <h1 className="m-0 mb-3 text-[36px] font-semibold leading-[1.15] tracking-[-0.02em]">
        {p.school}
      </h1>

      {p.proponents && p.proponents.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2 text-[13px] text-muted">
          <span className="font-semibold">Associated proponents:</span>
          <span>{p.proponents.join(" · ")}</span>
        </div>
      )}

      {/* AXIS FINGERPRINT — moved to the top so it's the first thing a reader
          sees about a position. The fingerprint is the most concrete summary
          of what a school is empirically committed to: the channels its
          claims live on. Everything below (track record, predictions,
          aligned movements, inferred evidence) makes more sense once the
          axis vocabulary is on screen. */}
      {positionAxes.length > 0 && (
        <section className="mb-8 rounded border border-rule bg-panel p-5">
          <h2 className="m-0 mb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Axis fingerprint — what this school speaks to
          </h2>
          <p className="m-0 mb-3 max-w-[780px] text-[13.5px] leading-[1.55] text-muted">
            Derived from the steelman + listed predictions. These are the
            framework axes this school makes empirical claims about. Any
            hypothesis testing one of these axes is relevant evidence,
            whether or not the school explicitly cited that hypothesis ID.
          </p>
          <div className="flex flex-wrap gap-1.5">
            {positionAxes.slice(0, 8).map((t) => (
              <AxisChip
                key={t.axis}
                axisId={t.axis}
                axisDef={axesMap[t.axis]}
              />
            ))}
          </div>
        </section>
      )}

      {myScore && myScore.total_claims > 0 && (
        <div className="mb-8 overflow-hidden rounded border border-rule bg-white">
          <div className="grid grid-cols-[1fr_auto] gap-6 p-5">
            <div>
              <h2 className="m-0 text-xs font-semibold uppercase tracking-wider text-muted">
                Empirical track record
              </h2>
              <div className="mt-2 text-[14px] text-ink">
                {myScore.tested > 0 ? (
                  <>
                    Of <strong>{myScore.total_claims}</strong> listed predictions,{" "}
                    <strong>{myScore.tested}</strong> have been tested.{" "}
                    <span className="text-green font-semibold">{myScore.supports} supported</span>
                    {myScore.partial_supports > 0 && (
                      <> · <span style={{ color: "#5fa673" }} className="font-semibold">{myScore.partial_supports} partial +</span></>
                    )}
                    {myScore.refutes > 0 && (
                      <> · <span className="text-red font-semibold">{myScore.refutes} refuted</span></>
                    )}
                    {myScore.partial_refutes > 0 && (
                      <> · <span style={{ color: "#c4756d" }} className="font-semibold">{myScore.partial_refutes} partial −</span></>
                    )}
                    {myScore.partial > 0 && (
                      <> · <span className="text-amber font-semibold">{myScore.partial} inconclusive</span></>
                    )}
                    {myScore.untested > 0 && (
                      <> · <span className="text-muted">{myScore.untested} pending</span></>
                    )}
                    .
                  </>
                ) : (
                  <>
                    <strong>{myScore.total_claims}</strong> predictions listed, none yet tested.
                    They update live when hypotheses run.
                  </>
                )}
              </div>
            </div>
            {myScore.tested > 0 && (
              <div className="text-right">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">
                  Support rate
                </div>
                <div
                  className="mt-1 inline-block rounded px-3 py-1 text-[22px] font-bold"
                  style={{
                    background:
                      myScore.support_rate >= 0.66 ? "#dff1e4"
                      : myScore.support_rate >= 0.33 ? "#fdf1da"
                      : "#f3d9d9",
                    color:
                      myScore.support_rate >= 0.66 ? "#2c7a4f"
                      : myScore.support_rate >= 0.33 ? "#b7791f"
                      : "#9e2f2f",
                  }}
                >
                  {Math.round(myScore.support_rate * 100)}%
                </div>
              </div>
            )}
          </div>
          <ScoreBar s={myScore} />
        </div>
      )}

      {p.steelman && (
        <section className="mb-10">
          <h2 className="mb-4 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Steelman — the strongest version of this school
          </h2>
          <div className="prose-body text-[15px] leading-[1.65]">
            <p>{p.steelman}</p>
          </div>
        </section>
      )}

      <section className="mb-10">
        <h2 className="mb-2 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
          Movements that align, oppose, or partially align with this school
        </h2>
        <p className="mb-4 text-[13px] text-muted">
          Historical movements (parties, governments, doctrinal coalitions)
          whose programmes the framework codes as aligned with, opposed to, or
          partially aligned with this school&apos;s predictions. Alignment is
          scored by what the movement enacted on each axis, not by the labels
          it used.
        </p>
        {alignedMovements.length === 0 ? (
          <p className="rounded border border-rule bg-panel px-4 py-3 text-[13px] text-muted">
            No movements yet linked to this school. As movement specs are
            authored with <code className="text-[12px]">position_alignments</code>,
            they will surface here automatically.
          </p>
        ) : (
          (["aligned", "opposed", "partially_aligned"] as const).map((bucket) => {
            const items = alignedMovements.filter((m) => m.alignment === bucket);
            if (items.length === 0) return null;
            const tone =
              bucket === "aligned"
                ? "border-green text-[#2c7a4f] bg-[#dff1e4]"
                : bucket === "opposed"
                ? "border-red text-[#9e2f2f] bg-[#f3d9d9]"
                : "border-amber text-[#b7791f] bg-[#fdf1da]";
            const label =
              bucket === "aligned"
                ? "Aligned"
                : bucket === "opposed"
                ? "Opposed"
                : "Partially aligned";
            return (
              <div key={bucket} className="mb-6 last:mb-0">
                <div className="mb-2 flex items-center gap-2">
                  <span
                    className={`inline-flex items-center rounded-sm border px-2 py-[2px] text-[10.5px] font-semibold uppercase tracking-wider ${tone}`}
                  >
                    {label}
                  </span>
                  <span className="text-[12px] text-muted">
                    {items.length} {items.length === 1 ? "movement" : "movements"}
                  </span>
                </div>
                <div className="grid grid-cols-1 gap-1.5 md:grid-cols-2 lg:grid-cols-3">
                  {items.map((m) => (
                    <Link
                      key={m.movement_id}
                      href={`/m/${m.movement_id}`}
                      className="group block rounded border border-rule bg-white px-3 py-2 hover:border-rule-strong hover:no-underline"
                    >
                      <div className="text-[13px] font-medium leading-snug text-ink group-hover:text-accent">
                        {m.name ?? m.movement_id}
                      </div>
                      <div className="mt-0.5 flex flex-wrap items-center gap-2 text-[11px] text-muted">
                        {m.countries && m.countries.length > 0 && (
                          <span>{m.countries.slice(0, 3).join(", ")}{m.countries.length > 3 ? "…" : ""}</span>
                        )}
                        {m.era?.start != null && (
                          <span className="font-mono text-[10.5px] text-faint">
                            {m.era.start}{m.era.end != null ? `–${m.era.end === "ongoing" ? "now" : m.era.end}` : ""}
                          </span>
                        )}
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            );
          })
        )}
      </section>

      {myScore && myScore.scored_claims.some((c) => c.outcome !== "untested") && (
        <section className="mb-10">
          <h2 className="mb-4 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Specific predictions — live empirical status
          </h2>
          <div className="space-y-3">
            {myScore.scored_claims.filter((c) => c.outcome !== "untested").map((c, i) => {
              const tone = outcomeTone(c.outcome);
              return (
                <div
                  key={i}
                  className="overflow-hidden rounded border border-rule bg-white"
                >
                  <div className="flex flex-wrap items-start gap-3 p-4">
                    <span
                      className="inline-flex items-center rounded px-2 py-[3px] text-xs font-semibold"
                      style={{ background: tone.bg, color: tone.fg }}
                    >
                      {tone.label}
                    </span>
                    <div className="min-w-[300px] flex-1">
                      <p className="m-0 text-[15px] leading-[1.55] text-ink">{c.claim}</p>
                      <div className="mt-2 flex flex-wrap items-center gap-2 text-[12px] text-muted">
                        <span>School predicts:</span>
                        <code className="text-[11px]">{c.school_prediction}</code>
                        <span>·</span>
                        <span>Hypothesis:</span>
                        {c.hypothesis_exists ? (
                          <Link
                            href={`/h/${c.linked_hypothesis_id}`}
                            className="font-mono text-[11px]"
                          >
                            {c.linked_hypothesis_id}
                          </Link>
                        ) : (
                          <span className="font-mono text-[11px] text-faint">
                            {c.linked_hypothesis_id} <em>(not yet written)</em>
                          </span>
                        )}
                      </div>
                      {c.verdict && (
                        <div className="mt-2 rounded bg-panel px-3 py-2 text-[12.5px] text-muted">
                          <span className="text-ink">{c.verdict}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Axis fingerprint moved to the top of the page (above the empirical
          track record). Inferred-evidence section follows below. */}

      {inferredCards.length > 0 && (
        <section className="mb-10">
          <h2 className="mb-2 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Inferred evidence — hypotheses testing this school&apos;s axes
          </h2>
          <p className="mb-4 text-[13px] text-muted">
            Ranked by axis-overlap score. These are hypotheses already in the
            library whose tests speak to the axes this school&apos;s predictions
            live on, regardless of whether the school explicitly cited them.
          </p>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            {inferredCards.map((ic) => {
              const toneBar =
                ic.tone === "green"
                  ? "bg-green"
                  : ic.tone === "amber"
                  ? "bg-amber"
                  : ic.tone === "red"
                  ? "bg-red"
                  : "bg-faint";
              return (
                <Link
                  key={ic.id}
                  href={`/h/${ic.id}`}
                  className="group block overflow-hidden rounded border border-rule bg-white hover:border-rule-strong hover:no-underline"
                >
                  <div className={toneBar} style={{ height: 3 }} />
                  <div className="flex items-start gap-3 p-3.5">
                    <div className="flex-1 min-w-0">
                      <div className="text-[13.5px] font-medium leading-snug text-ink group-hover:text-accent">
                        {ic.claim}
                      </div>
                      <div className="mt-0.5 font-mono text-[10.5px] text-faint">
                        {ic.id}
                      </div>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {ic.shared_axes.slice(0, 3).map((ax) => (
                          <span
                            key={ax}
                            className="inline-block rounded bg-code-bg px-1.5 py-[1px] font-mono text-[10.5px] text-ink"
                          >
                            {ax}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="flex-none">
                      {ic.tone === "green" && <Badge variant="green" dot>supported</Badge>}
                      {ic.tone === "amber" && <Badge variant="amber" dot>partial</Badge>}
                      {ic.tone === "red" && <Badge variant="red" dot>refuted</Badge>}
                      {ic.tone === "muted" && <Badge variant="muted">pending</Badge>}
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </section>
      )}

      {p.empirical_record_summary && (
        <section className="mb-10">
          <h2 className="mb-4 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Empirical record — narrative summary
          </h2>
          <p className="whitespace-pre-wrap text-[14px] leading-[1.65] text-muted">
            {p.empirical_record_summary.trim()}
          </p>
        </section>
      )}

      {p.scope_decisions && p.scope_decisions.length > 0 && (
        <section className="mb-10">
          <h2 className="mb-4 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Scope decisions — claims this school makes that we do NOT test
          </h2>
          <p className="mb-3 text-[13px] text-muted">
            These are claims explicitly excluded from testing (contested in mainstream literature
            or beyond what available data can identify). Excluding them sharpens what remains.
          </p>
          <ul className="space-y-2">
            {p.scope_decisions.map((s, i) => (
              <li
                key={i}
                className="rounded border-l-[3px] border-faint bg-panel px-4 py-3 text-[13.5px] text-muted"
              >
                {s.trim()}
              </li>
            ))}
          </ul>
        </section>
      )}

      {p.key_texts && p.key_texts.length > 0 && (
        <section className="mb-10">
          <h2 className="mb-4 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Key texts
          </h2>
          <ul className="list-disc pl-5 text-[14px] leading-[1.6] text-muted">
            {p.key_texts.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

function ScoreBar({
  s,
}: {
  s: {
    total_claims: number;
    supports: number;
    refutes: number;
    partial_supports: number;
    partial_refutes: number;
    partial: number;
    untested: number;
  };
}) {
  const total = s.total_claims;
  const seg = (n: number) => `${(n / total) * 100}%`;
  return (
    <div className="flex h-[8px] w-full">
      <div style={{ background: "#2c7a4f", width: seg(s.supports) }} title={`supports: ${s.supports}`} />
      <div style={{ background: "#a8d4b5", width: seg(s.partial_supports) }} title={`partial+: ${s.partial_supports}`} />
      <div style={{ background: "#b7791f", width: seg(s.partial) }} title={`neutral partial: ${s.partial}`} />
      <div style={{ background: "#e3b5b0", width: seg(s.partial_refutes) }} title={`partial-: ${s.partial_refutes}`} />
      <div style={{ background: "#9e2f2f", width: seg(s.refutes) }} title={`refutes: ${s.refutes}`} />
      <div style={{ background: "#e8e6e0", width: seg(s.untested) }} title={`untested: ${s.untested}`} />
    </div>
  );
}
