import { loadPolicyBrowserIndex, toPolicyBrowserClientRows } from "@/lib/policy-browser";

export const dynamic = "force-static";

export async function GET() {
  const index = await loadPolicyBrowserIndex();
  return Response.json({
    api_version: "2",
    evidence_scope: index.evidence_scope,
    summary: index.summary,
    rows: toPolicyBrowserClientRows(index),
  });
}
