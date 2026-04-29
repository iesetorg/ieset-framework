# IESET

**An empirically-grounded, adversarially-reviewed framework for contemporary economic policy questions.**

The framework combines a versioned data substrate, a registry of pre-registered econometric hypotheses, an open adversarial-review protocol, and a public web platform that links every claim to its data, its method, and the historical analogues it depends on.

```
272 hypotheses · 245 runs · 2,986 policies · 615 movements · 17 positions
```

| Verdict | Count | Meaning |
|---|---|---|
| SUPPORTED | 48 | clean ≥-threshold pass |
| supported_subset | 2 | passed indicators tested; canonical-literature basket has documented gaps |
| partial | 42 | direction correct but threshold missed |
| refuted | 23 | clean ≥-threshold fail |
| weakened | 6 | identification flawed; one-way refutation signal |
| inconclusive | 118 | data gap or method failure (NOT a refutation) |

> See `data/SOCIAL_FETCHER_BACKLOG.md` for the data gaps that hold many `inconclusive` and `supported_subset` verdicts. Each gap is a fetcher waiting to land; verdicts will tighten as the backlog clears.

---

## Why this framework

Most public economic argument is one of two things — political-coalition coding ("the left says X, the right says Y") or unfalsifiable narrative ("the experts agree"). Both leave the reader unable to distinguish a claim that survived a real test from one that was never tested.

IESET is structured to fix that:

1. **Pre-registration** — Every hypothesis commits a falsifiable threshold before the data is examined. Git timestamps enforce this; the engine refuses to score a run whose threshold was set after the data landed.
2. **Falsification-first verdict semantics** — Verdicts are `SUPPORTED`, `supported_subset`, `partial`, `refuted`, `weakened`, or `inconclusive`. There is no "interesting result" or "suggestive evidence" — every run lands in one of those tiers based on the pre-registered rule.
3. **Channel-separated policy axes** — A movement's coalition label (left, right, populist) is decoupled from its policy content (fiscal stance, regulatory burden, monetary regime, openness, distribution). The framework codes axes, not coalitions.
4. **Vintaged data substrate** — Every datapoint carries `(publisher, series, vintage_utc, sha256)`. A re-run from a year later picks up the new vintage; the old run remains reproducible against the old vintage forever.
5. **Adversarial review** — Anyone can submit a coherent challenge to a verdict via the `review/` machinery. A successful challenge re-opens the verdict; the audit trail is permanent.
6. **Indicator-set integrity** — For social-outcome claims (basic needs, wellbeing, human development, poverty), the spec must enumerate the canonical-literature basket and either test each dimension or document it as a data gap. Omitted canonical dimensions cap the verdict at `supported_subset`. This catches the upstream gaming pattern that pre-registration alone cannot reach.

These six invariants are spelled out in `METHODOLOGY.md`.

---

## How to read a verdict

Every hypothesis page on the public site shows:

- **Verdict tier and tone** — green / amber / red / muted, parsed from the first word of the verdict string
- **Primary statistic and threshold** — the one number the run was designed to test, plus the line it had to clear or fall below
- **Method-validity gate** — what would have to be true for the run to be informative; failures emit `inconclusive`, not `refuted`
- **Steelman doc** — the strongest counter-argument the spec author could write before grading
- **Replication trail** — `engine/runs/<id>/replication.py` is the literal script that produced the verdict, plus `manifest.yaml` pinning every input series by `(publisher, series, vintage_utc, sha256)`
- **Linked policies, movements, positions** — what historical analogues the test draws on, what schools of thought the verdict bears on

The pre-registration timestamp is visible: spec commit must predate run timestamp.

---

## How to challenge a verdict

The verdict isn't the end — it's the latest reading. Anyone can submit:

- A **methodological challenge** — argue the spec's threshold was wrong, the method had an identification flaw, or the canonical-basket coverage is incomplete
- A **data challenge** — show that a different vintage, publisher, or series yields a different result
- A **scope challenge** — argue the spec answers a narrower question than the claim implies

Submit via PR with `review/` template. The author writes a steelman of the challenge; either the original verdict survives with a public note of the unsuccessful challenge, OR the spec is bumped to v2 with the challenge integrated and the old run archived.

The framework treats successful challenges as wins, not failures. The integrity audit on Cuba × 2 + Japan + Costa Rica + single-payer that produced the `supported_subset` tier and the canonical-basket gate started exactly this way — a reader pointing out that the tested indicators were a favourable subset of the canonical-literature basket.

---

