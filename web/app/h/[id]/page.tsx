import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";

import {
  loadAllHypotheses,
  loadHypothesis,
  loadRunArtifacts,
  parseSourceString,
  schoolPredictionsForHypothesis,
} from "@/lib/content";
import { hypothesisBibTex, hypothesisPermalink } from "@/lib/permalink";
import { absoluteUrl, githubCommitUrl } from "@/lib/site";
import { Badge } from "@/components/badges/Badge";
import { PreRegStrip } from "@/components/cards/PreRegStrip";
import { FalsificationCard } from "@/components/cards/FalsificationCard";
import { SteelmanBlock } from "@/components/cards/SteelmanBlock";
import { CiteBlock } from "@/components/cards/CiteBlock";
import { ResultBanner } from "@/components/cards/ResultBanner";
import { PolicyBriefCard } from "@/components/cards/PolicyBriefCard";
import { HypothesisChart } from "@/components/charts/HypothesisChart";

export async function generateStaticParams() {
  const all = await loadAllHypotheses();
  return all.map((h) => ({ id: h.hypothesis_id }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const h = await loadHypothesis(id);
  if (!h) return { title: id };
  const run = await loadRunArtifacts(id);
  const claimShort = h.claim.split(/(?<=[.!?])\s+/)[0].slice(0, 72);
  const verdictWord = (run.verdict ?? "pending").split(/[\s—–-]/)[0];
  const title = `${claimShort} — ${verdictWord}`;
  const description = [
    run.verdict ? `Verdict: ${run.verdict.split("\n")[0].slice(0, 120)}.` : null,
    h.claim.slice(0, 160),
  ]
    .filter(Boolean)
    .join(" ");
  const url = absoluteUrl(hypothesisPermalink(h));
  return {
    title,
    description,
    alternates: { canonical: url },
    openGraph: {
      title,
      description,
      url,
      type: "article",
      siteName: "IESET",
    },
    twitter: {
      card: "summary",
      title,
      description,
    },
  };
}

export default async function HypothesisPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const h = await loadHypothesis(id);
  if (!h) return notFound();

  const run = await loadRunArtifacts(id);
  const schoolPredictions = await schoolPredictionsForHypothesis(id);

  const outcomeVars = h.variables?.outcome ?? [];
  const treatmentVars = h.variables?.treatment ?? [];
  const channelVars = h.variables?.decomposition_channels ?? [];
  const controlVars = h.variables?.controls ?? [];

  const varRows = [
    ...outcomeVars.map((v) => ({ ...v, role: "outcome" })),
    ...treatmentVars.map((v) => ({ ...v, role: "treatment" })),
    ...channelVars.map((v) => ({ ...v, role: "channel" })),
    ...controlVars.map((v) => ({ ...v, role: "control" })),
  ];

  const varRowsWithTokens = await Promise.all(
    varRows.map(async (v) => ({ ...v, tokens: await parseSourceString(v.source) }))
  );

  const permalinkAbsolute = absoluteUrl(hypothesisPermalink(h));
  const bibtex = hypothesisBibTex(h);

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "ScholarlyArticle",
    headline: h.claim.split(/(?<=[.!?])\s+/)[0],
    abstract: [
      run.verdict ? `Verdict: ${String(run.verdict).split("\n")[0]}.` : null,
      "Pre-registered falsification rule with pinned public-data vintages.",
      "Research artifact — not peer-reviewed by default.",
    ]
      .filter(Boolean)
      .join(" "),
    datePublished: h._first_commit?.iso?.slice(0, 10),
    dateModified: run.generated_at?.slice(0, 10) ?? h._first_commit?.iso?.slice(0, 10),
    author: { "@type": "Organization", name: "IESET" },
    license: "https://creativecommons.org/licenses/by/4.0/",
    url: permalinkAbsolute,
    identifier: h._first_commit?.hash
      ? {
          "@type": "PropertyValue",
          propertyID: "git-commit",
          value: h._first_commit.hash,
          url: githubCommitUrl(h._first_commit.hash),
        }
      : undefined,
    isPartOf: {
      "@type": "WebSite",
      name: "IESET",
      url: absoluteUrl("/"),
    },
  };

  // Plain-English first line — the one-sentence version of the claim
  const claimSentences = h.claim.split(/(?<=[.!?])\s+/);
  const firstSentence = claimSentences[0];
  const restOfClaim = claimSentences.slice(1).join(" ").trim();

  return (
    <div className="mx-auto max-w-content px-8">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      {/* ---------- HEADER: minimal, just the claim + topic crumb ---------- */}
      <header className="pt-8 pb-4">
        <div className="mb-3 flex items-center gap-3 text-[13px] text-muted">
          <Link href="/h" className="text-muted hover:text-ink hover:no-underline">
            Hypotheses
          </Link>
          <span>·</span>
          <span className="capitalize">{h.topic.replace(/_/g, " ")}</span>
          <span>·</span>
          <span className="font-mono text-[11px] text-faint">{h.hypothesis_id}</span>
        </div>
        <h1 className="m-0 max-w-[900px] text-[30px] font-semibold leading-[1.15] tracking-[-0.02em] text-ink md:text-[34px]">
          {firstSentence}
        </h1>
        {restOfClaim && (
          <p className="mt-4 max-w-[780px] text-[17px] leading-[1.55] text-muted">
            {restOfClaim}
          </p>
        )}
      </header>

      {/* ---------- RESULT BANNER: verdict first, above the fold ---------- */}
      <ResultBanner run={run} />

      {/* ---------- PLAIN-ENGLISH POLICY BRIEF ---------- */}
      <PolicyBriefCard hypothesis={h} run={run} variables={varRows} />

      {/* ---------- CHART SECTION ---------- */}
      <section className="mb-10">
        <div className="mb-3 flex items-baseline justify-between">
          <h2 className="m-0 text-xs font-semibold uppercase tracking-wider text-muted">
            {run.exists ? "Results" : "Registered outcome variables"}
          </h2>
          {run.run_dir_rel && (
            <span className="font-mono text-[11px] text-faint">
              {run.run_dir_rel}
            </span>
          )}
        </div>
        <HypothesisChart hypothesis={h} />
      </section>

      {/* ---------- SCHOOLS PREDICTING ON THIS HYPOTHESIS ---------- */}
      {schoolPredictions.length > 0 && (
        <section className="mb-10">
          <div className="mb-3">
            <h2 className="m-0 text-xs font-semibold uppercase tracking-wider text-muted">
              Who has skin in the game — schools predicting on this
            </h2>
            <p className="mt-2 max-w-[780px] text-[13px] text-muted">
              {schoolPredictions.length === 1
                ? "1 school"
                : `${schoolPredictions.length} schools`}{" "}
              list this hypothesis as a test of their position. The chips below
              are school-level scoreboard outcomes, not a second hypothesis
              verdict.
            </p>
          </div>
          <div className="mb-3 rounded border-l-[3px] border-amber bg-[#fff8e8] px-4 py-3 text-[13px] leading-[1.55] text-ink">
            <div className="sc mb-1 text-[10px] font-semibold tracking-[0.1em] text-amber">
              hypothesis verdict vs scoreboard outcome
            </div>
            <p className="m-0">
              The banner verdict judges this hypothesis as written. The
              scoreboard asks whether each school&apos;s polarity-corrected
              prediction was right. Raw status is not a school win:{" "}
              <code className="font-mono text-[12px]">SUPPORTED</code> supports
              schools that needed <code className="font-mono text-[12px]">SUPPORTED</code>,
              but refutes schools that needed{" "}
              <code className="font-mono text-[12px]">REFUTED</code>.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {schoolPredictions.map((sp) => {
              const v = (run.verdict ?? "").toLowerCase();
              let tone: "green" | "red" | "amber" | "muted" = "muted";
              if (run.exists && run.verdict) {
                const supported = v.startsWith("supported");
                const refuted =
                  v.startsWith("refuted") ||
                  v.startsWith("not supported") ||
                  v.startsWith("not_supported");
                const partial =
                  v.startsWith("partial") ||
                  v.startsWith("mixed") ||
                  v.startsWith("weakly");
                const inconclusive =
                  v.startsWith("inconclusive") || v.startsWith("weakened");
                if (inconclusive) tone = "amber";
                else if (sp.expected_verdict === "supported") {
                  tone = supported ? "green" : refuted ? "red" : partial ? "amber" : "muted";
                } else if (sp.expected_verdict === "falsified") {
                  tone = refuted ? "green" : supported ? "red" : partial ? "amber" : "muted";
                } else {
                  tone = "amber";
                }
              }
              const toneClass =
                tone === "green"
                  ? "border-green bg-[#dff1e4] text-[#2c7a4f]"
                  : tone === "red"
                  ? "border-red bg-[#f3d9d9] text-[#9e2f2f]"
                  : tone === "amber"
                  ? "border-amber bg-[#fdf1da] text-[#b7791f]"
                  : "border-rule bg-white text-muted";
              const expectedVerdictLabel =
                sp.expected_verdict === "supported"
                  ? "SUPPORTED"
                  : sp.expected_verdict === "falsified"
                  ? "REFUTED"
                  : "MIXED";
              const schoolOutcomeLabel =
                !run.exists || !run.verdict
                  ? "scoreboard pending"
                  : tone === "green"
                  ? "school supported"
                  : tone === "red"
                  ? "school refuted"
                  : tone === "amber"
                  ? "partial/no-call"
                  : "scoreboard no-call";
              return (
                <Link
                  key={sp.position_id}
                  href={`/pos/${sp.position_id}`}
                  className={`group inline-flex items-center gap-2 rounded border px-3 py-1.5 text-[13px] hover:no-underline ${toneClass}`}
                  title={`School wins if this hypothesis is ${expectedVerdictLabel}; current school-level outcome: ${schoolOutcomeLabel}${sp.polarity === "inverted" ? " (polarity-inverted)" : ""}`}
                >
                  <span className="font-medium">{sp.school}</span>
                  <span className="text-[10.5px] uppercase tracking-wider opacity-75">
                    wins if {expectedVerdictLabel}
                  </span>
                  <span className="inline-flex items-center rounded-sm bg-white/60 px-1.5 py-[2px] text-[9.5px] font-semibold uppercase tracking-wider opacity-90">
                    {schoolOutcomeLabel}
                  </span>
                  {sp.polarity === "inverted" && (
                    <span
                      className="inline-flex items-center rounded-sm bg-white/60 px-1 font-mono text-[9.5px]"
                      title="School's narrative claim is opposite-signed to the hypothesis's recorded claim — verdict has been flipped accordingly"
                    >
                      ⇄
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        </section>
      )}

      {/* ---------- TWO-COLUMN: prose + rail ---------- */}
      <div className="grid grid-cols-1 gap-16 py-4 md:grid-cols-[minmax(0,1fr)_280px]">
        <main className="min-w-0">
          {/* Pre-registration */}
          <section className="mb-10">
            <SectionHeader>Pre-registration</SectionHeader>
            <PreRegStrip hypothesis={h} run={run} />
            <p className="text-[15px] leading-[1.65] text-ink">{h.claim.trim()}</p>
          </section>

          {/* Falsification — the framework's load-bearing feature */}
          <section className="mb-10">
            <SectionHeader>Falsification criterion — what would disprove this</SectionHeader>
            <FalsificationCard hypothesis={h} />
          </section>

          {/* Method */}
          {h.estimator && (
            <section className="mb-10">
              <SectionHeader>Method</SectionHeader>
              <dl className="grid grid-cols-[160px_1fr] gap-x-5 gap-y-2.5 text-sm">
                <dt className="text-muted">Template</dt>
                <dd><code>{h.estimator.template}</code></dd>
                {h.estimator.fixed_effects && (
                  <>
                    <dt className="text-muted">Fixed effects</dt>
                    <dd><code>{h.estimator.fixed_effects.join(", ")}</code></dd>
                  </>
                )}
                {h.estimator.clustering && (
                  <>
                    <dt className="text-muted">Clustering</dt>
                    <dd><code>{h.estimator.clustering}</code></dd>
                  </>
                )}
                {h.sample && (
                  <>
                    <dt className="text-muted">Sample</dt>
                    <dd>
                      {h.sample.countries.length} countries · {h.sample.period[0]} – {h.sample.period[1]}
                    </dd>
                  </>
                )}
                <dt className="text-muted">Evidence type</dt>
                <dd className="capitalize">{h.evidence_type ?? "—"}</dd>
              </dl>
              {h.estimator.notes && (
                <p className="mt-4 whitespace-pre-wrap text-[14px] leading-[1.65] text-muted">
                  {h.estimator.notes.trim()}
                </p>
              )}
            </section>
          )}

          {/* Data */}
          {varRowsWithTokens.length > 0 && (
            <section className="mb-10">
              <SectionHeader>Data</SectionHeader>
              <table className="w-full border-collapse text-[13.5px]">
                <thead>
                  <tr>
                    <th className="w-[35%] border-b border-rule p-2 text-left text-[11px] font-semibold uppercase tracking-wider text-muted">
                      Variable
                    </th>
                    <th className="border-b border-rule p-2 text-left text-[11px] font-semibold uppercase tracking-wider text-muted">
                      Source
                    </th>
                    <th className="w-[22%] border-b border-rule p-2 text-left text-[11px] font-semibold uppercase tracking-wider text-muted">
                      Transform
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {varRowsWithTokens.map((v, i) => (
                    <tr key={v.name + i}>
                      <td className="border-b border-rule p-2 align-top">
                        <div className="font-mono text-[12.5px] text-ink">{v.name}</div>
                        <div className="sc mt-0.5 text-[10px]">{v.role}</div>
                      </td>
                      <td className="border-b border-rule p-2 align-top">
                        {v.tokens.length === 0 && (
                          <span className="text-xs text-muted">{v.source ?? "—"}</span>
                        )}
                        {v.tokens.map((t, ti) => (
                          <div key={ti} className="mb-1 last:mb-0">
                            <SourceTokenBadge token={t} />
                          </div>
                        ))}
                      </td>
                      <td className="border-b border-rule p-2 align-top font-mono text-[12px] text-muted">
                        {v.transformation ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="sc mt-3 text-[10px]">
                <span className="text-green">●</span> ready &nbsp;·&nbsp;
                <span className="text-amber">●</span> pending &nbsp;·&nbsp;
                <span className="text-red">●</span> reconstruct-needed
              </p>
            </section>
          )}

          {/* Result card rendered inline when a run exists */}
          {run.result_card_html && (
            <section className="mb-10">
              <SectionHeader>Detailed result card</SectionHeader>
              <div
                className="prose-body rounded border border-rule bg-white p-6"
                dangerouslySetInnerHTML={{ __html: run.result_card_html }}
              />
            </section>
          )}

          {/* Steelman */}
          {h._steelman_html && (
            <section className="mb-10">
              <SectionHeader>Strongest opposing argument</SectionHeader>
              <p className="mb-3 text-[14px] text-muted">
                Every hypothesis ships with its charitable opposing argument. The framework
                earns credibility by handling objections at their strongest, not weakest.
              </p>
              <SteelmanBlock html={h._steelman_html} sourcePath={h.steelman} />
            </section>
          )}

          {/* Notes */}
          {h.notes && (
            <section className="mb-10">
              <SectionHeader>Notes</SectionHeader>
              <p className="whitespace-pre-wrap text-[14px] leading-[1.65] text-muted">
                {h.notes.trim()}
              </p>
            </section>
          )}
        </main>

        {/* RAIL */}
        <aside className="self-start md:sticky md:top-[68px]">
          <div className="mb-3 rounded border border-rule bg-white p-4">
            <h3 className="sc mb-3 text-[10px]">Quick facts</h3>
            <dl className="grid grid-cols-[80px_1fr] gap-x-4 gap-y-2.5 text-[12.5px]">
              <dt className="text-muted">Status</dt>
              <dd>
                {h.status === "pre_registered" && <Badge variant="green" dot>pre-reg</Badge>}
                {h.status === "candidate" && <Badge variant="amber" dot>candidate</Badge>}
                {h.status === "draft" && <Badge variant="muted" dot>draft</Badge>}
              </dd>
              <dt className="text-muted">Topic</dt>
              <dd className="capitalize">{h.topic.replace(/_/g, " ")}</dd>
              {h.evidence_type && (
                <>
                  <dt className="text-muted">Evidence</dt>
                  <dd className="capitalize">{h.evidence_type}</dd>
                </>
              )}
              {h.sample && (
                <>
                  <dt className="text-muted">Sample</dt>
                  <dd>
                    {h.sample.countries.length} countries<br />
                    <span className="text-muted">{h.sample.period[0]}–{h.sample.period[1]}</span>
                  </dd>
                </>
              )}
              {run.exists && (
                <>
                  <dt className="text-muted">Run</dt>
                  <dd>
                    <Badge variant="green" dot>yes</Badge>
                  </dd>
                </>
              )}
            </dl>
          </div>

          <CiteBlock permalink={permalinkAbsolute} bibtex={bibtex} />

          {(h.linked_hypotheses?.length || h.linked_conditions?.length) && (
            <div className="mb-3 rounded border border-rule bg-white p-4">
              <h3 className="sc mb-3 text-[10px]">Linked</h3>
              {h.linked_hypotheses && h.linked_hypotheses.length > 0 && (
                <>
                  <div className="sc mb-1.5 text-[10px]">Hypotheses</div>
                  <ul className="m-0 mb-3 list-none space-y-1.5 p-0 text-[12px]">
                    {h.linked_hypotheses.map((id) => (
                      <li key={id}>
                        <Link href={`/h/${id}`} className="font-mono text-[11.5px]">
                          {id}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </>
              )}
              {h.linked_conditions && h.linked_conditions.length > 0 && (
                <>
                  <div className="sc mb-1.5 text-[10px]">Conditions</div>
                  <ul className="m-0 list-none space-y-1.5 p-0 text-[12px]">
                    {h.linked_conditions.map((id) => (
                      <li key={id}>
                        <Link href={`/c/${id}`} className="font-mono text-[11.5px]">
                          {id}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          )}

          <div className="mb-3 rounded border border-rule bg-white p-4">
            <h3 className="sc mb-3 text-[10px]">Found an issue?</h3>
            <p className="mb-3 text-[12px] text-muted">
              No bounty programme is currently active. Accepted challenges are
              credited unless the contributor requests anonymity; payment
              applies only to a separately published, pre-funded bounty round.
            </p>
            <a
              href="/contribute"
              className="block rounded border border-accent bg-accent px-3 py-2 text-center text-[12.5px] font-medium text-white hover:bg-[#183e61] hover:no-underline"
            >
              Submit a challenge
            </a>
          </div>
        </aside>
      </div>
      <div className="border-t border-rule py-5 text-center text-[11.5px] text-faint">
        Authored framework.{" "}
        <Link href="/disclosure" className="text-muted hover:text-ink">
          Read the transparency note
        </Link>
        .
      </div>
    </div>
  );
}

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="mb-4 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
      {children}
    </h2>
  );
}

function SourceTokenBadge({ token }: { token: Awaited<ReturnType<typeof parseSourceString>>[number] }) {
  const dotColor =
    token.status === "ready" ? "#2c7a4f"
    : token.status === "pending" ? "#b7791f"
    : token.status === "gap" ? "#9e2f2f"
    : "#636363";
  return (
    <span className="inline-flex items-center rounded bg-code-bg px-1.5 py-[2px] font-mono text-[11.5px]">
      <span
        className="mr-1 inline-block h-[7px] w-[7px] rounded-full"
        style={{ background: dotColor }}
      />
      {token.publisher}:{token.series}
      <span className="ml-2 font-sans text-[10px] text-faint">
        tier {token.credibility_tier}
      </span>
    </span>
  );
}
