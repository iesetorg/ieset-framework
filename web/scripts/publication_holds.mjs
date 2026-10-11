import { existsSync, lstatSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const REPO_ROOT = resolve(fileURLToPath(new URL("../../", import.meta.url)));

function hasEntry(path) {
  try {
    lstatSync(path);
    return true;
  } catch (error) {
    if (error.code === "ENOENT") return false;
    throw error;
  }
}

export function loadPublicationHolds(repoRoot) {
  const path = join(repoRoot, "engine", "publication_rights_holds.json");
  const registry = JSON.parse(readFileSync(path, "utf8"));
  if (registry.schema !== "ieset-publication-rights-holds-v1" ||
      registry.status !== "active_publication_hold" || !Array.isArray(registry.groups)) {
    throw new Error("Invalid publication-rights hold registry");
  }
  const ids = new Set();
  let evidenceQualified = 0;
  for (const group of registry.groups) {
    if (!group.source || !Array.isArray(group.hypothesis_ids) ||
        group.hypothesis_ids.length !== group.count ||
        !Number.isInteger(group.currently_public) ||
        group.currently_public < 0 || group.currently_public > group.count) {
      throw new Error(`Invalid publication-rights hold group: ${group.source ?? "unknown"}`);
    }
    evidenceQualified += group.currently_public;
    for (const id of group.hypothesis_ids) {
      if (typeof id !== "string" || !/^[a-z0-9_]+$/.test(id) || ids.has(id)) {
        throw new Error(`Duplicate or invalid publication-rights hold ID: ${id}`);
      }
      ids.add(id);
    }
  }
  return { ids, evidenceQualified };
}

function counts(values) {
  const tally = {};
  for (const value of values) tally[value] = (tally[value] ?? 0) + 1;
  return tally;
}

export function projectEvidenceAudit(source, holds, repoRoot = REPO_ROOT) {
  const original = new Map(source.records.map((record) => [record.hypothesis_id, record]));
  for (const id of holds.ids) {
    if (!original.has(id)) throw new Error(`Publication hold ID missing from evidence audit: ${id}`);
  }
  const heldPublic = [...holds.ids].filter((id) => original.get(id).public_visible).length;
  const publicProjection = heldPublic === 0 && [...holds.ids].every((id) => {
    const runPath = join(repoRoot, "engine", "runs", id);
    return original.get(id).registration_status === "registered_no_run" &&
      !hasEntry(runPath) && !hasEntry(join(runPath, "result_card.md"));
  });
  if (heldPublic !== holds.evidenceQualified && !publicProjection) {
    throw new Error(`Publication hold source is neither the private evidence audit nor a run-free public projection: registry ${holds.evidenceQualified}, audit ${heldPublic}`);
  }
  const records = source.records.filter((record) => !holds.ids.has(record.hypothesis_id));
  return {
    ...source,
    records,
    reference_set: source.reference_set.filter((row) => !holds.ids.has(row.hypothesis_id)),
    summary: {
      ...source.summary,
      hypotheses: records.length,
      public_visible: records.filter((record) => record.public_visible).length,
      reference_set: records.filter((record) => record.reference_set).length,
      tier_counts: counts(records.map((record) => record.tier)),
      registration_counts: counts(records.map((record) => record.registration_status)),
      verdict_counts: counts(records.map((record) => record.verdict_bucket)),
      estimator_floor_failures: counts(records.flatMap((record) => record.estimator_floor_failures)),
      exclusion_counts: counts(records.flatMap((record) => record.exclusion_reasons)),
    },
  };
}

function cardVerdictBucket(text) {
  const match = text.match(/^(?:\*\*)?verdict:?(?:\*\*)?:?\s*(.+)$/im);
  if (!match) return "missing";
  const value = match[1].trim().toLowerCase().replace(/^[*_`]+/, "");
  if (value.startsWith("supported_subset")) return "supported_subset";
  if (value.startsWith("inconclusive_data_pending")) return "inconclusive_data_pending";
  return value.split(/[^a-z_]+/, 1)[0] || "missing";
}

export function projectPublicCensus(source, audit, holds, repoRoot) {
  let heldRuns = 0;
  let heldCards = 0;
  const verdictCounts = { ...source.verdict_counts };
  for (const id of holds.ids) {
    const runPath = join(repoRoot, "engine", "runs", id);
    if (existsSync(runPath)) heldRuns++;
    const cardPath = join(runPath, "result_card.md");
    if (!existsSync(cardPath)) continue;
    heldCards++;
    const bucket = cardVerdictBucket(readFileSync(cardPath, "utf8"));
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
      publication_rights_held_records: holds.ids.size,
      publication_rights_held_evidence_qualified: holds.evidenceQualified,
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
}
