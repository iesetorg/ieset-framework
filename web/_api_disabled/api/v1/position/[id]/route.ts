export const dynamic = "force-static";

import { NextResponse } from "next/server";

import { loadAllPositions, loadPosition } from "@/lib/content";

export async function generateStaticParams() {
  const all = await loadAllPositions();
  return all.map((p) => ({ id: p.position_id }));
}

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const p = await loadPosition(id);
  if (!p) {
    return NextResponse.json(
      { error: "position_not_found", id },
      { status: 404 }
    );
  }

  return NextResponse.json(
    {
      api_version: "v1",
      position_id: p.position_id,
      school: p.school,
      short_name: p.short_name,
      status: p.status,
      proponents: p.proponents,
      key_texts: p.key_texts,
      steelman: p.steelman,
      falsifiable_specific_claims: p.falsifiable_specific_claims,
      empirical_record_summary: p.empirical_record_summary,
      scope_decisions: p.scope_decisions,
      linked_hypotheses: p.linked_hypotheses,
      notes: p.notes,
      provenance: {
        source_file: p._file,
        first_commit: p._first_commit,
      },
      permalink: `https://ieset.dev/pos/${p.position_id}`,
    },
    {
      headers: {
        "Cache-Control": "public, max-age=60, s-maxage=300",
      },
    }
  );
}
