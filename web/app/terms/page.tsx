import Link from "next/link";

export const metadata = {
  title: "Terms of Service",
  description:
    "Terms for using the IESET public research framework, data pages, and contribution channels.",
};

const UPDATED = "May 5, 2026";

const sections = [
  {
    title: "What IESET is",
    body: [
      "IESET is a public research framework, policy lab, and think tank for turning economic-policy claims into testable hypotheses. It publishes pre-registered specifications, reproducible evidence packets, policy links, movement histories, and scoreboard views.",
      "The framework is designed to make arguments auditable. It does not promise ideological neutrality; it promises explicit priors, transparent methods, public provenance, and openness to adversarial correction.",
    ],
  },
  {
    title: "Not professional advice",
    body: [
      "IESET content is provided for research, education, and public-interest discussion. It is not legal, financial, investment, tax, medical, or professional advice.",
      "Do not rely on IESET as the sole basis for policy, investment, legal, or personal decisions. Verify primary sources and consult qualified professionals where decisions carry real-world risk.",
    ],
  },
  {
    title: "Using the site",
    body: [
      "You may browse, cite, discuss, and link to public IESET pages. When using IESET data, code, charts, or evidence packets, preserve source attribution and respect any license notices attached to the relevant repository files, datasets, or third-party sources.",
      "Do not misuse the site by attempting to disrupt availability, bypass security, overload infrastructure, misrepresent results, strip provenance, or present IESET outputs as if they were produced under a different methodology.",
      "Automated access should be reasonable, cached where practical, and respectful of hosting limits. IESET exists to make public evidence easier to inspect, not to provide a high-volume commercial data feed.",
    ],
  },
  {
    title: "Contributions",
    body: [
      "If you submit issues, pull requests, review notes, data repairs, hypotheses, or other contributions, only submit material you have the right to share.",
      "By submitting material to IESET contribution channels, you give IESET permission to review, reproduce, adapt, publish, attribute, and archive that material as part of the public framework, subject to any repository license terms or contribution rules that apply.",
      "Do not submit confidential, proprietary, sensitive personal, or embargoed material unless a private review process has been explicitly agreed in advance.",
    ],
  },
  {
    title: "Evidence and limitations",
    body: [
      "IESET results are provisional research artifacts. A verdict can change when data vintages improve, specifications are corrected, better causal identification becomes available, or adversarial review finds an error.",
      "The scoreboard and related pages summarize the current corpus. They should be read together with each hypothesis page, evidence packet, diagnostics, steelman, and falsification rule.",
      "IESET may contain errors, stale links, incomplete coverage, or contested interpretations. The correction process is part of the product, not an exception to it.",
    ],
  },
  {
    title: "Third-party services and sources",
    body: [
      "IESET links to publisher APIs, public datasets, repositories, archives, and third-party websites. Those services are governed by their own terms, privacy policies, licenses, and availability constraints.",
      "IESET is not responsible for third-party content, data availability, API changes, rate limits, or licensing changes.",
    ],
  },
  {
    title: "Reserved integration routes",
    body: [
      "Some URLs may be reserved for third-party app verification or OAuth redirect configuration. A reserved redirect URL being reachable does not mean that a full sign-in or token-exchange flow is active unless IESET explicitly documents that integration.",
    ],
  },
  {
    title: "No warranty",
    body: [
      "IESET is provided on an as-is and as-available basis. To the fullest extent permitted by law, IESET disclaims warranties of accuracy, completeness, fitness for a particular purpose, uninterrupted availability, and non-infringement.",
      "To the fullest extent permitted by law, IESET will not be liable for indirect, incidental, consequential, special, exemplary, or punitive damages arising from use of the site or reliance on its content.",
    ],
  },
  {
    title: "Changes",
    body: [
      "IESET may update these terms as the framework, data pipeline, contribution process, or integrations evolve. The updated date at the top of this page indicates the latest published version.",
    ],
  },
  {
    title: "Contact",
    body: [
      "Questions about these terms can be raised through the contribution channels linked from the contribute page.",
    ],
  },
];

function Section({
  title,
  body,
}: {
  title: string;
  body: string[];
}) {
  return (
    <section className="border-t border-rule pt-7">
      <h2 className="sc mb-4">{title}</h2>
      <div className="space-y-4 text-[15px] leading-7 text-ink">
        {body.map((paragraph) => (
          <p key={paragraph}>{paragraph}</p>
        ))}
      </div>
    </section>
  );
}

export default function TermsPage() {
  return (
    <main className="mx-auto max-w-[820px] px-8 py-12">
      <div className="mb-10 border-b border-rule pb-8">
        <p className="sc mb-3">IESET policy</p>
        <h1 className="mb-4 text-[36px] font-semibold leading-tight tracking-tight text-ink">
          Terms of Service
        </h1>
        <p className="max-w-2xl text-[16px] leading-7 text-muted">
          These terms cover the public IESET website, its research pages, and
          the contribution pathways used to improve the corpus. The short
          version: use the framework honestly, preserve provenance, respect
          source licenses, and do not treat provisional research as a substitute
          for professional advice.
        </p>
        <p className="mt-4 text-xs uppercase tracking-[0.14em] text-muted">
          Last updated: {UPDATED}
        </p>
      </div>

      <div className="space-y-9">
        {sections.map((section) => (
          <Section key={section.title} {...section} />
        ))}
      </div>

      <div className="mt-10 rounded-lg border border-rule bg-panel p-5 text-sm leading-6 text-muted">
        For the review process, see{" "}
        <Link href="/contribute" className="font-medium">
          Contribute
        </Link>
        . For data-handling details, see{" "}
        <Link href="/privacy" className="font-medium">
          Privacy Policy
        </Link>
        .
      </div>
    </main>
  );
}
