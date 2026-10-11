import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { loadEvidenceTierAudit, REPO_ROOT } from "./content";
import { publicationHeldIds, publicationHoldCounts } from "./publication-holds";

export interface PublicCorpusCensus {
  schema_version: number;
  generated_utc?: string;
  counts: {
    hypothesis_specs: number;
    run_directories: number;
    result_card_files: number;
    policies: number;
    movements: number;
    positions: number;
    ranked_schools?: number;
    benchmark_controls?: number;
    conditional_entries: number;
    review_submissions: number;
    completed_review_logs: number;
    public_visible_results?: number;
    featured_evidence?: number;
    calibration_evidence?: number;
    archive_records?: number;
    reference_set?: number;
    publication_rights_held_records?: number;
    publication_rights_held_evidence_qualified?: number;
  };
  definitions?: Record<string, string>;
  verdict_counts?: Record<string, number>;
  registration_counts?: Record<string, number>;
  estimator_floor_failure_counts?: Record<string, number>;
  evidence_exclusion_counts?: Record<string, number>;
}

/**
 * Single source of truth for public counters.
 * Written by CI / census scripts to engine/public_corpus_census.json.
 */
export function loadPublicCensus(): PublicCorpusCensus | null {
  const path = join(REPO_ROOT, "engine", "public_corpus_census.json");
  if (!existsSync(path)) return null;
  try {
    const source = JSON.parse(readFileSync(path, "utf8")) as PublicCorpusCensus;
    const audit = loadEvidenceTierAudit();
    if (!audit) throw new Error("Published census requires the evidence audit");

    let heldRuns = 0;
    let heldCards = 0;
    const verdictCounts = { ...source.verdict_counts };
    for (const id of publicationHeldIds()) {
      const runPath = join(REPO_ROOT, "engine", "runs", id);
      if (existsSync(runPath)) heldRuns++;
      const cardPath = join(runPath, "result_card.md");
      if (!existsSync(cardPath)) continue;
      heldCards++;
      const card = readFileSync(cardPath, "utf8");
      const match = card.match(/^(?:\*\*)?verdict:?(?:\*\*)?:?\s*(.+)$/im);
      const value = match?.[1]?.trim().toLowerCase().replace(/^[*_`]+/, "") ?? "missing";
      const bucket = value.startsWith("supported_subset")
        ? "supported_subset"
        : value.startsWith("inconclusive_data_pending")
          ? "inconclusive_data_pending"
          : value.split(/[^a-z_]+/, 1)[0] || "missing";
      if (!verdictCounts[bucket]) throw new Error(`Missing held verdict bucket: ${bucket}`);
      verdictCounts[bucket]--;
      if (verdictCounts[bucket] === 0) delete verdictCounts[bucket];
    }

    return {
      ...source,
      counts: {
        ...source.counts,
        hypothesis_specs: audit.summary.hypotheses,
        run_directories: source.counts.run_directories - heldRuns,
        result_card_files: source.counts.result_card_files - heldCards,
        public_visible_results: audit.summary.public_visible,
        featured_evidence: audit.summary.tier_counts.featured ?? 0,
        calibration_evidence: audit.summary.tier_counts.calibration ?? 0,
        archive_records: audit.summary.tier_counts.archive ?? 0,
        reference_set: audit.summary.reference_set,
        publication_rights_held_records: publicationHoldCounts.records,
        publication_rights_held_evidence_qualified: publicationHoldCounts.evidenceQualified,
      },
      definitions: {
        ...source.definitions,
        hypothesis_specs: "Hypothesis specs available in the published site, excluding source-rights holds.",
        run_directories: "Result runs available in the published site, excluding source-rights holds.",
        result_card_files: "Result cards available in the published site, excluding source-rights holds.",
        public_visible_results: "Evidence-qualified results available in the published site; source-rights holds are counted separately.",
        publication_rights_held_records: "Research records held from publication during publisher-rights review; evidence grades are unchanged.",
        publication_rights_held_evidence_qualified: "Evidence-qualified records held from publication during publisher-rights review.",
      },
      verdict_counts: verdictCounts,
      registration_counts: audit.summary.registration_counts,
      estimator_floor_failure_counts: audit.summary.estimator_floor_failures,
      evidence_exclusion_counts: audit.summary.exclusion_counts,
    };
  } catch {
    return null;
  }
}
