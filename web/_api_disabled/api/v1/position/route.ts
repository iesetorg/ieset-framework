export const dynamic = "force-static";

import { NextResponse } from "next/server";

import { loadAllPositions } from "@/lib/content";

export async function GET() {
  const all = await loadAllPositions();
  return NextResponse.json(
    {
      api_version: "v1",
      count: all.length,
      positions: all.map((p) => ({
        position_id: p.position_id,
        school: p.school,
        short_name: p.short_name,
        status: p.status,
        proponents: p.proponents ?? [],
        linked_hypotheses: p.linked_hypotheses ?? [],
        first_commit: p._first_commit,
        permalink: `https://ieset.dev/pos/${p.position_id}`,
        api_url: `/api/v1/position/${p.position_id}`,
      })),
    },
    { headers: { "Cache-Control": "public, max-age=60, s-maxage=300" } }
  );
}
