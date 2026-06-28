import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";

import {
  loadAxes,
  loadRunArtifacts,
  loadAllHypotheses,
  axisShortLabel,
} from "@/lib/content";
import { loadPolicy, loadAllPolicies } from "@/lib/policies";
import { hypothesesForPolicy, similarPolicies } from "@/lib/matching";
import { AxisTile } from "@/components/cards/AxisTile";
import { AxisChip } from "@/components/badges/AxisChip";
import { Badge } from "@/components/badges/Badge";
import { SteelmanBlock } from "@/components/cards/SteelmanBlock";

export async function generateStaticParams() {
  const all = await loadAllPolicies();
  return all.map((p) => ({ id: p.policy_id }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const p = await loadPolicy(id);
  if (!p) return { title: id };
  return {
    title: p.title,
    description: p.description?.slice(0, 200),
  };
}

function verdictTone(v: string | undefined): "green" | "amber" | "red" | "muted" {
  if (!v) return "muted";
  const vl = v.toLowerCase();
  if (vl.startsWith("supported")) return "green";
  if (vl.startsWith("partial") || vl.startsWith("mixed")) return "amber";
  if (vl.startsWith("refuted") || vl.startsWith("weakened")) return "red";
  return "muted";
}

function formatReference(reference: unknown): string {
  if (typeof reference === "string") return reference;
  if (typeof reference === "number" || typeof reference === "boolean") {
    return String(reference);
  }
  if (Array.isArray(reference)) {
    return reference.map(formatReference).filter(Boolean).join("; ");
  }
  if (reference && typeof reference === "object") {
    return Object.entries(reference)
      .map(([key, value]) => {
        const formatted = formatReference(value);
        return formatted ? `${key}: ${formatted}` : key;
      })
      .join("; ");
  }
  return "";
}

export default async function PolicyPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const policy = await loadPolicy(id);
  if (!policy) return notFound();

  const axesMap = await loadAxes();
  const [allHyps, allPolicies] = await Promise.all([
    loadAllHypotheses(),
    loadAllPolicies(),
  ]);
  const hypById = new Map(allHyps.map((h) => [h.hypothesis_id, h]));

  const linkedHyps: {
    id: string;
    claim?: string;
    verdict?: string;
    tone: "green" | "amber" | "red" | "muted";
    inferred?: boolean;
    shared_axes?: string[];
  }[] = [];

  const explicitIds = new Set(policy.linked_hypotheses ?? []);
  for (const hid of policy.linked_hypotheses ?? []) {
    const h = hypById.get(hid);
    const run = await loadRunArtifacts(hid);
    linkedHyps.push({
      id: hid,
      claim: h?.claim.split(/(?<=[.!?])\s+/)[0],
      verdict: run.verdict,
      tone: verdictTone(run.verdict),
    });
  }

  // Inferred links — hypotheses whose axis tags overlap this policy's axes_moved
  const inferredMatches = await hypothesesForPolicy(policy, 8);
  for (const m of inferredMatches) {
    if (explicitIds.has(m.hypothesis_id)) continue;
    const h = hypById.get(m.hypothesis_id);
    if (!h) continue;
    const run = await loadRunArtifacts(m.hypothesis_id);
    linkedHyps.push({
      id: m.hypothesis_id,
      claim: h.claim.split(/(?<=[.!?])\s+/)[0],
      verdict: run.verdict,
      tone: verdictTone(run.verdict),
      inferred: true,
      shared_axes: m.shared_axes,
    });
  }

  // Similar historical policies by axis overlap
  const similar = similarPolicies(policy, allPolicies, { limit: 8 });

  const endLabel =
    policy.timeframe.end === "ongoing" ? "present" : policy.timeframe.end;

  // Intended vs unintended effects grouped
  const intended = (policy.axes_moved ?? []).filter(
    (a) => a.intended !== false
  );
  const unintended = (policy.axes_moved ?? []).filter(
    (a) => a.intended === false
  );

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <div className="mb-3 flex items-center gap-3 text-[13px] text-muted">
        <Link href="/p" className="text-muted hover:text-ink hover:no-underline">
          Policies
        </Link>
        <span>·</span>
        <span className="font-mono text-[11px] text-faint">
          {policy.policy_id}
        </span>
      </div>

      <h1 className="m-0 mb-3 text-[30px] font-semibold leading-[1.2] tracking-[-0.02em] md:text-[34px]">
        {policy.title}
      </h1>

      <div className="mb-6 flex flex-wrap items-center gap-3 text-[14px] text-muted">
        <span>
          <strong className="text-ink">{policy.countries.join(", ")}</strong>
        </span>
        <span>·</span>
        <span>
          <strong className="text-ink">{policy.timeframe.start}</strong> –{" "}
          {endLabel}
        </span>
        {policy.timeframe.enacted_date && (
          <>
            <span>·</span>
            <span>enacted {policy.timeframe.enacted_date}</span>
          </>
        )}
        {policy.coalition_label_at_enactment && (
          <>
            <span>·</span>
            <span>{policy.coalition_label_at_enactment}</span>
          </>
        )}
        <Badge variant="muted">{policy.status}</Badge>
      </div>

      {/* AXIS CHIP STRIP — channel-coloured, at-a-glance fingerprint */}
      {(policy.axes_moved?.length ?? 0) > 0 && (
        <div className="mb-6 flex flex-wrap items-center gap-1.5">
          <span className="sc mr-1 text-[10px]">moves</span>
          {policy.axes_moved!.map((a, i) => (
            <AxisChip
              key={`${a.axis}-${i}`}
              axisId={a.axis}
              axisDef={axesMap[a.axis]}
              direction={a.direction}
            />
          ))}
        </div>
      )}

      {/* DESCRIPTION */}
      {policy.description && (
        <section className="mb-8 rounded border border-rule bg-white p-5">
          <h2 className="m-0 mb-3 text-xs font-semibold uppercase tracking-wider text-muted">
            What the policy did
          </h2>
          <p className="m-0 whitespace-pre-wrap text-[15px] leading-[1.65] text-ink">
            {policy.description.trim()}
          </p>
        </section>
      )}

      {/* AXES MOVED */}
      {(intended.length > 0 || unintended.length > 0) && (
        <section className="mb-8">
          <h2 className="mb-2 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Policy-content fingerprint — what this policy moved, on which axes
          </h2>
          <p className="mb-4 text-[13px] text-muted">
            Per invariant 3, reforms are scored by what they did on each
            channel-separated axis, not by the party that enacted them. This
            fingerprint is how the policy-match engine finds historical
            analogues.
          </p>

          {intended.length > 0 && (
            <>
              <div className="sc mb-2 text-[10px]">intended</div>
              <div className="mb-5 grid grid-cols-1 gap-3 md:grid-cols-2">
                {intended.map((a, i) => (
                  <AxisTile key={i} move={a} axisDef={axesMap[a.axis]} />
                ))}
              </div>
            </>
          )}

          {unintended.length > 0 && (
            <>
              <div className="sc mb-2 text-[10px]">unintended / side-effect</div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {unintended.map((a, i) => (
                  <AxisTile key={i} move={a} axisDef={axesMap[a.axis]} />
                ))}
              </div>
            </>
          )}
        </section>
      )}

      {/* ENACTED BY */}
      {policy.enacted_by && policy.enacted_by.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-4 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Enacted by
          </h2>
          <ul className="m-0 list-none space-y-1.5 p-0">
            {policy.enacted_by.map((mid) => (
              <li key={mid}>
                <Link
                  href={`/m/${mid}`}
                  className="font-mono text-[13px] text-accent hover:underline"
                >
                  {mid}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* LINKED HYPOTHESES — the empirical evidence */}
      {linkedHyps.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-2 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Empirical evidence — linked hypotheses
          </h2>
          <p className="mb-4 text-[13px] text-muted">
            Explicit links are curated by the author. Inferred links are
            hypotheses in the library that test the same axes this policy
            moved — the framework&apos;s answer to &quot;what does the data
            say about a policy like this?&quot;.
          </p>
          <div className="space-y-3">
            {linkedHyps.map((lh) => {
              const toneBar =
                lh.tone === "green"
                  ? "bg-green"
                  : lh.tone === "amber"
                  ? "bg-amber"
                  : lh.tone === "red"
                  ? "bg-red"
                  : "bg-faint";
              return (
                <Link
                  key={lh.id}
                  href={`/h/${lh.id}`}
                  className="group block overflow-hidden rounded border border-rule bg-white hover:border-rule-strong hover:no-underline"
                >
                  <div className={toneBar} style={{ height: 3 }} />
                  <div className="flex items-start gap-3 p-4">
                    <div className="flex-1 min-w-0">
                      {lh.claim && (
                        <div className="text-[14.5px] font-medium leading-snug text-ink group-hover:text-accent">
                          {lh.claim}
                        </div>
                      )}
                      <div className="mt-0.5 flex flex-wrap items-center gap-2 font-mono text-[11px] text-faint">
                        <span>{lh.id}</span>
                        {lh.inferred && (
                          <span className="inline-flex items-center rounded-sm bg-accent-soft px-1.5 py-[1px] font-sans text-[10px] font-medium uppercase tracking-wider text-accent">
                            inferred
                          </span>
                        )}
                      </div>
                      {lh.shared_axes && lh.shared_axes.length > 0 && (
                        <div className="mt-1 flex flex-wrap gap-1 text-[11px] text-muted">
                          <span className="sc mr-1 text-[10px]">via</span>
                          {lh.shared_axes.map((ax) => (
                            <span
                              key={ax}
                              className="inline-block rounded bg-code-bg px-1.5 py-[1px] font-mono text-[10.5px] text-ink"
                            >
                              {ax}
                            </span>
                          ))}
                        </div>
                      )}
                      {lh.verdict && (
                        <div className="mt-2 text-[12.5px] leading-[1.5] text-muted">
                          {lh.verdict.length > 160
                            ? lh.verdict.slice(0, 160) + "…"
                            : lh.verdict}
                        </div>
                      )}
                    </div>
                    <div>
                      {lh.tone === "green" && (
                        <Badge variant="green" dot>supported</Badge>
                      )}
                      {lh.tone === "amber" && (
                        <Badge variant="amber" dot>partial</Badge>
                      )}
                      {lh.tone === "red" && (
                        <Badge variant="red" dot>refuted</Badge>
                      )}
                      {lh.tone === "muted" && (
                        <Badge variant="muted">run pending</Badge>
                      )}
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </section>
      )}

      {/* SIMILAR HISTORICAL POLICIES — the policy-match engine surface */}
      {similar.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-2 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Similar historical policies
          </h2>
          <p className="mb-4 text-[13px] text-muted">
            Ranked by axis-fingerprint overlap with this policy. Direction
            match bolded — those are the closest historical analogues. Shape
            of the match is what drives policy-outcome comparison, not the
            country or party label.
          </p>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            {similar.map((m) => (
              <Link
                key={m.policy.policy_id}
                href={`/p/${m.policy.policy_id}`}
                className="group block rounded border border-rule bg-white p-3.5 hover:border-rule-strong hover:no-underline"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="text-[13.5px] font-medium leading-snug text-ink group-hover:text-accent">
                      {m.policy.title}
                    </div>
                    <div className="mt-0.5 flex flex-wrap items-center gap-2 text-[11px] text-muted">
                      <span className="font-mono text-[10.5px] text-faint">
                        {m.policy.countries.join(", ")}
                      </span>
                      <span>·</span>
                      <span>{m.policy.timeframe.start}</span>
                    </div>
                  </div>
                  <div className="flex-none text-right tabular-nums">
                    <div className="text-[11px] text-muted">match</div>
                    <div className="text-[13px] font-semibold text-ink">
                      {m.score.toFixed(1)}
                    </div>
                  </div>
                </div>
                <div className="mt-2 flex flex-wrap gap-1">
                  {m.shared_axes.map((sa) => (
                    <span
                      key={sa.axis}
                      className={`inline-flex items-center rounded px-1.5 py-[1px] font-mono text-[10.5px] ${
                        sa.same_direction
                          ? "bg-accent-soft font-semibold text-accent"
                          : "bg-code-bg text-muted"
                      }`}
                      title={
                        sa.same_direction
                          ? "same direction on this axis"
                          : "opposite direction on this axis"
                      }
                    >
                      {axisShortLabel(sa.axis)}
                    </span>
                  ))}
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* STEELMAN */}
      {policy._steelman_html && (
        <section className="mb-8">
          <h2 className="mb-3 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Strongest case for this policy
          </h2>
          <p className="mb-3 text-[13px] text-muted">
            Every policy ships with its charitable defense. The framework earns
            credibility by handling the case for a reform at its strongest.
          </p>
          <SteelmanBlock
            html={policy._steelman_html}
            sourcePath={policy.steelman}
          />
        </section>
      )}

      {/* REFERENCES */}
      {policy.references && policy.references.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            References
          </h2>
          <ul className="m-0 list-none space-y-1 p-0 text-[13px] text-ink">
            {policy.references.map((r, i) => (
              <li key={i}>· {formatReference(r)}</li>
            ))}
          </ul>
        </section>
      )}

      {policy.notes && (
        <section className="mb-8">
          <h2 className="mb-3 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Notes
          </h2>
          <p className="whitespace-pre-wrap text-[14px] leading-[1.65] text-muted">
            {policy.notes.trim()}
          </p>
        </section>
      )}
    </div>
  );
}
