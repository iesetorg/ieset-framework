# Result card — latam_extra_inflation_targeting_diff_in_diff_1999_2024

**Verdict:** REFUTED — preregistered support conjunction failed because primary negative-ATT significance condition (a) failed; no opposite effect is established

## Frozen rule

- (a) ATT < 0 at p < 0.10: **False**; ATT=-0.021804688218885825, p=0.99121036365077
- (b) within-country five-year inflation volatility declines: **None**; median post-minus-pre=-1.8263420637285084
- (c) no cumulative-growth penalty: **True**; matched median log-growth gap=0.10631290106592872 (threshold -0.05)

**Decision scope:** Frozen condition (a) alone is dispositive for this conjunctive claim. A null secondary condition remains unmeasured and is not treated as a pass or failure. This logical failure of the support rule does not show an opposite treatment effect.
Design-grade recommendation: **calibration** — The primary condition fails the conjunction, but the early 1999 cohorts lack a pure five-year pre-adoption volatility window; few treated cohorts and jackknife uncertainty limit causal generalization. Failure of necessary condition (a) is not evidence that the unmeasured secondary condition passed or failed, nor that treatment had an opposite effect.

## Method and coverage

Group-time ATT(g,t) compares each adoption cohort with countries not yet or never treated, from g-1 to t. Control-country outcome regression adjusts for terms-of-trade change and the latest observed WGI at or before g-1 (early WGI is biennial; no post-adoption backfill). The pooled ATT weights treated country-periods; uncertainty uses a delete-one-country jackknife. Common oil-price and US-rate movements are absorbed in each group-time comparison.
Group-time cells: 125; contributing countries: 15; registered treated countries without primary baseline: none.
The previous TWFE fallback and its incorrectly inferred cohort years are preserved under `historical/`. COVID 2020–2021 is excluded only from the registered cumulative-growth endpoint.

Spec SHA-256: `93bdec9f42a588c9805599fce92f8838c619b762b46fa6e0415ae4db6ec42c6a`
Input-panel SHA-256: `cb8c130fa61cf64ba7e19ed27dde26692299fe2da93739a360dbcc85046fcc0f`
