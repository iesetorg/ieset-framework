import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";

import { readFile, readdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join, resolve } from "node:path";
import yaml from "js-yaml";

import {
  loadAllHypotheses,
  loadAxes,
  loadRunArtifacts,
} from "@/lib/content";
import { AxisTile } from "@/components/cards/AxisTile";
import { Badge } from "@/components/badges/Badge";
import { verdictTone, verdictShort } from "@/lib/verdict";

interface Movement {
  movement_id: string;
  status: string;
  name: string;
  countries: string[];
  timeframe: { start: number; end: number | string; enacted_date?: string };
  coalition?: string;
  leaders?: string[];
  doctrine?: string;
  policies?: string[];
  axes_summary?: {
    axis: string;
    direction: string;
    magnitude?: string;
    rationale?: string;
  }[];
  outcome_hypotheses?: string[];
  position_alignments?: { position_id: string; alignment: string; notes?: string }[];
  steelman?: string;
  references?: string[];
  notes?: string;
}

const REPO_ROOT = resolve(process.cwd(), "..");

let _movementsCache: Promise<Movement[]> | null = null;
async function listMovements(): Promise<Movement[]> {
  if (_movementsCache) return _movementsCache;
  _movementsCache = (async () => {
    const dir = join(REPO_ROOT, "movements");
    if (!existsSync(dir)) return [];
    const entries = await readdir(dir);
    const out: Movement[] = [];
    for (const e of entries) {
      if (!e.endsWith(".yaml")) continue;
      const raw = await readFile(join(dir, e), "utf8");
      try {
        const doc = yaml.load(raw) as Movement;
        if (doc?.movement_id) out.push(doc);
      } catch {
        /* skip malformed YAML; logged via validate_specs.py */
      }
    }
    return out.sort((a, b) => a.movement_id.localeCompare(b.movement_id));
  })();
  return _movementsCache;
}

async function loadMovement(id: string): Promise<Movement | null> {
  const all = await listMovements();
  return all.find((m) => m.movement_id === id) ?? null;
}

