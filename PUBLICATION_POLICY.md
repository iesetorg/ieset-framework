# Public publication and change-control policy

IESET's public repository contains the research substrate needed to inspect,
reproduce, challenge, and cite the framework. It does not contain operator
automation, credentials, private dispatch material, personal-device metadata,
or unpublished control state.

## Institutional authorship

- Public commits, pull requests, releases, and repository administration use
  the `iesetorg` GitHub organization/account surface.
- Public-facing authorship is IESET. Personal operator identity is not a
  research dependency and is not required for attribution.
- The institutional contact for public engagement and security reports is
  `info@ieset.org`.

## Required gates

Every change to the public default branch must pass:

1. schema and cross-reference validation;
2. strict pre-registration-index validation;
3. evidence-tier and estimator-floor freshness checks;
4. definition-bearing public census freshness;
5. public OPSEC tree and commit-metadata checks;
6. web tests and a full static export.

Generated audit artifacts are committed with the research change they
describe. The site, APIs, scoreboard, and LLM discovery files must use those
artifacts rather than independently invented counters or inclusion rules.

## History and releases

- Ordinary default-branch history is append-only.
- A forced rewrite is permitted only to remove exposed private or security
  material. The replacement tip must pass the full public OPSEC and integrity
  suite before it is published.
- A release identifies one exact git commit and publishes its tag, changelog,
  census schema, and evidence-tier schema.
- IESET does not claim a cryptographically signed release, DOI, or independent
  archive timestamp unless the public release page links to verifiable proof.
- External archive deposits are additive: they do not replace the public git
  history or per-hypothesis registration proof.

## Corrections and review

Specific challenges are accepted through the public contribution process.
Accepted corrections update the affected spec, result, audit artifact, and
scoreboard in one reviewable change. External review counts include only
completed third-party review logs; internal audits are labelled as internal.

No bounty programme is active unless a separately published round identifies
its funding, scope, adjudication rule, and payout ledger.
