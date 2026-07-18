import type { MetadataRoute } from "next";

import {
  loadAllAxes,
  loadAllConditions,
  loadAllHypotheses,
  loadAllPositions,
  loadRunArtifacts,
  REPO_ROOT,
} from "@/lib/content";
import { loadDrift } from "@/lib/drift";
import { loadAllPolicies } from "@/lib/policies";
import { PUBLIC_SITE_ORIGIN } from "@/lib/site";
import { existsSync, readdirSync } from "node:fs";
import { join } from "node:path";

export const dynamic = "force-static";

function abs(path: string): string {
  return `${PUBLIC_SITE_ORIGIN}${path.startsWith("/") ? path : `/${path}`}`;
}

function parsedDate(value: string | undefined): Date | undefined {
  if (!value) return undefined;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? undefined : date;
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const entries: MetadataRoute.Sitemap = [];

  // Static pillars
  for (const path of [
    "/",
    "/h/",
    "/p/",
    "/m/",
    "/pos/",
    "/a/",
    "/c/",
    "/scoreboard/",
    "/atlas/",
    "/drift/",
    "/policy-browser/",
    "/methodology/",
    "/methods-paper/",
    "/how-it-works/",
    "/disclosure/",
    "/production/",
    "/evidence/",
    "/updates/",
    "/contribute/",
    "/terms/",
    "/privacy/",
  ]) {
    entries.push({
      url: abs(path),
    });
  }

  const [hyps, positions, axes, conditions, policies, drift] = await Promise.all([
    loadAllHypotheses(),
    loadAllPositions(),
    loadAllAxes(),
    loadAllConditions(),
    loadAllPolicies(),
    loadDrift(),
  ]);

  // Archive-tier pages remain directly inspectable but carry noindex and are
  // omitted here. A sitemap should describe canonical pages intended for
  // indexing, not inflate the corpus with records that fail public gates.
  for (const h of hyps.filter((hypothesis) => hypothesis._evidence_public_visible)) {
    const run = await loadRunArtifacts(h.hypothesis_id);
    entries.push({
      url: abs(`/h/${h.hypothesis_id}/`),
      lastModified:
        parsedDate(run.generated_at) ?? parsedDate(h._first_commit?.iso),
    });
  }

  for (const p of positions) {
    entries.push({
      url: abs(`/pos/${p.position_id}/`),
    });
  }

  for (const a of axes) {
    entries.push({
      url: abs(`/a/${a.id}/`),
    });
  }

  for (const c of conditions) {
    entries.push({
      url: abs(`/c/${c.id}/`),
    });
  }

  for (const p of policies) {
    entries.push({
      url: abs(`/p/${p.policy_id}/`),
    });
  }

  const movDir = join(REPO_ROOT, "movements");
  if (existsSync(movDir)) {
    const files = readdirSync(movDir).filter((f) => f.endsWith(".yaml"));
    for (const f of files) {
      const id = f.replace(/\.yaml$/, "");
      entries.push({
        url: abs(`/m/${id}/`),
      });
    }
  }

  for (const iso3 of Object.keys(drift?.countries ?? {}).sort()) {
    entries.push({
      url: abs(`/country/${iso3}/`),
    });
  }

  return entries;
}
