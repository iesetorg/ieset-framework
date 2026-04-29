export const dynamic = "force-static";

import { NextResponse } from "next/server";

import { loadAllHypotheses } from "@/lib/content";

export async function GET() {
  const all = await loadAllHypotheses();
  return NextResponse.json(
    {
      api_version: "v1",
      count: all.length,
      hypotheses: all.map((h) => ({
        hypothesis_id: h.hypothesis_id,
        status: h.status,
        topic: h.topic,
        claim: h.claim,
        evidence_type: h.evidence_type,
        prior_confidence: h.prior_confidence,
        sample: h.sample,
        first_commit: h._first_commit,
        permalink: `https://ieset.dev/h/${h.hypothesis_id}`,
        api_url: `/api/v1/hypothesis/${h.hypothesis_id}`,
      })),
    },
    { headers: { "Cache-Control": "public, max-age=60, s-maxage=300" } }
  );
}
