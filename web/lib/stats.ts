import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { REPO_ROOT } from "./content";

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
    conditional_entries: number;
    review_submissions: number;
    completed_review_logs: number;
  };
  definitions?: Record<string, string>;
  verdict_counts?: Record<string, number>;
}

/**
 * Single source of truth for public counters.
 * Written by CI / census scripts to engine/public_corpus_census.json.
 */
export function loadPublicCensus(): PublicCorpusCensus | null {
  const path = join(REPO_ROOT, "engine", "public_corpus_census.json");
  if (!existsSync(path)) return null;
  try {
    return JSON.parse(readFileSync(path, "utf8")) as PublicCorpusCensus;
  } catch {
    return null;
  }
}
