// Scoreboard JSON API.
//
// Pre-rendered at build time. Cross-position-school weighted score
// summary — the same data that powers /scoreboard but in machine-readable
// form for third-party citation, dashboards, and newsroom embeds. Positions
// are ordered by the attribution-aware integrity score; legacy forecast scores
// remain in each row for comparison.

import {
  loadScoreboardSecondOrderGateSummary,
  scoreAllPositions,
} from "@/lib/content";

export const dynamic = "force-static";

export async function GET() {
  const [scores, secondOrderGates] = await Promise.all([
    scoreAllPositions(),
    loadScoreboardSecondOrderGateSummary(),
  ]);
  const rankedSchools = scores.filter((score) => score.scoreboard_role === "school");
  const benchmarkControls = scores.filter(
    (score) => score.scoreboard_role === "benchmark_control"
  );
  return Response.json({
    api_version: "2",
    generated_at: new Date().toISOString(),
    canonical_url: "https://framework.ieset.org/scoreboard/",
    scoring_policy: "attribution_net_v3_second_order_gated",
    second_order_gate_artifact: secondOrderGates,
    rank_basis: "integrity_net_score",
    rank_tie_breakers: [
      "integrity_tested_weight",
      "adjusted_net_score",
      "adjusted_tested_weight",
      "net_score",
      "position_id",
    ],
    legacy_forecast_score_field: "adjusted_net_score",
    ranked_school_count: rankedSchools.length,
    benchmark_control_count: benchmarkControls.length,
    positions: rankedSchools,
    benchmark_controls: benchmarkControls,
  });
}
