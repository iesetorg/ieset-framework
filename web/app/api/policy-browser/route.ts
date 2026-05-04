import { loadPolicyBrowserIndex, toPolicyBrowserClientRows } from "@/lib/policy-browser";

export const dynamic = "force-static";

export async function GET() {
  const index = await loadPolicyBrowserIndex();
  return Response.json({
    api_version: "1",
    generated_at: new Date().toISOString(),
    canonical_url: "https://framework.ieset.org/policy-browser/",
    payload: "compact",
    note:
      "Compact policy-browser payload kept below Cloudflare's 25 MiB static-asset limit. Use policy pages and linked hypothesis APIs for full evidence detail.",
    summary: index.summary,
    rows: toPolicyBrowserClientRows(index),
  });
}
