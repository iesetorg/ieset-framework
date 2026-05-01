// Per-hypothesis JSON API.
//
// Pre-rendered at build time to a static file (no Worker, no edge runtime):
//   /api/h/<id>.json — payload of YAML spec + run summary, falsification rule,
//   diagnostic verdict, school predictions, and a public-visibility flag.
//
// `dynamic = 'force-static'` + `generateStaticParams` + Next.js `output: 'export'`
// causes Next to write the JSON body to `out/api/h/<id>` at build time, served
// verbatim by Cloudflare Pages.
//
// Visibility note: ALL hypotheses with YAML on disk get a JSON file, including
// those hidden from the public index. The `is_public` flag in the payload tells
// downstream consumers (citation-checkers, RSS, etc.) whether the verdict was
// reached against a sharpened pre-registered rule. Hidden ones still surface
// their YAML so a citing third party can audit the spec — they just don't have
// a sharpened verdict yet.

import {
  loadAllHypotheses,
  loadHypothesis,
  loadRunArtifacts,
  isHypothesisPubliclyVisible,
  schoolPredictionsForHypothesis,
} from "@/lib/content";

export const dynamic = "force-static";
export const dynamicParams = false;

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
    return new Response(
      JSON.stringify({ error: "hypothesis not found", id }),
      { status: 404, headers: { "content-type": "application/json" } }
    );
  }

  const run = await loadRunArtifacts(id);
  const schoolPredictions = await schoolPredictionsForHypothesis(id);
  const isPublic = isHypothesisPubliclyVisible(h, {
    exists: run.exists,
    verdict: run.verdict,
  });

  const payload = {
    hypothesis_id: h.hypothesis_id,
    version: h.version,
    status: h.status,
    topic: h.topic,
    claim: h.claim ?? null,
    scope: h.scope ?? null,
    sample: h.sample ?? null,
    estimator: h.estimator ?? null,
    falsification: h.falsification ?? null,
    methodology_note: h.methodology_note ?? null,
    notes: h.notes ?? null,
    run: {
      exists: run.exists,
      verdict: run.verdict ?? null,
      verdict_reason:
        (run.diagnostics?.verdict_reason as string | undefined) ?? null,
      diagnostics: run.diagnostics ?? null,
      run_dir: run.run_dir_rel ?? null,
    },
    school_predictions: schoolPredictions,
    is_public: isPublic,
    canonical_url: `https://framework.ieset.org/h/${h.hypothesis_id}/`,
    api_version: "1",
  };

  return Response.json(payload);
}
