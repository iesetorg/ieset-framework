import type { MetadataRoute } from "next";

import {
  loadAllAxes,
  loadAllConditions,
  loadAllHypotheses,
  loadAllPositions,
  REPO_ROOT,
} from "@/lib/content";
import { loadAllPolicies } from "@/lib/policies";
import { PUBLIC_SITE_ORIGIN } from "@/lib/site";
import { existsSync, readdirSync } from "node:fs";
import { join } from "node:path";

function abs(path: string): string {
  return `${PUBLIC_SITE_ORIGIN}${path.startsWith("/") ? path : `/${path}`}`;
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();
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
    "/how-it-works/",
    "/disclosure/",
    "/production/",
    "/updates/",
    "/contribute/",
    "/terms/",
    "/privacy/",
  ]) {
    entries.push({
      url: abs(path),
      lastModified: now,
      changeFrequency: path === "/" || path === "/scoreboard/" ? "weekly" : "monthly",
      priority: path === "/" ? 1 : path === "/scoreboard/" || path === "/h/" ? 0.9 : 0.6,
    });
  }

  const [hyps, positions, axes, conditions, policies] = await Promise.all([
    loadAllHypotheses(),
    loadAllPositions(),
    loadAllAxes(),
    loadAllConditions(),
    loadAllPolicies(),
  ]);

  for (const h of hyps) {
    entries.push({
      url: abs(`/h/${h.hypothesis_id}/`),
      lastModified: h._first_commit?.iso ? new Date(h._first_commit.iso) : now,
      changeFrequency: "monthly",
      priority: 0.7,
    });
  }

  for (const p of positions) {
    entries.push({
      url: abs(`/pos/${p.position_id}/`),
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.65,
    });
  }

  for (const a of axes) {
    entries.push({
      url: abs(`/a/${a.id}/`),
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.5,
    });
  }

  for (const c of conditions) {
    entries.push({
      url: abs(`/c/${c.id}/`),
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.5,
    });
  }

  // Cap policies/movements to keep sitemap generation bounded; the full
  // indexes remain crawlable from /p/ and /m/.
  for (const p of policies.slice(0, 2500)) {
    entries.push({
      url: abs(`/p/${p.policy_id}/`),
      lastModified: now,
      changeFrequency: "yearly",
      priority: 0.4,
    });
  }

  const movDir = join(REPO_ROOT, "movements");
  if (existsSync(movDir)) {
    const files = readdirSync(movDir).filter((f) => f.endsWith(".yaml"));
    for (const f of files.slice(0, 800)) {
      const id = f.replace(/\.yaml$/, "");
      entries.push({
        url: abs(`/m/${id}/`),
        lastModified: now,
        changeFrequency: "yearly",
        priority: 0.4,
      });
    }
  }

  return entries;
}
