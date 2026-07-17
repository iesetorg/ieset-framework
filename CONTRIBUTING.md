# Contributing

This framework depends on specific, evidence-backed contributions. The most valuable submissions identify a data problem, specification weakness, mapping error, or stronger opposing argument that changes what the framework should publish.

## Public repository scope

The public repository contains research specifications, source provenance,
replication code and results, methodology, validation, and the public site.
Credentials, local paths, operator notes, private automation, outreach,
administrative plans, and unrelated applications belong outside this
repository.

## Kinds of contribution

### 1. Data challenges
"Your series X from publisher Y is wrong / stale / uses the wrong methodology." Open an issue; include publisher citation and why the current series is inappropriate. If accepted, we add a new fetcher or switch the series and re-run affected hypotheses.

### 2. Specification challenges
"Your hypothesis Z is specified in a way that biases the result." Open an issue or PR; include an alternative specification with justification. If the alternative is reasonable, we add it as an additional spec (`version: 2`) and publish both. If the alternative changes the conclusion, we update the hypothesis prominently.

### 3. Falsification challenges
"Your hypothesis Z is actually falsified under a correct reading of the data." Submit a PR that runs an alternative specification and demonstrates the falsification. If the falsification holds, we update the result card, publish the change in `/updates`, and credit the contributor.

### 4. Steelman challenges
"Your steelman file for hypothesis Z does not steelman the strongest opposing argument." Submit a PR with a stronger version. Accepted steelmans credit the contributor.

### 5. Condition taxonomy challenges
"Your condition entry for X omits institution Y or misclassifies case Z." Submit a PR with supporting cases and disconfirming cases. Taxonomy entries are living documents.

### 6. Methodological challenges
"Your invariant #N is wrong / impossible to enforce / too strict." Open an issue. Methodological changes require explicit commit messages and, once the review infrastructure is live, independent review.

## Bounties

No bounty programme is currently active, and no payout has been recorded.
`review/bounties/README.md` is the status and ledger page. If a funded bounty
round opens, its amount, eligibility rules, decision process, and payout history
will be published there before submissions are accepted.

## Public review log

External review is a pilot. No external submission had been logged as of
2026-07-17. New review submissions and their outcomes are logged in
`review/log/` with reasoning; rejected submissions receive a public reason
unless publication would expose private or unsafe material.

## What is out of scope

- Rhetorical reframings without data or specification substance.
- Ideological assertions unsupported by citation.
- Demands that specific conclusions be reached regardless of evidence.
- Attempts to identify or harass private contributors or maintainers. Relevant
  expertise and conflicts may still be raised when they bear directly on a
  claim, method, or disclosure.

## Process

1. Open an issue first, even for small things. This keeps the public review log coherent.
2. For PRs: fork, branch, submit. Include `review/submissions/<date>_<short-name>.md` describing the submission and the evidence or reasoning behind it.
3. The author reviews; outcomes are logged in `review/log/`.
4. Accepted contributions are publicly credited unless the contributor requests
   anonymity. Payment applies only when a separately published bounty round was
   open before submission.

## Reviewer Context

Contributors may include relevant context about their expertise, priors, or exposure when it helps readers interpret the submission. This is optional. The contribution is judged on its evidence, code, and reasoning.

## Code of conduct

Engage with the strongest version of the position you disagree with. Write for the public review log, not for point-scoring. The framework's credibility is the shared asset; undermining its reviewer pool by hostile posture hurts everyone using the system.
