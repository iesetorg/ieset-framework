export const dynamic = "force-static";

import { NextResponse } from "next/server";

import { loadAllConditions, loadCondition } from "@/lib/content";

export async function generateStaticParams() {
  const all = await loadAllConditions();
  return all.map((c) => ({ id: c.id }));
}

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const c = await loadCondition(id);
  if (!c) {
    return NextResponse.json(
      { error: "condition_not_found", id },
      { status: 404 }
    );
  }

  return NextResponse.json(
    {
      api_version: "v1",
      id: c.id,
      category: c.category,
      description: c.description,
      institutional_features_that_make_the_model_work:
        c.institutional_features_that_make_the_model_work,
      supporting_cases: c.supporting_cases,
      disconfirming_cases: c.disconfirming_cases,
      failed_replications: c.failed_replications,
      policy_implications: c.policy_implications,
      what_the_model_is_not: c.what_the_model_is_not,
      framework_position: c.framework_position,
      confidence: c.confidence,
      linked_hypotheses: c.linked_hypotheses,
      linked_model_ids: c.linked_model_ids,
      sub_analyses: c.sub_analyses,
      provenance: {
        source_file: c._file,
        first_commit: c._first_commit,
      },
      permalink: `https://ieset.dev/c/${c.id}`,
    },
    {
      headers: {
        "Cache-Control": "public, max-age=60, s-maxage=300",
      },
    }
  );
}
