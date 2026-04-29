export const dynamic = "force-static";

import { NextResponse } from "next/server";

import { loadAllConditions } from "@/lib/content";

export async function GET() {
  const all = await loadAllConditions();
  return NextResponse.json(
    {
      api_version: "v1",
      count: all.length,
      conditions: all.map((c) => ({
        id: c.id,
        category: c.category,
        description: c.description,
        confidence: c.confidence,
        linked_hypotheses: c.linked_hypotheses ?? [],
        first_commit: c._first_commit,
        permalink: `https://ieset.dev/c/${c.id}`,
        api_url: `/api/v1/condition/${c.id}`,
      })),
    },
    { headers: { "Cache-Control": "public, max-age=60, s-maxage=300" } }
  );
}
