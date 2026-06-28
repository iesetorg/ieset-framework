# Methodology

This document defines the methodological invariants that every hypothesis, dataset, and model in IESET must satisfy. These are enforced in CI where possible and by review where not.

Changes to this document are themselves tracked in git history. An invariant cannot be silently relaxed — a weakening requires a visible commit with stated reasoning.

---

## The seven invariants

### 1. Pre-registration precedes estimation

Every hypothesis YAML (`hypotheses/<topic>/<id>.yaml`) is committed to git **before** any run artifact for that hypothesis is created. The first git commit of a spec is its pre-registration timestamp. That timestamp is the authoritative record that the hypothesis, its variables, its sample, its estimator, and its falsification criterion existed before the data was examined.

**Enforced by:** `scripts/check_preregistration.py` (CI), which fails if any file under `engine/runs/<id>/` has a filesystem mtime earlier than the first git commit of `hypotheses/**/<id>.yaml`.

**If a spec must change after the first run:** do not edit the v1 spec. Create a `v2` version in the same file under a `version: 2` block, commit it separately, and leave v1 immutable in history. Changing sample, variables, estimator, or falsification criterion of a v1 spec post-run is forbidden.

### 2. Provenance to publisher

Every cell in every table used in any model run resolves to a publisher API call or bulk download URL, with fetch UTC and source URL preserved in metadata.

**Enforced by:** fetchers must emit a `FetchResult` containing `source_url`, `publisher`, `license`, `fetch_utc`, `methodology_url`, and a SHA256 of the payload. Manifests in `data/manifests/` record every fetch. A result card that cites a coefficient whose underlying data has no manifest entry is a CI failure.

### 3. Policy-content coding, not coalition coding

Country-year ideology panel variables are scored by **what a government did**, not by its party label. Schröder's Agenda 2010 labour reforms (2003-2005, SPD-Green coalition) score as market-oriented. Trump's 2018-2019 tariffs score as state-interventionist in trade, regardless of the Republican label. See `hypotheses/country_year_ideology/codebook.md` (when created) for the canonical worked examples.

**Enforced by:** review. Every ideology-panel contribution must reference the codebook's worked examples. CI flags changes to the panel without a codebook reference.

### 4. Channel-separated fiscal and regulatory intervention measurement

Fiscal intervention (tax-and-transfer footprint) and regulatory intervention (market rule-setting) are measured on independent indices, even though they correlate empirically (r≈0.74 in Western democracies 2010-2025). A hypothesis that claims "intervention caused X" must specify which channel.

**Enforced by:** schema. Any hypothesis whose variables include an intervention measure must identify it as `fiscal`, `regulatory`, or (rarely, with justification) `bundled`.

### 5. Trajectory over snapshot

The default analytical lens is within-country change over time, not cross-section at a point in time. A hypothesis that relies only on cross-sectional comparison must include a trajectory-based robustness check or justify in its spec why trajectory is inappropriate for the question.

**Enforced by:** schema (`sample.temporal_structure` must be `panel`, `time_series`, or `cross_section_with_justification`) and review.

### 6. Second-order mechanism accounting before public promotion

Policy experiments do not earn high-integrity public promotion from headline outcomes alone. A policy test must either measure the second-order channels implied by its coded axes or explicitly mark those channels as data gaps. For price controls and rent control this includes shortages, quality, search or queue costs, entry and exit, supply response, leakage, distributional incidence, and net welfare. For other policies the required layers are inherited from `axes.yaml`.

**Enforced by:** schema and audit. Policy specs may declare `evaluation_design`; axes declare `second_order_measurement`; `scripts/audit_second_order_measurement.py` and `engine/policy_second_order_requirements_index.*` expand every policy into required layers, preferred designs, and source-family gaps. Claims that lack the required mechanism contract remain candidate, descriptive, or screen-only until the missing layers are measured.

### 7. Authored, reproducible, open to correction

IESET is an authored framework, not an anonymous consensus document. [DISCLOSURE.md](DISCLOSURE.md) records the author's perspective and broad economic exposure. Every hypothesis YAML includes a pre-run `prior_confidence`, not as a badge of truth, but as an audit marker for how surprising the result was expected to be. The framework's defence is reproducibility and correction: pre-registration commits, public replication code, challengeable mappings, and visible updates when a test changes the record.

**Enforced by:** every hypothesis YAML must include a `disclosure` field and a non-null `prior_confidence` in `[0, 1]`.

---

## Causal-claim requirements

A hypothesis that asserts a causal relationship (not merely a correlation) must satisfy one of:

- **Two-spec rule.** Ship two independently-motivated specifications (e.g., DiD + synthetic control, or panel FE + IV) whose point estimates agree in sign and agree within a factor of two on magnitude.
- **Natural experiment.** A documented exogenous shock, with placebo tests, balance checks, and parallel-trends diagnostics reported in the result card.
- **Decomposition.** A channel decomposition whose residual is reported honestly and subjected to a falsification threshold (e.g., Nordic decomposition §D.2.9: residual > 30% of gap falsifies).

Single-spec causal claims do not ship. Correlational-only claims are permitted but must be labelled `evidence_type: associational` in the spec.

---

## Vintage policy

Data is never overwritten. A revised release from a publisher creates a new vintage file: `<publisher>/<series>@<fetch_utc>.parquet`. The manifest records which runs used which vintages. A run that used vintage A remains reproducible from vintage A even after vintage B exists.

When a new vintage materially changes a coefficient (sign change or >1σ movement), the hypothesis page surfaces this as a "vintage alert" rather than silently updating the displayed result.

---

## Multi-source disagreements

When two publishers disagree on a series (e.g., OECD vs IMF on a country's debt/GDP), the hypothesis may use only one, but the spec must name it and the metadata must link to the alternative. The hypothesis page surfaces the disagreement on inspection.

---

## Steelman requirement

Every hypothesis in `hypotheses/` must have a corresponding markdown file in `hypotheses/steelman/<id>.md` that presents the strongest opposing argument, written charitably. An empty or placeholder steelman is a review failure.

---

## What happens when a hypothesis is falsified

Falsification is not failure — it is the framework working. A falsified hypothesis:

1. Remains in the library (never deleted).
2. Has its result card updated to state: "Falsified. Prior was X; post-run belief is Y; reasoning below."
3. Triggers a public note in `/updates` on the platform.
4. Counts positively toward framework credibility, not negatively.

Framework updates that move against the pre-run expectation are useful stress tests. They should remain visible because they show the scoring rule can bind the framework as well as its critics.

---

## Changes to this document

Edits to `METHODOLOGY.md` require:

- A commit message that explicitly names which invariant changed and why.
- A line in the commit body naming any existing hypotheses the change affects.
- Review sign-off from at least one opposing-prior reviewer once the review infrastructure is live (Phase 6).

Before Phase 6, changes are sole-author but are logged in `review/log/methodology_changes.md` for future retroactive review.
