// Scoreboard JSON API.
//
// Pre-rendered at build time. Cross-position-school weighted score
// summary — the same data that powers /scoreboard but in machine-readable
// form for third-party citation, dashboards, and newsroom embeds. Positions
// are ordered by the attribution-aware integrity score; legacy forecast scores
// remain in each row for comparison.

import { scoreAllPositions } from "@/lib/content";

export const dynamic = "force-static";

export async function GET() {
  const scores = await scoreAllPositions();
  return Response.json({
    api_version: "2",
    generated_at: new Date().toISOString(),
    canonical_url: "https://framework.ieset.org/scoreboard/",
    scoring_policy: "attribution_net_v2",
    rank_basis: "integrity_net_score",
    legacy_forecast_score_field: "adjusted_net_score",
    positions: scores,
  });
}
