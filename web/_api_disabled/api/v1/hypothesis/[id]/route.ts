export const dynamic = "force-static";

import { NextResponse } from "next/server";

import { loadAllHypotheses, loadHypothesis, parseSourceString } from "@/lib/content";

export async function generateStaticParams() {
  const all = await loadAllHypotheses();
  return all.map((h) => ({ id: h.hypothesis_id }));
}

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const h = await loadHypothesis(id);
  if (!h) {
    return NextResponse.json(
      { error: "hypothesis_not_found", id },
      { status: 404 }
    );
  }

  // Enrich source strings with resolved publisher metadata for API consumers
  const variables = h.variables ?? {};
  const enriched: Record<string, unknown[]> = {};
  for (const [group, vars] of Object.entries(variables)) {
    if (!vars) continue;
    enriched[group] = await Promise.all(
      (vars as { name: string; source?: string; transformation?: string; notes?: string }[]).map(async (v) => ({
        ...v,
        tokens: await parseSourceString(v.source),
      }))
    );
  }

  return NextResponse.json(
    {
      api_version: "v1",
      hypothesis_id: h.hypothesis_id,
      version: h.version,
      status: h.status,
      topic: h.topic,
      claim: h.claim,
      evidence_type: h.evidence_type,
      sample: h.sample,
      variables: enriched,
      intervention_channel: h.intervention_channel,
      estimator: h.estimator,
      falsification: h.falsification,
      prior_confidence: h.prior_confidence,
      disclosure: h.disclosure,
      conflict_disclosure: h.conflict_disclosure,
      steelman: { path: h.steelman, rendered_html_url: `/h/${h.hypothesis_id}` },
      linked_hypotheses: h.linked_hypotheses,
      linked_conditions: h.linked_conditions,
      provenance: {
        source_file: h._file,
        first_commit: h._first_commit,
      },
      permalink: `https://ieset.dev/h/${h.hypothesis_id}`,
    },
    {
      headers: {
        "Cache-Control": "public, max-age=60, s-maxage=300",
      },
    }
  );
}
