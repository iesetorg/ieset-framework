# Result card — latam_extra_fiscal_rule_adoption_panel_1999_2024

**Verdict:** INCONCLUSIVE_DATA_PENDING — registered treated cohorts lack a pre-adoption primary outcome: BRA, PER

## Frozen rule

- (a) ATT < 0 at p < 0.10: **None**; ATT=-8.174586225055632, p=0.359067232035882
- (b) within-country fiscal-balance dispersion declines: **None**; median post-minus-pre=0.850951208062906
- (c) no cumulative-growth penalty: **True**; matched median log-growth gap=0.07401030401260833 (threshold 0.0)

**Decision scope:** The full registered treatment cohort cannot be graded from the local primary outcome.
Design-grade recommendation: **archive** — Missing registered pretreatment outcome prevents full-sample grading. Failure of necessary condition (a) is not evidence that the unmeasured secondary condition passed or failed, nor that treatment had an opposite effect.

## Method and coverage

Group-time ATT(g,t) compares each adoption cohort with countries not yet or never treated, from g-1 to t. Control-country outcome regression adjusts for terms-of-trade change and the latest observed WGI at or before g-1 (early WGI is biennial; no post-adoption backfill). The pooled ATT weights treated country-periods; uncertainty uses a delete-one-country jackknife. Common oil-price and US-rate movements are absorbed in each group-time comparison.
Group-time cells: 54; contributing countries: 16; registered treated countries without primary baseline: BRA, PER.
The previous TWFE fallback and its incorrectly inferred cohort years are preserved under `historical/`. COVID 2020–2021 is excluded only from the registered cumulative-growth endpoint.

Spec SHA-256: `2bc534b83c9249dc46e953415df6da4b4e82a88209f257d227b8061b9642c73c`
Input-panel SHA-256: `50a9943be305a9653693919a79151c822ee3b6f998f97224ffa4ab1b03b49fbc`

**Frozen-spec inconsistency:** The claim names Mexico as a 2006 adopter, but the registered treatment source omits it; this replay treats Mexico as a comparison country. The run remains archived pending prospective resolution.
