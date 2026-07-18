# IESET: a registered, machine-assisted evidence framework for economic-policy claims

**Working methods and limitations note · Version 1.2.0 · 18 July 2026**

**Institutional author:** IESET

**Contact:** info@ieset.org

**Canonical version:** https://framework.ieset.org/methods-paper/

**Code and evidence:** https://github.com/iesetorg/ieset-framework

**Status:** Public working paper; not peer-reviewed

## Abstract

IESET is an open framework for turning economic-policy claims into explicit,
versioned empirical tests. It links a hypothesis specification, falsification
rule, public-data provenance, replication code, result card, and school-level
prediction mapping in one inspectable repository. The corpus is produced with
large-language-model assistance under human direction. Models help draft,
retrieve, code, and audit; they are not treated as evidentiary authorities.

The framework's central methodological choice is to separate *volume* from
*credit*. A generated evidence ledger assigns records to featured,
calibration, or archive tiers. Strict registration topology, replication
availability, falsification-rule specificity, verdict eligibility, and an
estimator floor determine whether a record can support public claims. Archive
records remain visible for audit but receive no headline or scoreboard credit.

The present school-level result is a null: after attribution and integrity
gates, the ranked schools have not been separated at high integrity. This note
documents the framework, the controls added after public audit, and the
remaining threats to validity. It does not claim that the corpus is
peer-reviewed or independently validated.

## 1. Research problem

Economic-policy arguments often move between levels without making the move
explicit. A school of thought makes a broad prediction; a policy is described
under a partisan label; a later outcome is treated as evidence for a mechanism;
and the mechanism is then generalized to a different institutional setting.
IESET tries to make each link inspectable.

The unit of work is not an essay or an ideological score. It is a registered
hypothesis with:

1. a directional or threshold-bearing claim;
2. a named sample and time window;
3. a primary estimator or comparison design;
4. an explicit falsification rule;
5. a steelman and rival explanations;
6. public-data sources and pinned vintages;
7. a reproducible run and diagnostic record; and
8. any school-level prediction links, including their polarity.

Policy and movement records are coded separately from hypotheses. This avoids
treating a government label as a measurement of what that government did.

## 2. Registration and temporal ordering

Registration status is derived from git history, not from the current
repository head.

- `verified` means the first commit adding the hypothesis specification is a
  strict ancestor of the first commit adding a run artifact.
- `legacy_same_commit` means specification and run first entered history
  together. The record remains inspectable but receives no verified
  pre-registration credit.
- `registered_no_run` means a prospective specification exists without a
  recorded result.
- `invalid_history` means the required ordering cannot be established.

The hypothesis page links the first specification commit and shows the run
timestamp separately. This is only a self-hosted history proof. It is not a
substitute for an independent registry, and the framework makes no independent
timestamp claim until an external deposit is linked.

## 3. Data provenance and execution

The intended data path is:

`publisher source → pinned vintage → content hash → committed replication code → diagnostics → result card`

Primary publishers are preferred. A data source name alone is insufficient:
the repository is intended to retain enough information to locate the series,
identify the fetch, and reproduce the analytical input. The result card
records the estimator, sample, outcome, diagnostic status, and verdict rule
used by the public interface.

This design improves inspectability; it does not make source data correct or an
identification strategy valid. Data revisions, undocumented transformations,
measurement error, treatment misclassification, and institutional
non-comparability remain substantive risks.

## 4. Verdicts and the estimator floor

Verdicts are mechanical labels attached to a pre-specified rule:

- `SUPPORTED` indicates that the support threshold cleared.
- `PARTIAL` indicates incomplete or directional agreement short of the full
  support rule.
- `REFUTED` indicates contrary evidence under the registered rule.
- inconclusive, blocked, and pending states receive no directional credit.
- subset or weakened states retain their stated limitation.

A directional label cannot receive public evidence credit when diagnostics
show that the primary estimator failed, the design matrix was rank-deficient,
a fallback estimator replaced the primary, the estimated magnitude was
effectively zero despite a directional verdict, or required uncertainty could
not be estimated. The record is preserved with its diagnostic trail and placed
in the archive tier.

This floor was introduced because publication of a diagnostic is not the same
as preventing that failed diagnostic from influencing a headline. Both are
necessary.

## 5. Public evidence tiers

The generated tier ledger is the authority for inclusion.

