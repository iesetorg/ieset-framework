# IESET

**An open, empirical framework for contemporary economic policy questions.**

The framework combines a versioned data substrate, a registry of economic
hypotheses, an open correction protocol, and a public web platform that links
every claim to its data, method, and historical analogues. Published results are
research artifacts, not peer-reviewed findings, unless a result page links to a
completed external review.

Corpus counts change frequently. The machine-readable census at
`engine/public_corpus_census.json` defines and records each count; CI rejects a
stale census. Treat that file—not marketing copy or an older deployment—as the
authoritative corpus count.

The machine-readable evidence ledger at
`engine/evidence_tier_audit.json` separately publishes strict-registration
status, estimator-floor findings, public-credit exclusions, and the
`featured` / `calibration` / `archive` tier for every hypothesis. The public
site explains those rules at <https://framework.ieset.org/evidence/>.

---

## Why this framework

Most public economic argument is one of two things — political-coalition coding ("the left says X, the right says Y") or unfalsifiable narrative ("the experts agree"). Both leave the reader unable to distinguish a claim that survived a real test from one that was never tested.

IESET is structured to fix that:

1. **Pre-registration** — New prospective tests commit a falsifiable threshold before their first run. Git topology verifies strict spec-before-run ordering; historical same-commit records remain inspectable but do not receive verified pre-registration credit.
2. **Falsification-first verdict semantics** — Verdicts are `SUPPORTED`, `supported_subset`, `partial`, `refuted`, `weakened`, or `inconclusive`. There is no "interesting result" or "suggestive evidence" — every run lands in one of those tiers based on its recorded rule.
3. **Channel-separated policy axes** — A movement's coalition label (left, right, populist) is decoupled from its policy content (fiscal stance, regulatory burden, monetary regime, openness, distribution). The framework codes axes, not coalitions.
4. **Vintaged data substrate** — Every datapoint carries `(publisher, series, vintage_utc, sha256)`. A re-run from a year later picks up the new vintage; the old run remains reproducible against the old vintage forever.
5. **Open correction** — Anyone can submit a coherent challenge to a verdict via the `review/` process. The review log is currently a pilot and had received no external submissions as of 2026-07-17; it must not be described as completed peer review.
6. **Indicator-set integrity** — For social-outcome claims (basic needs, wellbeing, human development, poverty), the spec must enumerate the canonical-literature basket and either test each dimension or document it as a data gap. Omitted canonical dimensions cap the verdict at `supported_subset`. This catches the upstream gaming pattern that pre-registration alone cannot reach.
7. **Second-order policy measurement** — Policy tests must measure or disclose the mechanism layers implied by their axes: supply response, quality, substitution, incidence, enforcement cost, macro feedback, and net welfare where relevant. A price or rent control that only measures the controlled price is not scoreboard-grade evidence; it is a candidate screen until the shortage, quality, supply, search-cost, and welfare channels are tested.

These seven invariants are spelled out in `METHODOLOGY.md`.

---

## How to read a verdict

Every hypothesis page on the public site shows:

- **Verdict tier and tone** — green / amber / red / muted, parsed from the first word of the verdict string
- **Primary statistic and threshold** — the one number the run was designed to test, plus the line it had to clear or fall below
- **Method-validity gate** — what would have to be true for the run to be informative; failures emit `inconclusive`, not `refuted`
- **Steelman doc** — the strongest counter-argument the spec author could write before grading
- **Replication trail** — `engine/runs/<id>/replication.py` is the literal script that produced the verdict, plus `manifest.yaml` pinning every input series by `(publisher, series, vintage_utc, sha256)`
- **Linked policies, movements, positions** — what historical analogues the test draws on, what schools of thought the verdict bears on

The registration record is visible. A green verified badge requires the spec
commit to be a strict ancestor of the first run commit; legacy same-commit
records carry an amber, unverified label.

Evidence standing is also explicit:

- **Featured** — strict registration, public method gate, estimator floor, and
  causal-design label passed, with no screening markers.
- **Calibration** — public and method-valid, but associational, descriptive,
  canonical-case, or screening-grade.
- **Archive** — inspectable history that receives no headline or scoreboard
  evidence credit.

The six-record reference set is a balanced external-review queue, not a claim
of peer review. Current inclusion counts and every exclusion reason live in the
evidence ledger rather than in prose.

---

## How to challenge a verdict

The verdict isn't the end — it's the latest reading. Anyone can submit:

- A **methodological challenge** — argue the spec's threshold was wrong, the method had an identification flaw, or the canonical-basket coverage is incomplete
- A **data challenge** — show that a different vintage, publisher, or series yields a different result
- A **scope challenge** — argue the spec answers a narrower question than the claim implies

Submit via PR with the `review/` template. The maintainer writes a steelman of
the challenge; either the original verdict survives with a public note of the
unsuccessful challenge, or the spec is bumped to v2 with the challenge
integrated and the old run archived. See `review/README.md` for the current
pilot status.

The framework treats successful challenges as wins, not failures. The integrity audit on Cuba × 2 + Japan + Costa Rica + single-payer that produced the `supported_subset` tier and the canonical-basket gate started exactly this way — a reader pointing out that the tested indicators were a favourable subset of the canonical-literature basket.

---

## Honest limit: economic vs social-policy data asymmetry

The on-disk data publishers (WDI, FRED, IMF, OECD-macro, PWT, BIS, ECB, BoE, FAO partial, WHO-GHO partial) cover **economic** outcomes well — growth, inflation, productivity, fiscal multipliers. They are thin on **social-policy** outcomes — food security at sub-annual resolution, mental health, subjective wellbeing, time poverty, housing affordability, amenable mortality, healthcare quality.

