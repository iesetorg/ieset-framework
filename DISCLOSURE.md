# Transparency

IESET is not an anonymous oracle. It is an authored research framework with
published methods, public code, registration records, and reproducible results.
This page records the commitments that matter for interpreting the work.

The core integrity claim is methodological: hypotheses are written before
estimation, data vintages are pinned, result cards expose the rule used to score
the run, and contrary findings remain visible.

---

## Maintainer perspective and privacy

IESET is independently maintained. The maintainer's personal identity, home
directory, device names, addresses, counterparties, and line-item holdings are
not part of the research record and are intentionally kept private.

The framework has explicit priors and puts unusual weight on:

- separating fiscal footprint from regulatory constraint;
- measuring policy trajectories rather than one-year country labels;
- asking whether an intervention creates durable surplus, redistributes a fixed
  surplus, or reduces the base being redistributed;
- preserving enough provenance that a critic can reproduce or challenge a run.

Those are starting points for inquiry, not protected conclusions.

---

## Conflicts and economic exposure

The maintainer may have financial or professional interests relevant to topics
in the corpus. When an interest bears directly on a hypothesis, the spec should
carry a concise conflict note describing the category and direction of the
possible bias. Personal identity, exact holdings, addresses, position sizes, and
third-party information are not published.

## Automation and external review

IESET uses automated and model-assisted tools for drafting, coding, data
acquisition, replication, and quality checks. Those tools are production aids,
not independent authors or reviewers. A published artifact remains unrefereed
unless its page links to a completed external review in `review/log/`.

Internal prompts, provider routing, budgets, credentials, device details, and
operator briefs are operational security material and are not part of the
public evidence substrate.

---

## Operating Commitments

IESET commits to:

1. pre-registering hypotheses before estimation;
2. keeping falsification rules attached to the result after the run;
3. publishing contrary, partial, and inconclusive results rather than filtering
   them out;
4. preserving data provenance and code paths for replication;
5. keeping charitable opposing arguments attached to important claims;
6. accepting specific corrections when a critic finds a coding, data, or
   interpretation error.

This is a transparency model, not a neutrality or peer-review claim. Readers
should judge the framework by whether the methods are inspectable, the evidence
is reproducible, limitations are prominent, and the scoreboard updates when the
record moves.

---

## Updates

Material changes to this transparency note appear here as dated entries.

- **Initial publication** — Established framework-level transparency for author
  perspective, broad economic exposure, and pre-registration commitments.
- **Indicator-set integrity** — Added the canonical-basket gate after an audit
  found that several social-outcome specs could overstate support by selecting
  favourable indicators. The gate now caps such verdicts at
  `supported_subset`.
- **Tone revision** — Condensed the disclosure model from exhaustive author
  narrative into a shorter transparency note. The framework keeps the same
  methodological commitments without foregrounding biography or conflict
  language on every reader path.
- **Operational-security revision (2026-07-17)** — Removed personal-device
  metadata and internal control-plane material from the public repository;
  added a high-level automation disclosure and per-hypothesis conflict model.
