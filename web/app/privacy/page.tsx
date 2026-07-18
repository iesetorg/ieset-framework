import Link from "next/link";

export const metadata = {
  title: "Privacy Policy",
  description:
    "How IESET handles visitor, contribution, analytics, and provenance data.",
  alternates: { canonical: "https://framework.ieset.org/privacy/" },
};

const UPDATED = "May 5, 2026";

const sections = [
  {
    title: "Information we collect",
    body: [
      "You can browse IESET without creating an account. The site is primarily a public research library, so ordinary reading should not require you to submit personal information.",
      "For security, reliability, and analytics, our hosting and delivery providers may process standard web request data such as IP address, user agent, referrer, approximate location, requested URL, and request time. IESET also uses Cloudflare Web Analytics through a first-party, cookie-less beacon to understand aggregate site usage.",
      "If you contact IESET, open an issue, send a pull request, submit review material, or otherwise contribute, we may receive the information you choose to provide, such as your name, email address, GitHub handle, affiliation, comments, and attached files.",
      "The IESET corpus also contains public research provenance, including citations, publisher/API metadata, fetch timestamps, hashes, git commits, and source links. That provenance is about the evidence record and is not intended to profile site visitors.",
    ],
  },
  {
    title: "How we use information",
    body: [
      "We use operational data to keep the site available, secure it against abuse, diagnose errors, understand which public pages are useful, and improve the research interface.",
      "We use contribution and contact data to review submissions, discuss corrections, attribute public contributions when appropriate, maintain reproducible records, and respond to requests.",
      "We use provenance data to make hypotheses, datasets, and published results auditable: every table should be traceable back to its source, fetch time, and content hash where available.",
    ],
  },
  {
    title: "Sharing and publication",
    body: [
      "IESET does not sell personal information and does not run targeted advertising.",
      "We share data with service providers that operate the site, including hosting, security, analytics, repository, and deployment providers. Those providers process data so the site and research workflow can function.",
      "Contributions made through public channels, such as public repositories or issue trackers, may be published with their associated attribution and discussion history. Do not submit confidential material through public contribution channels.",
      "We may disclose information if required by law, to protect the site and its users, or to investigate misuse of IESET services.",
    ],
  },
  {
    title: "Cookies and tracking",
    body: [
      "IESET does not intentionally place advertising cookies or build cross-site advertising profiles.",
      "The public site currently includes Cloudflare Web Analytics, which is configured as a privacy-preserving, cookie-less analytics beacon. Cloudflare and other infrastructure providers may still process technical data needed for security, caching, abuse prevention, and delivery.",
    ],
  },
  {
    title: "Retention and correction",
    body: [
      "Operational logs are retained only as long as reasonably needed for security, debugging, analytics, and compliance.",
      "Public research records, git history, citations, hashes, and contribution discussions may be retained indefinitely because reproducibility depends on stable provenance. If a public contribution includes personal information that should not have been included, contact us through the contribution channels and we will review reasonable redaction requests while preserving the integrity of the evidence record.",
    ],
  },
  {
    title: "Your choices",
    body: [
      "You can browse the public site without logging in. You can also avoid submitting personal information by not using public contribution or contact channels.",
      "If IESET later enables accounts, OAuth sign-in, private workspaces, or email subscriptions, this policy should be updated before those features are used for expanded personal-data processing.",
    ],
  },
  {
    title: "Children",
    body: [
      "IESET is not directed to children under 13, and we do not knowingly collect personal information from children.",
    ],
  },
  {
    title: "Contact",
    body: [
      "Questions, correction requests, and privacy concerns can be sent to info@ieset.org or raised through the public contribution channels linked from the contribute page. Please do not include sensitive personal information in public issues or pull requests.",
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

export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-[820px] px-8 py-12">
      <div className="mb-10 border-b border-rule pb-8">
        <p className="sc mb-3">IESET policy</p>
        <h1 className="mb-4 text-[36px] font-semibold leading-tight tracking-tight text-ink">
          Privacy Policy
        </h1>
        <p className="max-w-2xl text-[16px] leading-7 text-muted">
          IESET is built as a public evidence map. The privacy posture follows
          that design: collect as little visitor data as practical, keep
          provenance public and auditable, and avoid tracking people when the
          framework only needs to track claims, data, and methods.
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
        For review and correction workflows, see{" "}
        <Link href="/contribute" className="font-medium">
          Contribute
        </Link>
        . For the research integrity model, see{" "}
        <Link href="/methodology" className="font-medium">
          Methodology
        </Link>
        .
      </div>
    </main>
  );
}