## Honest limit: economic vs social-policy data asymmetry

The on-disk data publishers (WDI, FRED, IMF, OECD-macro, PWT, BIS, ECB, BoE, FAO partial, WHO-GHO partial) cover **economic** outcomes well — growth, inflation, productivity, fiscal multipliers. They are thin on **social-policy** outcomes — food security at sub-annual resolution, mental health, subjective wellbeing, time poverty, housing affordability, amenable mortality, healthcare quality.

This asymmetry biased early social-outcome specs toward `SUPPORTED-on-favourable-subset` gaming. The canonical-basket gate (invariant 6 above) catches it: a spec that omits a literature-canonical dimension lands `supported_subset` (amber, not green) until the missing fetcher lands. `data/SOCIAL_FETCHER_BACKLOG.md` inventories the queue.

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

hypotheses/    pre-registered hypotheses (YAML schemas)
  topic/       organised by economic topic (growth, fiscal, monetary, distribution, etc.)
  steelman/    steelman docs (strongest counter-argument per hypothesis)

policies/      individual policies (interventions) coded by axes
movements/     political movements with timeframe + policy_ids + axis trajectory
positions/     17 schools of thought (market_liberal, social_democratic, post_keynesian, ...)

axes.yaml      the policy-content taxonomy (fiscal, regulatory, monetary, openness, distribution)

debate/        private debate engine (CLI; not deployed publicly)
web/           public Next.js platform + API
review/        adversarial review protocol + submitted challenges
schemas/       JSON schemas for every YAML kind

scripts/       CI and maintenance (validate_specs, derive_coverage, etc.)
tests/         pytest suite

HANDOFF_TO_RUN_AGENT.md     spec-to-runnable-replication briefing
HANDOFF_TO_DATA_AGENT.md    fetcher-development briefing
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
# → OK (3892 spec file(s) validated + cross-references clean)
```

### Run a hypothesis

```bash
# 1. Land the data
FRED_API_KEY=... .venv/bin/python scripts/fetch.py fred CPIAUCSL

# 2. Run the replication
.venv/bin/python engine/runs/volcker_disinflation_output_recovery/replication.py
# → SUPPORTED — CPI YoY fell from 14.4% peak to 3.2% in 1983Q4 (drop 11.2pp)...

# 3. Verify pre-registration timestamp
.venv/bin/python scripts/check_preregistration.py
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

The pre-registration invariant is enforced: spec commit timestamp must predate run commit timestamp.

---

## Status

This is **v1.0** of the public platform. Substance is the same as the development beta; the surface is debugged and the indicator-integrity gate is enforced framework-wide.

Open work:
- Closing the social-policy fetcher backlog (`data/SOCIAL_FETCHER_BACKLOG.md`)
- Expanding the engine's estimator templates beyond the current panel-FE / event-study / synth-DiD / local-projections set
- Building out the adversarial-review submission flow on the public site

---

## Licence

- **Code** (everything under `data/fetchers/`, `engine/`, `scripts/`, `web/`, `tests/`): Apache-2.0 — see [LICENSE](LICENSE).
- **Spec library + run artifacts** (everything under `hypotheses/`, `policies/`, `movements/`, `positions/`, `axes.yaml`, `engine/runs/*/diagnostics.json`, `engine/runs/*/result_card.md`): CC-BY-4.0 — see [LICENSE-DATA](LICENSE-DATA). Cite as the schema's `permalink` field.

The split is deliberate. Code wants maximum reuse (Apache-2.0). The spec library is a research artifact whose audit trail and adversarial-review history matters; CC-BY ensures attribution survives forks.

---

## Cite

```bibtex
@misc{ieset_framework,
  title = {IESET — An empirically-grounded, adversarially-reviewed economic policy framework},
  author = {{IESET Institute}},
  year = {2026},
  url = {https://github.com/<institute-org>/ieset},
  note = {Verdict-tier audit trail and indicator-integrity gate.}
}
```

A machine-readable `CITATION.cff` is in the repo root.

---

## Author disclosure

Per `DISCLOSURE.md`: the framework is built by a single author with documented market-liberal priors, position holdings in real estate (Latin America, East Asia) and cryptocurrency, and explicit conflicts on hypotheses where those positions could bias the result. Every spec carries a `disclosure:` field flagging this where applicable.

The disclosure model is *the framework's integrity model in action* — author bias is acknowledged, the adversarial-review channel is built specifically so external readers can challenge any verdict, and the `supported_subset` verdict tier exists precisely to prevent author-favourable indicator selection.
