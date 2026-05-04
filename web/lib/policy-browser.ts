import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join } from "node:path";

import { REPO_ROOT } from "./content";

export interface PolicyBrowserAxis {
  axis: string;
  channel: string;
  direction: string;
  magnitude?: string;
  intended?: boolean;
}

export interface PolicyBrowserEvidence {
  hypothesis_id: string;
  topic: string;
  evidence_type: string;
  verdict: string;
  bucket: string;
  evidence_strength: string;
  template: string;
  run_dir: string;
  position_ids: string[];
}

export interface PolicyBrowserRow {
  policy_id: string;
  title: string;
  status: string;
  countries: string[];
  timeframe: { start?: number; end?: number | string; enacted_date?: string };
  description?: string;
  path: string;
  axes: PolicyBrowserAxis[];
  coverage: string;
  linked_hypothesis_count: number;
  tested_hypothesis_count: number;
  verdict_counts: Record<string, number>;
  evidence_strength_counts: Record<string, number>;
  decision_lens: {
    posture: string;
    tested_hypotheses: number;
    unresolved_hypotheses: number;
    best_available_evidence: string;
    watch_points: string[];
  };
  search_terms: string[];
  evidence: PolicyBrowserEvidence[];
}

export interface PolicyBrowserIndex {
  schema_version: number;
  generated_by: string;
  summary: {
    policy_count: number;
    coverage_counts: Record<string, number>;
    verdict_counts: Record<string, number>;
    top_axes: [string, number][];
    top_countries: [string, number][];
    position_claim_link_counts: Record<string, number>;
  };
  policies: PolicyBrowserRow[];
}

export interface PolicyBrowserClientRow {
  policy_id: string;
  title: string;
  countries: string[];
  year: number | null;
  axes: { axis: string; channel: string; direction: string }[];
  coverage: string;
  linked_hypothesis_count: number;
  tested_hypothesis_count: number;
  verdict_counts: Record<string, number>;
  posture: string;
  best_available_evidence: string;
  watch_points: string[];
  top_hypotheses: { hypothesis_id: string; bucket: string; topic: string }[];
  schools: string[];
  search_terms: string[];
}

let cache: Promise<PolicyBrowserIndex> | null = null;

export async function loadPolicyBrowserIndex(): Promise<PolicyBrowserIndex> {
  if (cache) return cache;
  cache = (async () => {
    const path = join(REPO_ROOT, "engine", "policy_browser_index.json");
    if (!existsSync(path)) {
      throw new Error(
        "Missing engine/policy_browser_index.json. Run scripts/generate_policy_browser_index.py."
      );
    }
    const raw = await readFile(path, "utf8");
    return JSON.parse(raw) as PolicyBrowserIndex;
  })();
  return cache;
}

export function toPolicyBrowserClientRows(index: PolicyBrowserIndex): PolicyBrowserClientRow[] {
  return index.policies.map((row) => {
    const schoolSet = new Set<string>();
    const topHypotheses = row.evidence
      .filter((e) => e.bucket !== "missing")
      .slice(0, 6)
      .map((e) => {
        for (const positionId of e.position_ids ?? []) schoolSet.add(positionId);
        return {
          hypothesis_id: e.hypothesis_id,
          bucket: e.bucket,
          topic: e.topic,
        };
      });

    for (const evidence of row.evidence) {
      for (const positionId of evidence.position_ids ?? []) schoolSet.add(positionId);
    }

    return {
      policy_id: row.policy_id,
      title: row.title,
      countries: row.countries,
      year: row.timeframe?.start ?? null,
      axes: row.axes.map((a) => ({
        axis: a.axis,
        channel: a.channel,
        direction: a.direction,
      })),
      coverage: row.coverage,
      linked_hypothesis_count: row.linked_hypothesis_count,
      tested_hypothesis_count: row.tested_hypothesis_count,
      verdict_counts: row.verdict_counts,
      posture: row.decision_lens.posture,
      best_available_evidence: row.decision_lens.best_available_evidence,
      watch_points: row.decision_lens.watch_points,
      top_hypotheses: topHypotheses,
      schools: [...schoolSet].sort(),
      search_terms: row.search_terms,
    };
  });
}
