import { readFile, readdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join } from "node:path";
import yaml from "js-yaml";
import { remark } from "remark";
import remarkHtml from "remark-html";

import { REPO_ROOT } from "./content";

export interface PolicyAxisMove {
  axis: string;
  direction: string;
  magnitude?: string;
  intended?: boolean;
  rationale?: string;
}

export interface Policy {
  policy_id: string;
  status: string;
  title: string;
  countries: string[];
  timeframe: { start: number; end: number | string; enacted_date?: string };
  description?: string;
  enacted_by?: string[];
  coalition_label_at_enactment?: string;
  axes_moved?: PolicyAxisMove[];
  linked_hypotheses?: string[];
  linked_hypotheses_inferred?: string[];
  references?: string[];
  steelman?: string;
  notes?: string;
  _steelman_html?: string;
}

async function listPolicyFiles(): Promise<string[]> {
  const dir = join(REPO_ROOT, "policies");
  if (!existsSync(dir)) return [];
  const entries = await readdir(dir);
  return entries
    .filter((e) => e.endsWith(".yaml"))
    .map((e) => join(dir, e));
}

async function parsePolicy(absPath: string): Promise<Policy | null> {
  const raw = await readFile(absPath, "utf8");
  const doc = yaml.load(raw) as Policy;
  if (!doc?.policy_id) return null;
  if (doc.steelman) {
    const abs = join(REPO_ROOT, doc.steelman);
    if (existsSync(abs)) {
      const md = await readFile(abs, "utf8");
      const out = await remark().use(remarkHtml).process(md);
      doc._steelman_html = out.toString();
    }
  }
  return doc;
}

let _allPoliciesCache: Promise<Policy[]> | null = null;
export async function loadAllPolicies(): Promise<Policy[]> {
  if (_allPoliciesCache) return _allPoliciesCache;
  _allPoliciesCache = (async () => {
    const files = await listPolicyFiles();
    const all = await Promise.all(files.map(parsePolicy));
    return all
      .filter((p): p is Policy => p != null)
      .sort((a, b) => a.policy_id.localeCompare(b.policy_id));
  })();
  return _allPoliciesCache;
}

export async function loadPolicy(id: string): Promise<Policy | null> {
  const all = await loadAllPolicies();
  return all.find((p) => p.policy_id === id) ?? null;
}
