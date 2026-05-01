// Scoreboard JSON API.
//
// Pre-rendered at build time. Cross-position-school weighted score
// summary — the same data that powers /scoreboard but in machine-readable
// form for third-party citation, dashboards, and newsroom embeds.

import { scoreAllPositions } from "@/lib/content";

export const dynamic = "force-static";

export async function GET() {
  const scores = await scoreAllPositions();
  return Response.json({
    api_version: "1",
    generated_at: new Date().toISOString(),
    canonical_url: "https://framework.ieset.org/scoreboard/",
    positions: scores,
  });
}
