import type { Metadata } from "next";
import Link from "next/link";

import { PUBLIC_GITHUB_REPO } from "@/lib/site";

export const metadata: Metadata = {
  title: "Production method",
  description:
    "How IESET is built: human direction, LLM-assisted drafting and estimation, public evidence substrate, and what is deliberately not published.",
  alternates: { canonical: "https://framework.ieset.org/production/" },
};

export default function ProductionPage() {
  return (
    <div className="mx-auto max-w-[780px] px-8 py-10">
      <p className="mb-2 text-[12px] font-semibold uppercase tracking-wider text-muted">
        Disclosure
      </p>
      <h1 className="m-0 text-[34px] font-semibold tracking-[-0.02em]">
        How IESET is produced
      </h1>
      <p className="mt-4 text-[17px] leading-[1.55] text-muted">
        IESET is an authored research framework built at high tempo with
        large-language-model assistance under human direction. The public
        source of truth is not model prose — it is the committed specs,
        pinned data vintages, replication scripts, and git history in{" "}
        <a
          href={PUBLIC_GITHUB_REPO}
          className="text-accent underline hover:no-underline"
        >
          iesetorg/ieset-framework
        </a>
        .
      </p>

      <section className="mt-10">
        <h2 className="m-0 text-[18px] font-semibold">The rule that matters</h2>
        <p className="mt-3 text-[15px] leading-[1.65] text-ink">
          <strong>Models are workers, not authorities.</strong> A claim is only
          as good as its pre-registered falsification rule, its publisher-backed
          data lineage, and a run that can be re-executed from the repo. Model
          drafts that never land in that substrate do not count as evidence.
        </p>
      </section>

      <section className="mt-10">
        <h2 className="m-0 text-[18px] font-semibold">What the pipeline does</h2>
        <ol className="mt-3 list-decimal space-y-2 pl-5 text-[15px] leading-[1.65] text-ink">
          <li>
            Draft and refine hypothesis specs (claim, sample, estimator,
            threshold, steelman) under human review.
          </li>
          <li>
            Fetch and pin public series from primary publishers (World Bank,
            IMF, OECD, FRED, Eurostat, and others) with content hashes.
          </li>
          <li>
            Run estimators via committed scripts; write diagnostics, result
            cards, and replication artifacts into{" "}
            <code className="rounded bg-panel px-1 text-[13px]">
              engine/runs/&lt;id&gt;/
            </code>
            .
          </li>
          <li>
            Score school-level predictions on the scoreboard with explicit
            integrity and attribution discounts.
          </li>
          <li>
            Surface the public library on this site from the same repository
            the reader can clone.
          </li>
        </ol>
      </section>

      <section className="mt-10">
        <h2 className="m-0 text-[18px] font-semibold">What this is not</h2>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-[15px] leading-[1.65] text-ink">
          <li>
            Not peer review. External review is a{" "}
            <Link href="/contribute/" className="text-accent underline">
              pilot
            </Link>
            ; zero external submissions does not equal zero scrutiny, but it is
            not completed refereeing either.
          </li>
          <li>
            Not an independent multi-author institute with staff economists.
            IESET is maintained under an institutional banner by an author with
            disclosed priors — see{" "}
            <Link href="/disclosure/" className="text-accent underline">
              transparency
            </Link>
            .
          </li>
          <li>
            Not a claim that every verdict is high-integrity causal evidence.
            The scoreboard&apos;s strict gates often leave schools{" "}
            <em>too close to call</em>; that is an intended signal, not a bug.
          </li>
        </ul>
      </section>

      <section className="mt-10">
        <h2 className="m-0 text-[18px] font-semibold">
          Registration honesty after history audits
        </h2>
        <p className="mt-3 text-[15px] leading-[1.65] text-ink">
          A large share of early corpus rows entered git as same-commit
          spec+run pairs. Those are labelled{" "}
          <code className="rounded bg-panel px-1 text-[13px]">
            legacy_same_commit
          </code>{" "}
          and do not receive verified pre-registration credit. New prospective
          tests require strict spec-before-run topology, checked in CI.
          Hypothesis pages show the{" "}
          <strong>first commit that added the spec file</strong>, linked to
          GitHub — never the repository HEAD stamp.
        </p>
      </section>

      <section className="mt-10">
        <h2 className="m-0 text-[18px] font-semibold">
          What stays out of the public repository
        </h2>
        <p className="mt-3 text-[15px] leading-[1.65] text-ink">
          Operator automation (token budgets, private agent control planes,
          credentials, local paths, and internal dispatch state) is{" "}
          <strong>not</strong> published. That is an operational boundary, not
          a claim that production is magic. The evidence anyone should argue
          with is still public: specs, vintages, replication code, and
          results.
        </p>
      </section>

      <section className="mt-10">
        <h2 className="m-0 text-[18px] font-semibold">
          Institutional accountability and change control
        </h2>
        <p className="mt-3 text-[15px] leading-[1.65] text-ink">
          Public repository administration and authorship use the IESET
          institutional account. CI gates the research schemas, registration
          topology, evidence tiers, estimator floor, public counters, static
          export, and OPSEC boundary. Ordinary public history is append-only;
          an exposure response may rewrite history only after the replacement
          tip passes the complete gate.
        </p>
        <p className="mt-3 text-[15px] leading-[1.65] text-ink">
          IESET does not claim cryptographic release signing, a DOI, or an
          independent archive timestamp until verifiable proof is linked. The{" "}
          <a
            href={`${PUBLIC_GITHUB_REPO}/blob/main/PUBLICATION_POLICY.md`}
            className="text-accent underline"
          >
            publication policy
          </a>{" "}
          records the exact standard.
        </p>
      </section>

      <section className="mt-10 rounded border border-rule bg-panel p-5">
        <h2 className="m-0 text-[15px] font-semibold">Related</h2>
        <ul className="mt-3 m-0 list-none space-y-2 p-0 text-[14px]">
          <li>
            <Link href="/evidence/" className="text-accent underline">
              Evidence quality ledger
            </Link>
          </li>
          <li>
            <Link href="/methodology/" className="text-accent underline">
              Methodology invariants
            </Link>
          </li>
          <li>
            <Link href="/methods-paper/" className="text-accent underline">
              Methods and limitations working paper
            </Link>
          </li>
          <li>
            <Link href="/stats.json" className="text-accent underline">
              Machine-readable corpus census (stats.json)
            </Link>
          </li>
          <li>
            <Link href="/updates/" className="text-accent underline">
              Public updates log
            </Link>
          </li>
          <li>
            <a
              href={PUBLIC_GITHUB_REPO}
              className="text-accent underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              Source repository
            </a>
          </li>
        </ul>
      </section>
    </div>
  );
}
