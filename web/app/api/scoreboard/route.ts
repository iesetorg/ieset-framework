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
  const strictSignals = rankedSchools.filter(
    (score) =>
      score.integrity_score_signal === "positive_signal" ||
      score.integrity_score_signal === "negative_signal"
  );
  return Response.json({
    api_version: "2",
    generated_at: new Date().toISOString(),
    canonical_url: "https://framework.ieset.org/scoreboard/",
    scoring_policy: "attribution_net_v3_second_order_gated",
    evidence_gate: "evidence_tier_audit_v1",
    evidence_methodology_url: "https://framework.ieset.org/evidence/",
    peer_review_status: "not_peer_reviewed_by_default",
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
    strict_signal_school_count: strictSignals.length,
    strict_conclusion:
      strictSignals.length === 0
        ? "No ranked school is separated from the strict no-call band."
        : `${strictSignals.length} ranked schools are outside the strict no-call band.`,
    positions: rankedSchools,
    benchmark_controls: benchmarkControls,
  });
}
