// Hypothesis index JSON API.
//
// Pre-rendered at build time. Lightweight list of all hypotheses with their
// public-visibility flag, current verdict, and canonical URL — for paginated
// scrapers, search-engine sitemaps, and third parties wanting to walk the
// corpus without 270+ separate fetches.

import {
  loadAllHypotheses,
  loadRunArtifacts,
  isHypothesisPubliclyVisible,
} from "@/lib/content";

export const dynamic = "force-static";

export async function GET() {
  const all = await loadAllHypotheses();
  const items = await Promise.all(
    all.map(async (h) => {
      const run = await loadRunArtifacts(h.hypothesis_id);
      const isPublic = isHypothesisPubliclyVisible(h, {
        exists: run.exists,
        verdict: run.verdict,
      });
      return {
        hypothesis_id: h.hypothesis_id,
        topic: h.topic ?? null,
        claim: h.claim ?? null,
        evidence_type: h.evidence_type ?? null,
        evidence_tier: h._evidence_tier ?? "archive",
        registration_status: h._registration_status ?? "unknown",
        estimator_floor: h._estimator_floor ?? "unknown",
        reference_set: h._reference_set ?? false,
        exclusion_reasons: h._evidence_exclusion_reasons ?? [],
        verdict: run.verdict ?? null,
        is_public: isPublic,
        canonical_url: `https://framework.ieset.org/h/${h.hypothesis_id}/`,
        api_url: `https://framework.ieset.org/api/h/${h.hypothesis_id}.json`,
      };
    })
  );
  // Sort: public first (alpha), then hidden (alpha)
  items.sort((a, b) => {
    if (a.is_public !== b.is_public) return a.is_public ? -1 : 1;
    return a.hypothesis_id.localeCompare(b.hypothesis_id);
  });
  return Response.json({
    api_version: "2",
    generated_at: new Date().toISOString(),
    canonical_url: "https://framework.ieset.org/h/",
    methodology_url: "https://framework.ieset.org/evidence/",
    license: "https://creativecommons.org/licenses/by/4.0/",
    peer_review_status: "not_peer_reviewed_by_default",
    total: items.length,
    public_count: items.filter((i) => i.is_public).length,
    tier_counts: items.reduce<Record<string, number>>((counts, item) => {
      counts[item.evidence_tier] = (counts[item.evidence_tier] ?? 0) + 1;
      return counts;
    }, {}),
    items,
  });
}
