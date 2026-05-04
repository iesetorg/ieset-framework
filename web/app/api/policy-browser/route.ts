import { loadPolicyBrowserIndex } from "@/lib/policy-browser";

export const dynamic = "force-static";

export async function GET() {
  const index = await loadPolicyBrowserIndex();
  return Response.json({
    api_version: "1",
    generated_at: new Date().toISOString(),
    canonical_url: "https://framework.ieset.org/policy-browser/",
    summary: index.summary,
    policies: index.policies,
  });
}