**Featured.** Strict registration, public method gates, estimator floor, and a
causal-design label pass without first-pass screening markers. Featured does
not mean peer-reviewed.

**Calibration.** Strict registration and public method gates pass, but the
design is associational, descriptive, a canonical-case check, or otherwise
lower-identification. These records may be useful for pipeline calibration and
context, with the caveat carried into any claim.

**Archive.** One or more public-credit gates fail. The result remains directly
inspectable but cannot move the scoreboard or support a headline conclusion.

A small balanced reference set makes external review tractable. It is a review
queue, not a quality override or a gold-standard claim.

Current counts, definitions, exclusion reasons, and reference-set membership
are generated rather than copied into this paper:

- https://framework.ieset.org/stats.json
- https://framework.ieset.org/evidence-tiers.json

## 6. School-level scoring

A result does not automatically support every school linked to it. Each school
record contains a prediction and expected polarity. The scoreboard retains
three views:

1. a raw directional score;
2. a forecast-quality score discounted by identification strength; and
3. an attribution-aware integrity score further discounted for weak claim
   links, screening designs, unsupported failure mechanisms, and missing
   second-order measurements.

Benchmark controls are reported separately from ranked schools. Small numeric
differences inside the published no-call band are not interpreted as a
substantive ranking. The current strict conclusion is that no ranked school has
been separated at high integrity.

## 7. Machine-assisted production

IESET is LLM-assisted under human direction. Models can propose specifications,
write code, retrieve candidate sources, summarize diagnostics, and draft
result prose. This creates speed and breadth, but also correlated error,
automation bias, citation error, duplicated assumptions, and the risk that
plausible prose outruns the analysis.

The public safeguard is artifact-based:

- a model statement is not evidence;
- committed specifications and data lineage are inspectable;
- execution code and diagnostics are preserved;
- strict gates determine public credit;
- public counts are generated from one census;
- corrections are made in versioned history.

Private operator automation, credentials, local paths, and dispatch state are
outside the public research repository. They are neither evidence nor a
claimed source of authority.

## 8. Threats to validity

### 8.1 Closed-loop authorship

The same institutional project proposes, executes, and grades most records.
Registration reduces some researcher degrees of freedom but cannot replace an
independent adversary. Until external review exists, results must be described
as unrefereed.

### 8.2 Retrospective and canonical-case tests

Some records reproduce well-known historical patterns. They can validate
plumbing and measurement, but they are weaker evidence of discovery and should
not be treated as equivalent to prospective or quasi-experimental tests.

### 8.3 Multiple testing and corpus selection

A large registry creates opportunities for selective emphasis even when every
record is public. The tier ledger reduces this risk by defining public credit
mechanically, but it does not supply family-wise inference across unrelated
questions.

### 8.4 Construct and external validity

Economic concepts are represented by measurable proxies. A result may be
internally correct for a series while failing to measure the broader construct
used in public debate. Cross-country and cross-period transportability must be
argued, not assumed.

### 8.5 School attribution

Schools are internally diverse and evolve over time. Prediction mappings are
authored interpretations, not surveys of every adherent. Attribution discounts
and a no-call band limit overstatement but do not eliminate interpretive
judgment.

## 9. External validation status and next tests

At this version:

- the corpus is not peer-reviewed by default;
- no completed external review or challenge submission is claimed unless
  counted in the public census;
- no active bounty programme or payout is claimed;
- no DOI, release signature, or independent archive timestamp is claimed
  without a linked proof.

The next legitimacy tests are deliberately external:

1. adversarial review of the balanced reference set by a reviewer with
   opposing priors;
2. public responses and corrected artifacts for every sustained finding;
3. an independently timestamped versioned deposit;
4. expansion of prospectively registered tests whose execution follows a
   meaningful delay and data release; and
5. replication by parties who did not author the original specifications.

## 10. Data, code, corrections, and citation

The public repository contains the framework code, research specifications,
data provenance records, runs, and site source:
https://github.com/iesetorg/ieset-framework

The evidence ledger and data catalog are available at:

- https://framework.ieset.org/evidence/
- https://framework.ieset.org/api/catalog.json

Correction and review instructions are available at:
https://framework.ieset.org/contribute/

Until an external identifier exists, cite the versioned repository and
canonical methods-paper URL. Do not infer peer review, a DOI, or independent
validation from the existence of this working paper.
