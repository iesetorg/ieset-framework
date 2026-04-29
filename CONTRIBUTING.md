# Contributing

This framework depends on adversarial contributions. Reviewers with priors different from the author's are the most valuable contributors — their submissions are the mechanism by which the "legibly biased, structurally open" design works in practice.

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
"Your invariant #N is wrong / impossible to enforce / too strict." Open an issue. Methodological changes require explicit commit messages and (once Phase 6 infrastructure is live) opposing-prior reviewer sign-off.

## Bounties

Successful challenges that change a coefficient, overturn a falsification, or identify a methodological error are paid in USD. Bounty amounts, criteria, and payout history are maintained in `review/bounties/README.md`. Contributions that update the author's priors *against* the disclosed direction are weighted higher.

## Public review log

Every contribution — accepted, rejected, or partially-accepted — is logged in `review/log/` with reasoning. Transparency is the mechanism. A contribution that is rejected gets a logged reason, and the reason is inspectable.

## What is out of scope

- Rhetorical reframings without data or specification substance.
- Ideological assertions unsupported by citation.
- Demands that specific conclusions be reached regardless of evidence.
- Identity-based objections ("you're not a credentialed economist"); the methodology is the methodology regardless of who applies it.

## Process

1. Open an issue first, even for small things. This keeps the public review log coherent.
2. For PRs: fork, branch, submit. Include `review/submissions/<date>_<short-name>.md` describing the submission and any prior you are disclosing about yourself.
3. The author reviews; outcomes are logged in `review/log/`.
4. Bounty-eligible successful contributions get paid and publicly credited (unless the contributor requests anonymity, which is honoured).

## Reviewer priors — disclosure reciprocity

Contributors are encouraged (not required) to disclose their own priors in their submission. This reciprocity makes the review process legibly asymmetric: contributions from reviewers whose disclosed priors differ from the author's count more toward the framework's structural-openness claim.

## Code of conduct

Engage with the strongest version of the position you disagree with. Write for the public review log, not for point-scoring. The framework's credibility is the shared asset; undermining its reviewer pool by hostile posture hurts everyone using the system.
