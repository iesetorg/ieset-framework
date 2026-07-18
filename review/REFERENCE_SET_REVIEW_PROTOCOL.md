# Adversarial reference-set review protocol

**Status:** Open protocol; no reviewer commissioned and no completed review

**Reference-set source:** `engine/evidence_tier_audit.json`
**Public ledger:** https://framework.ieset.org/evidence-tiers.json

## Purpose

This protocol makes the first external review finite and falsifiable. It asks a
reviewer with no role in the original specifications to attack the six-record
reference set. The set is deliberately balanced across verdict directions and
policy areas. It is a review queue, not a claim that the records are already
gold-standard evidence.

The review should answer whether IESET's public evidence gate is too permissive,
whether each result follows from its registered rule, and whether the public
summary is materially more confident than the design supports.

## Independence disclosure

Before starting, the reviewer should disclose:

- relevant training or professional experience;
- prior public work on any included topic;
- financial or organizational conflicts;
- prior collaboration with IESET; and
- broad economic-policy priors, in whatever terms the reviewer considers fair.

Expertise is useful context, not a substitute for a reproducible objection.
Opposing priors are welcome but not required.

## Frozen review packet

The review log must identify one immutable repository commit. At that commit,
freeze:

1. `engine/evidence_tier_audit.json`;
2. each reference-set hypothesis specification;
3. each corresponding `engine/runs/<hypothesis_id>/` directory;
4. the relevant replication scripts and pinned data-vintage records;
5. `METHODOLOGY.md` and `METHODS_PAPER.md`; and
6. the generated `stats.json` and scoreboard API output.

Changes after the frozen commit may be cited as responses but must not replace
the material under review.

## Required checks for every record

Score each item `pass`, `minor finding`, `major finding`, or `not assessable`.
Every non-pass result should cite a file, line, command output, or primary
source.

### A. Registration

- Does the first specification commit strictly precede the first run commit?
- Did any material outcome, estimator, sample, threshold, or exclusion rule
  change after execution without being labelled as a new version?
- Is the displayed registration proof the first specification commit rather
  than repository head?

### B. Data provenance

- Can the analytical input be traced to a named primary publisher?
- Are series identifiers, transformations, fetch metadata, and content hashes
  sufficient to locate or reconstruct the input?
- Are missing values, revisions, units, deflators, and geographic joins handled
  defensibly?

### C. Execution

- Does the committed command reproduce the reported result in the documented
  environment?
- Is the executed estimator the registered primary estimator?
- Do rank, convergence, uncertainty, and sample diagnostics clear the published
  estimator floor?

### D. Identification and inference

- Does the evidence-type label match the actual design?
- Are treatment timing, comparison units, pre-trends, spillovers, and concurrent
  shocks handled well enough for the stated claim?
- Does the result survive at least one reasonable specification or measurement
  alternative that was not chosen to favour the reported direction?

### E. Verdict and presentation

- Does the verdict follow mechanically from the registered threshold?
- Does `PARTIAL`, subset, or weakened language preserve the failed component?
- Does the plain-language summary stay within what the design identifies?
- Is featured or calibration tier membership justified under the generated
  rules?

### F. School attribution

- Is the school prediction specific enough to have failed?
- Is its polarity correct?
- Does credit depend on a failure mechanism the study did not measure?
- Do the integrity and second-order gates prevent unsupported school-level
  inference?

## Reviewer deliverables

Submit:

1. an executive conclusion of no more than 500 words;
2. the completed per-record checklist;
3. reproducibility commands and environment notes;
4. a findings table with severity and affected files;
5. any proposed patches or alternative specifications; and
6. a statement of whether the reviewer believes each record should remain
   featured, move to calibration, or move to archive.

Use `review/submissions/TEMPLATE.md` and put supporting material in a branch or
permanent external archive. The final disposition belongs in `review/log/`.

## Severity

**Major finding:** could change the verdict, tier, registration status, public
summary, or school-level credit.

**Minor finding:** improves reproducibility or wording but is unlikely to change
evidentiary standing.

**Not assessable:** the public packet is insufficient. Missing evidence is
itself a major finding when the framework claims the relevant gate passed.

## IESET response standard

For each finding, IESET will publish one of:

- accepted and corrected;
- accepted, correction pending;
- disputed with a reproducible reason; or
- out of scope with a specific reason.

The original submission remains public. Corrections must name affected records,
update generated ledgers and counters, and appear in the public updates feed.
No favorable review language may be quoted without linking the complete review.

## Bounty and payment status

This protocol does not open a bounty or promise payment. A paid round exists
only after a pre-funded amount, eligibility rules, adjudication process, and
payout ledger are published in `review/bounties/README.md`.