export async function generateStaticParams() {
  const all = await listMovements();
  return all.map((m) => ({ id: m.movement_id }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const m = await loadMovement(id);
  if (!m) return { title: id };
  return {
    title: m.name,
    description: m.doctrine?.slice(0, 200),
    alternates: {
      canonical: `https://framework.ieset.org/m/${encodeURIComponent(id)}/`,
    },
  };
}

export default async function MovementPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const m = await loadMovement(id);
  if (!m) return notFound();

  const axesMap = await loadAxes();

  // Resolve outcome_hypotheses → their verdicts, for "what the data says"
  const allHyps = await loadAllHypotheses();
  const hypIds = new Set(allHyps.map((h) => h.hypothesis_id));
  const outcomeLinks: {
    id: string;
    exists: boolean;
    verdict?: string;
  }[] = [];
  for (const hid of m.outcome_hypotheses ?? []) {
    const exists = hypIds.has(hid);
    let verdict: string | undefined;
    if (exists) {
      const run = await loadRunArtifacts(hid);
      verdict = run.verdict;
    }
    outcomeLinks.push({ id: hid, exists, verdict });
  }

  const endLabel = m.timeframe.end === "ongoing" ? "present" : m.timeframe.end;

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <div className="mb-3 flex items-center gap-3 text-[13px] text-muted">
        <Link href="/m" className="text-muted hover:text-ink hover:no-underline">
          Movements
        </Link>
        <span>·</span>
        <span className="font-mono text-[11px] text-faint">{m.movement_id}</span>
      </div>
      <h1 className="m-0 mb-3 text-[36px] font-semibold leading-[1.15] tracking-[-0.02em]">
        {m.name}
      </h1>
      <div className="mb-6 flex flex-wrap items-center gap-4 text-[14px] text-muted">
        <span>
          <strong className="text-ink">{m.countries.join(", ")}</strong>
        </span>
        <span>·</span>
        <span>
          <strong className="text-ink">{m.timeframe.start}</strong> – {endLabel}
        </span>
        {m.coalition && (
          <>
            <span>·</span>
            <span>{m.coalition}</span>
          </>
        )}
      </div>

      {m.leaders && m.leaders.length > 0 && (
        <div className="mb-3 text-[13px] text-muted">
          <span className="font-semibold">Leaders: </span>
          {m.leaders.join(" · ")}
        </div>
      )}

      {/* LINKED POSITIONS BYLINE — at-a-glance which schools aligned/opposed */}
      {m.position_alignments && m.position_alignments.length > 0 && (
        <div className="mb-6 flex flex-wrap items-center gap-1.5 text-[13px]">
          <span className="sc mr-1 text-[10px] text-muted">positions</span>
          {m.position_alignments.map((a) => {
            const tone =
              a.alignment === "aligned"
                ? { bg: "#dff1e4", fg: "#2c7a4f", ring: "#bcdcc4" }
                : a.alignment === "partially_aligned"
                ? { bg: "#fdf1da", fg: "#b7791f", ring: "#ecd6a6" }
                : a.alignment === "opposed"
                ? { bg: "#f3d9d9", fg: "#9e2f2f", ring: "#e3b6b6" }
                : { bg: "#f3f3f1", fg: "#636363", ring: "#dcdad4" };
            const glyph =
              a.alignment === "aligned"
                ? "✓"
                : a.alignment === "opposed"
                ? "✗"
                : a.alignment === "partially_aligned"
                ? "~"
                : "·";
            return (
              <Link
                key={a.position_id}
                href={`/pos/${a.position_id}`}
                className="inline-flex items-center gap-1.5 rounded px-1.5 py-[2px] text-[12px] font-medium leading-snug ring-1 ring-inset hover:no-underline"
                style={{ background: tone.bg, color: tone.fg, borderColor: tone.ring }}
                title={a.notes ?? a.alignment}
              >
                <span
                  className="inline-flex h-[14px] w-[14px] items-center justify-center rounded-sm text-[10px] font-bold leading-none"
                  style={{ background: tone.fg, color: tone.bg }}
                  aria-hidden
                >
                  {glyph}
                </span>
                <span className="font-mono text-[11.5px]">{a.position_id}</span>
              </Link>
            );
          })}
        </div>
      )}

      {/* DOCTRINE */}
      {m.doctrine && (
        <section className="mb-8 rounded border border-rule bg-white p-5">
          <h2 className="m-0 mb-3 text-xs font-semibold uppercase tracking-wider text-muted">
            Doctrine — stated goals and content
          </h2>
          <p className="m-0 whitespace-pre-wrap text-[15px] leading-[1.65] text-ink">
            {m.doctrine.trim()}
          </p>
        </section>
      )}

      {/* AXES MOVED */}
      {m.axes_summary && m.axes_summary.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-4 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Policy-content fingerprint — how the framework codes this movement on its axes
          </h2>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {m.axes_summary.map((a, i) => (
              <AxisTile key={i} move={a} axisDef={axesMap[a.axis]} />
            ))}
          </div>
        </section>
      )}

      {/* POLICIES */}
      {m.policies && m.policies.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-4 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Policies enacted
          </h2>
          <ul className="space-y-1.5 text-[13.5px]">
            {m.policies.map((p) => (
              <li key={p} className="font-mono text-[12px] text-muted">
                · {p}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* OUTCOMES — live verdicts from linked hypotheses */}
      {outcomeLinks.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-4 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            What the data says — linked outcome hypotheses
          </h2>
          <p className="mb-3 text-[13.5px] text-muted">
            The movement&apos;s outcome claims are tied to these hypotheses. Verdicts
            update as models run.
          </p>
          <div className="space-y-2">
            {outcomeLinks.map((o) => (
              <div
                key={o.id}
                className="flex items-start gap-3 rounded border border-rule bg-white p-3"
              >
                {o.verdict ? (
                  verdictBadge(o.verdict)
                ) : o.exists ? (
                  <Badge variant="muted" dot>
                    run pending
                  </Badge>
                ) : (
                  <Badge variant="muted">not yet written</Badge>
                )}
                <div className="flex-1 min-w-0">
                  {o.exists ? (
                    <Link
                      href={`/h/${o.id}`}
                      className="font-mono text-[12px] text-ink hover:underline"
                    >
                      {o.id}
                    </Link>
                  ) : (
                    <span className="font-mono text-[12px] text-faint">
                      {o.id}
                    </span>
                  )}
                  {o.verdict && (
                    <div className="mt-1 text-[12.5px] leading-[1.5] text-muted">
                      {o.verdict}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* POSITION ALIGNMENTS — which schools predicted what */}
      {m.position_alignments && m.position_alignments.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-4 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Schools of thought aligned or opposed
          </h2>
          <div className="space-y-2">
            {m.position_alignments.map((a, i) => (
              <div
                key={i}
                className="flex items-start gap-3 rounded border border-rule bg-white p-3"
              >
                {a.alignment === "aligned" && (
                  <Badge variant="green">aligned</Badge>
                )}
                {a.alignment === "partially_aligned" && (
                  <Badge variant="amber">partial</Badge>
                )}
                {a.alignment === "opposed" && (
                  <Badge variant="red">opposed</Badge>
                )}
                <div className="flex-1">
                  <Link
                    href={`/pos/${a.position_id}`}
                    className="font-mono text-[12px] text-ink hover:underline"
                  >
                    {a.position_id}
                  </Link>
                  {a.notes && (
                    <div className="mt-0.5 text-[12.5px] text-muted">
                      {a.notes}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* REFERENCES */}
      {m.references && m.references.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-4 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            References
          </h2>
          <ul className="list-disc pl-5 text-[13.5px] leading-[1.55] text-muted">
            {m.references.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </section>
      )}

      {m.notes && (
        <section className="mb-8">
          <h2 className="mb-4 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            Notes
          </h2>
          <p className="whitespace-pre-wrap text-[13.5px] leading-[1.65] text-muted">
            {m.notes.trim()}
          </p>
        </section>
      )}
    </div>
  );
}

function verdictBadge(verdict: string) {
  const tone = verdictTone(verdict);
  const label = verdictShort(verdict);
  if (tone === "green") return <Badge variant="green" dot>{label}</Badge>;
  if (tone === "red") return <Badge variant="red" dot>{label}</Badge>;
  if (tone === "amber") return <Badge variant="amber" dot>{label}</Badge>;
  return <Badge variant="muted" dot>{label}</Badge>;
}
