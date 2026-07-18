import { PolicyEvidenceBrowser } from "@/components/policies/PolicyEvidenceBrowser";
import { loadPolicyBrowserIndex } from "@/lib/policy-browser";

export const metadata = {
  title: "Policy Browser",
  description:
    "Search policy reforms by evidence, verdict mix, countries, axes, and schools of thought.",
  alternates: { canonical: "https://framework.ieset.org/policy-browser/" },
};

export default async function PolicyBrowserPage() {
  const index = await loadPolicyBrowserIndex();
  const tested = index.summary.coverage_counts.tested ?? 0;
  const noLink = index.summary.coverage_counts.no_hypothesis_link ?? 0;

  return (
    <div className="mx-auto max-w-content px-8 py-10">
      <h1 className="m-0 text-[34px] font-semibold tracking-[-0.02em]">
        Policy evidence browser
      </h1>
      <p className="mt-4 max-w-[820px] text-[17px] leading-[1.55] text-muted">
        Search concrete reforms by country, axis, verdict mix, and school-of-thought
        links. Each card joins a policy file to the hypotheses that test its
        outcomes, then compresses the result into a policy-maker read: posture,
        evidence strength, open gaps, and what to monitor next.
      </p>
      <div className="mt-5 rounded border border-[#d8c99f] bg-[#fff8e8] px-4 py-3 text-[13px] leading-[1.5] text-[#6f5018]">
        Method note: policy cards can mix direct policy-specific hypotheses with
        inferred analogues from the same policy axis. Treat this as a navigation
        layer for evidence, not a replacement for opening the linked hypothesis
        and checking its preregistered test.
      </div>

      <div className="my-6 grid gap-4 text-[14px] md:grid-cols-3">
        <div className="rounded border border-rule bg-panel p-4">
          <div className="sc text-[10px] text-muted">policies</div>
          <div className="mt-1 text-[24px] font-semibold">{index.summary.policy_count}</div>
        </div>
        <div className="rounded border border-rule bg-panel p-4">
          <div className="sc text-[10px] text-muted">with tested evidence</div>
          <div className="mt-1 text-[24px] font-semibold">{tested}</div>
        </div>
        <div className="rounded border border-rule bg-panel p-4">
          <div className="sc text-[10px] text-muted">unlinked</div>
          <div className="mt-1 text-[24px] font-semibold">{noLink}</div>
        </div>
      </div>

      <PolicyEvidenceBrowser />
    </div>
  );
}
