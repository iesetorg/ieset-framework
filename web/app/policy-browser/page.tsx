import { PolicyEvidenceBrowser } from "@/components/policies/PolicyEvidenceBrowser";
import { loadPolicyBrowserIndex } from "@/lib/policy-browser";

export const metadata = {
  title: "Policy Browser",
  description:
    "Search policy reforms by curated public linked results, countries, and policy axes.",
  alternates: { canonical: "https://framework.ieset.org/policy-browser/" },
};

export default async function PolicyBrowserPage() {
  const index = await loadPolicyBrowserIndex();
  const tested = index.summary.coverage_counts.tested ?? 0;
  const anyPublicLinked = index.policies.filter(
    (row) => row.tested_hypothesis_count > 0 || (row.context_counts.related_public ?? 0) > 0
  ).length;

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <h1 className="m-0 text-[34px] font-semibold tracking-[-0.02em]">
        Policy evidence browser
      </h1>
      <p className="mt-4 max-w-[820px] text-[17px] leading-[1.55] text-muted">
        Search concrete reforms by country, policy axis, and linked research.
        Each card shows the public results on curated links, related research,
        and gaps that remain open.
      </p>
      <div className="mt-5 rounded border border-[#d8c99f] bg-[#fff8e8] px-4 py-3 text-[13px] leading-[1.5] text-[#6f5018]">
        Method note: only a curated link to a current public result contributes
        to a card&apos;s verdict mix, design strength, or tested count. Axis matches
        and archived runs are navigation context. A link alone does not show
        that this policy caused the linked result.
      </div>

      <div className="my-6 grid gap-4 text-[14px] md:grid-cols-3">
        <div className="rounded border border-rule bg-panel p-4">
          <div className="sc text-[10px] text-muted">policies</div>
          <div className="mt-1 text-[24px] font-semibold">{index.summary.policy_count}</div>
        </div>
        <div className="rounded border border-rule bg-panel p-4">
          <div className="sc text-[10px] text-muted">with curated public results</div>
          <div className="mt-1 text-[24px] font-semibold">{tested}</div>
        </div>
        <div className="rounded border border-rule bg-panel p-4">
          <div className="sc text-[10px] text-muted">with any public linked result</div>
          <div className="mt-1 text-[24px] font-semibold">{anyPublicLinked}</div>
          <div className="mt-1 text-[11px] text-muted">includes axis matches</div>
        </div>
      </div>

      <PolicyEvidenceBrowser />
    </div>
  );
}