This asymmetry biased early social-outcome specs toward `SUPPORTED-on-favourable-subset` gaming. The canonical-basket gate (invariant 6 above) catches it: a spec that omits a literature-canonical dimension lands `supported_subset` (amber, not green) until the missing evidence lands.

Concrete: claims like *"Costa Rica achieves high wellbeing at low throughput"* that look SUPPORTED on life expectancy + CO2 alone come back **refuted** when the canonical safety leg (homicide rate) is added — Costa Rica's homicide rate is 2.19× the US in 2010-2020. That's the gate working.

The framework is structurally honest about what it can and can't dispositively test. Closing the social-policy fetcher backlog is what makes social claims dispositively gradeable rather than `supported_subset` perpetually.

---

## Repository layout

```
data/          publisher fetchers, normalisation, vintaged parquet contracts
  fetchers/    one fetcher per publisher (FRED, WDI, IMF, OECD, PWT, BIS, BoE, ECB, FAO, WHO, etc.)
  manifests/   per-fetch-run manifest with sha256 + retrieval timestamp
  vintages/    @utc-stamped parquet (gitignored — populated by fetcher runs)

engine/        econometric templates, run registry, replication scripts
  runs/        one folder per hypothesis run; replication.py + 5 artifacts each

hypotheses/    registered hypotheses + registration status (YAML schemas)
  topic/       organised by economic topic (growth, fiscal, monetary, distribution, etc.)
  steelman/    steelman docs (strongest counter-argument per hypothesis)

policies/      individual policies (interventions) coded by axes
movements/     political movements with timeframe + policy_ids + axis trajectory
positions/     16 ranked schools plus one separately reported benchmark control

axes.yaml      the policy-content taxonomy (fiscal, regulatory, monetary, openness, distribution)

web/           public Next.js platform + API
review/        open-correction pilot + submitted challenges
schemas/       JSON schemas for every YAML kind

scripts/       CI and maintenance (validate_specs, derive_coverage, etc.)
tests/         pytest suite

HYPOTHESIS_FRAMEWORK_AUDIT.md   lineage of methodological refinements
```

---

## Quickstart

### Run the public site locally

```bash
cd web
npm install
npm run dev
# → http://localhost:3000
```

### Validate the spec library

```bash
.venv/bin/python scripts/validate_specs.py
# → validates schemas and cross-references
```

### Run a hypothesis

```bash
# 1. Land the data
FRED_API_KEY=... .venv/bin/python scripts/fetch.py fred CPIAUCSL

# 2. Run the replication
.venv/bin/python engine/runs/volcker_disinflation_output_recovery/replication.py
# → SUPPORTED — CPI YoY fell from 14.4% peak to 3.2% in 1983Q4 (drop 11.2pp)...

# 3. Verify pre-registration timestamp
.venv/bin/python scripts/check_preregistration.py --check-index
```

### Add a new hypothesis

```bash
# 1. Write the spec (commit BEFORE running)
git add hypotheses/<topic>/<id>.yaml hypotheses/steelman/<id>.md
git commit -m "pre-register: <id>"

# 2. Validate
.venv/bin/python scripts/validate_specs.py

# 3. Author engine/runs/<id>/replication.py mirroring
#    engine/runs/post_2008_oecd_growth_emissions_path/replication.py

# 4. Run + commit artifacts
.venv/bin/python engine/runs/<id>/replication.py
git add engine/runs/<id>/
git commit -m "run: <id> — <verdict>"
```

The pre-registration invariant is enforced: the spec commit must be a strict
ancestor of the first run commit.

---

## Status

This is **v1.2** of the public platform. The public repository is restricted to
the research substrate and its verification tooling. Publication,
institutional-authorship, release, and history-rewrite rules are documented in
`PUBLICATION_POLICY.md`.

Open work:
- Executing the generated
  [next-200 strict-scoreboard upgrade queue](engine/audits/next_200_scoreboard_data_gap_roadmap_2026-07-19.md),
  regenerated after each 50-candidate wave
- Closing documented source-family and social-policy data gaps
- Expanding the engine's estimator templates beyond the current panel-FE / event-study / synth-DiD / local-projections set
- Building out and independently exercising the external-review pilot

---

## Licence

- **Code** (everything under `data/fetchers/`, `engine/`, `scripts/`, `web/`, `tests/`): Apache-2.0 — see [LICENSE](LICENSE).
- **Spec library + run artifacts** (everything under `hypotheses/`, `policies/`, `movements/`, `positions/`, `axes.yaml`, `engine/runs/*/diagnostics.json`, `engine/runs/*/result_card.md`): CC-BY-4.0 — see [LICENSE-DATA](LICENSE-DATA). Cite as the schema's `permalink` field.

The split is deliberate. Code wants maximum reuse (Apache-2.0). The spec library is a research artifact whose audit and correction history matters; CC-BY ensures attribution survives forks.

---

## Cite

```bibtex
@misc{ieset_framework,
  title = {IESET — An empirical economic-policy research framework},
  author = {{IESET}},
  year = {2026},
  url = {https://github.com/iesetorg/ieset-framework},
  note = {Verdict-tier audit trail and indicator-integrity gate.}
}
```

A machine-readable `CITATION.cff` is in the repo root.

---

## Maintainer and automation disclosure

Per `DISCLOSURE.md`, IESET is independently maintained and uses automated and
model-assisted tooling. Automation is not an independent reviewer. Relevant
conflicts are disclosed at hypothesis level without publishing personal
identity, addresses, counterparties, or holdings. The correction channel exists
so external readers can challenge verdicts; until such a review is logged, a
result remains unrefereed.
