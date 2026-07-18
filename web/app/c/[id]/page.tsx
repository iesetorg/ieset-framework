import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";

import { loadAllConditions, loadCondition } from "@/lib/content";
import { loadConditionEvidence } from "@/lib/condition-evidence";
import { Badge } from "@/components/badges/Badge";
import type {
  Condition,
  ConditionCase,
  ConditionConfidence,
} from "@/lib/types";
import type { ConditionEvidenceLink } from "@/lib/condition-evidence";

export async function generateStaticParams() {
  const all = await loadAllConditions();
  return all.map((c) => ({ id: c.id }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const c = await loadCondition(id);
  if (!c) return { title: id };
  return {
    title: humanName(c.id),
    description: c.description.slice(0, 200),
    alternates: {
      canonical: `https://framework.ieset.org/c/${encodeURIComponent(id)}/`,
    },
  };
}

export default async function ConditionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [c, evidence] = await Promise.all([
    loadCondition(id),
    loadConditionEvidence(id),
  ]);
  if (!c) return notFound();

  const features = c.institutional_features_that_make_the_model_work ?? {};
  const featureKeys = Object.keys(features);

  return (
    <div className="mx-auto max-w-content px-8">
      {/* Header */}
      <div className="border-b border-rule py-8">
        <div className="mb-3 text-[13px] text-muted">
          <Link href="/c" className="text-muted hover:text-ink hover:no-underline">
            Conditions
          </Link>{" "}
          &rsaquo;{" "}
          <span>{categoryLabel(c.category)}</span>
        </div>

        <h1 className="mb-3.5 text-[34px] font-semibold leading-tight tracking-[-0.02em] text-ink">
          {humanName(c.id)}
        </h1>

        <p className="mb-5 max-w-[780px] whitespace-pre-wrap text-[18px] leading-relaxed text-muted">
          {c.description.trim()}
        </p>

        <div className="flex flex-wrap items-center gap-x-6 gap-y-3 text-[13px] text-muted">
          <Badge variant={confidenceVariant(c.confidence)} dot>
            confidence: {c.confidence.replace(/_/g, " ")}
          </Badge>
          <Badge variant="muted">{categoryLabel(c.category)}</Badge>
          {c._first_commit && (
            <span className="text-[12.5px] text-faint">
              entry added {c._first_commit.iso.slice(0, 10)}
            </span>
          )}
          <span className="font-mono text-xs text-muted">{c.id}</span>
        </div>
      </div>

      {/* Body */}
      <div className="grid grid-cols-1 gap-14 py-10 md:grid-cols-[minmax(0,1fr)_260px]">
        <main>
          {featureKeys.length > 0 && (
            <section className="mb-10">
              <SectionHeader>
                Institutional features that make the model work
              </SectionHeader>
              <div className="divide-y divide-rule rounded border border-rule bg-white">
                {featureKeys.map((key) => (
                  <details
                    key={key}
                    className="group px-4 py-3"
                  >
                    <summary className="cursor-pointer list-none text-[15px] font-medium text-ink marker:hidden">
                      <span className="mr-2 inline-block text-muted group-open:rotate-90 transition-transform">
                        &rsaquo;
                      </span>
                      {humanLabel(key)}
                    </summary>
                    <div className="mt-3 whitespace-pre-wrap pl-5 text-[14.5px] leading-[1.65] text-ink">
                      {features[key].trim()}
                    </div>
                  </details>
                ))}
              </div>
            </section>
          )}

          {c.supporting_cases && c.supporting_cases.length > 0 && (
            <section className="mb-10">
              <SectionHeader>Supporting cases</SectionHeader>
              <CaseGrid cases={c.supporting_cases} tone="neutral" />
            </section>
          )}

          {c.failed_replications && c.failed_replications.length > 0 && (
            <section className="mb-10">
              <SectionHeader>Failed replications</SectionHeader>
              <CaseGrid cases={c.failed_replications} tone="amber" />
            </section>
          )}

          {c.disconfirming_cases && c.disconfirming_cases.length > 0 && (
            <section className="mb-10">
              <SectionHeader>Disconfirming cases</SectionHeader>
              <CaseGrid cases={c.disconfirming_cases} tone="red" />
            </section>
          )}

          {c.what_the_model_is_not && c.what_the_model_is_not.length > 0 && (
            <section className="mb-10">
              <SectionHeader>What this condition is NOT</SectionHeader>
              <ul className="list-disc space-y-2 pl-5 text-[15px] leading-[1.65]">
                {c.what_the_model_is_not.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </section>
          )}

          {c.policy_implications && (
            <section className="mb-10">
              <SectionHeader>Policy implications</SectionHeader>
              <p className="whitespace-pre-wrap text-[15px] leading-[1.65]">
                {c.policy_implications.trim()}
              </p>
            </section>
          )}

          <section className="mb-10">
            <SectionHeader>Framework position</SectionHeader>
            <p className="whitespace-pre-wrap text-[15px] leading-[1.65]">
              {c.framework_position.trim()}
            </p>
          </section>

          {c.sub_analyses && c.sub_analyses.length > 0 && (
            <section className="mb-10">
              <SectionHeader>Sub-analyses</SectionHeader>
              <div className="space-y-5">
                {c.sub_analyses.map((s) => (
                  <div
                    key={s.id}
                    className="rounded border border-rule bg-white p-4"
                  >
                    <div className="mb-1.5 font-mono text-[12px] text-faint">
                      {s.id}
                    </div>
                    <div className="mb-2 text-[14.5px] leading-[1.65]">
                      <strong className="font-semibold">Observation.</strong>{" "}
                      {s.observation.trim()}
                    </div>
                    <div className="text-[14.5px] leading-[1.65]">
                      <strong className="font-semibold">
                        Framework position.
                      </strong>{" "}
                      {s.framework_position.trim()}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
        </main>

        {/* Rail — lighter than hypothesis rail */}
        <aside className="self-start md:sticky md:top-20">
          <div className="mb-3.5 rounded border border-rule bg-white p-4">
            <h3 className="sc mb-3">Quick facts</h3>
            <dl className="grid grid-cols-[90px_1fr] gap-x-5 gap-y-2.5 text-[12.5px]">
              <dt className="text-muted">Confidence</dt>
              <dd>
                <Badge variant={confidenceVariant(c.confidence)} dot>
                  {c.confidence.replace(/_/g, " ")}
                </Badge>
              </dd>
              <dt className="text-muted">Category</dt>
              <dd>{categoryLabel(c.category)}</dd>
              <dt className="text-muted">Direct</dt>
              <dd>{evidence.direct_count}</dd>
              <dt className="text-muted">Related</dt>
              <dd>
                {evidence.related_count}
                {evidence.related_available_count > evidence.related_count && (
                  <span className="text-faint"> of {evidence.related_available_count}</span>
                )}
              </dd>
              <dt className="text-muted">Tested</dt>
              <dd>{evidence.tested_count}</dd>
              {c._first_commit && (
                <>
                  <dt className="text-muted">Added</dt>
                  <dd>{c._first_commit.iso.slice(0, 10)}</dd>
                </>
              )}
            </dl>
          </div>

          {(evidence.direct.length > 0 || evidence.related.length > 0) && (
            <div className="mb-3.5 rounded border border-rule bg-white p-4">
              <h3 className="sc mb-2">Evidence hypotheses</h3>
              <p className="mb-3 text-[12px] leading-[1.45] text-muted">
                Direct links are curated. Related links are labelled search
                matches for discovery, not scored links.
              </p>
              {evidence.direct.length > 0 && (
                <EvidenceList title="Direct" links={evidence.direct} />
              )}
              {evidence.related.length > 0 && (
                <EvidenceList title="Related" links={evidence.related} />
              )}
            </div>
          )}

          {c.linked_model_ids && c.linked_model_ids.length > 0 && (
            <div className="mb-3.5 rounded border border-rule bg-white p-4">
              <h3 className="sc mb-3">Linked model ids</h3>
              <ul className="m-0 list-none space-y-2 p-0 text-[12.5px]">
                {c.linked_model_ids.map((mid) => (
                  <li
                    key={mid}
                    className="font-mono text-[12px] text-muted"
                  >
                    {mid}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

function EvidenceList({
  title,
  links,
}: {
  title: string;
  links: ConditionEvidenceLink[];
}) {
  return (
    <div className="mb-4 last:mb-0">
      <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-muted">
        {title}
      </div>
      <ul className="m-0 list-none space-y-2 p-0 text-[12.5px]">
        {links.map((link) => (
          <li key={`${title}-${link.hypothesis_id}`} className="rounded border border-rule bg-panel p-2">
            <Link href={`/h/${link.hypothesis_id}`} className="font-mono text-[11.5px]">
              {link.hypothesis_id}
            </Link>
            <div className="mt-1 flex flex-wrap gap-1.5">
              <Badge variant={verdictVariant(link.verdict_tone)}>
                {link.verdict_label}
              </Badge>
              <Badge variant={link.source === "related" ? "accent" : "green"}>
                {sourceLabel(link.source)}
              </Badge>
            </div>
            <p className="mt-1.5 text-[12px] leading-[1.45] text-muted">
              {link.claim}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="mb-3.5 border-b border-rule pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
      {children}
    </h2>
  );
}

function CaseGrid({
  cases,
  tone,
}: {
  cases: ConditionCase[];
  tone: "neutral" | "amber" | "red";
}) {
  const toneClass =
    tone === "amber"
      ? "border-amber-soft bg-amber-soft/40"
      : tone === "red"
      ? "border-red-soft bg-red-soft/40"
      : "border-rule bg-white";
  return (
    <div className="grid grid-cols-1 gap-3.5 md:grid-cols-2">
      {cases.map((caseItem) => (
        <div
          key={caseItem.id}
          className={`rounded border p-4 ${toneClass}`}
        >
          <div className="mb-1.5 font-mono text-[12px] text-faint">
            {caseItem.id}
          </div>
          <p className="text-[14px] leading-[1.6]">
            {caseItem.description.trim()}
          </p>
          {caseItem.citations && caseItem.citations.length > 0 && (
            <ul className="mt-2 list-none space-y-1 p-0 text-[11.5px] text-muted">
              {caseItem.citations.map((cite, i) => (
                <li key={i}>{cite}</li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
}

function humanName(id: string): string {
  // "nordic_institutional_design" -> "Nordic institutional design"
  const words = id.replace(/_/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function humanLabel(key: string): string {
  // "cultural_and_social" -> "Cultural and social"
  const words = key.replace(/_/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function categoryLabel(cat: Condition["category"]): string {
  switch (cat) {
    case "conditions_favoring_markets":
      return "Conditions favoring markets";
    case "conditions_favoring_intervention":
      return "Conditions favoring intervention";
    case "conditions_with_distributional_considerations":
      return "Distributional considerations";
    case "conditions_specific_institutional_models":
      return "Specific institutional models";
  }
}

function confidenceVariant(
  c: ConditionConfidence
): "green" | "amber" | "muted" | "accent" {
  if (c === "high") return "green";
  if (c === "medium_high") return "accent";
  if (c === "medium") return "amber";
  return "muted";
}

function verdictVariant(tone: "green" | "amber" | "red" | "muted") {
  return tone;
}

function sourceLabel(source: ConditionEvidenceLink["source"]) {
  if (source === "curated") return "curated";
  if (source === "reverse") return "back-link";
  if (source === "model") return "model id";
  return "related";
}
