# Result card — pcw100_us_mw_bite_ratio_p10_wage

- Registered verdict: **SUPPORTED**, for the specified association only.
- Current evidence standing: **public calibration; unscored by schools**.
- Sample realized: 459 state-year observations, 51 jurisdictions, nine observed years (2014–2018, 2020–2021, 2023–2024). The registered sample window was 2006–2024; missing years were not imputed.
- Estimate: +0.5883855769, state-clustered SE 0.0860611951, two-sided p=8.0965928468e-12; full state/year fixed-effects R²=0.9749146812.

The 17 school links were attached after this result was known. They remain visible as historical links but are **untested for school scoring**: no win, loss, tested count, support-rate contribution, Q-net, raw net, or strict-integrity credit is awarded. The result does not establish a causal effect of minimum-wage policy on low-end wages.

## Superseding integrity correction — 2026-10-09

The independent [integrity replay](../../audits/pcw100_us_mw_bite_ratio_p10_wage_integrity_replay_2026-10-09.md) matched the registered runner and original result from pinned analysis inputs. The pre-registered rule was a positive state/year fixed-effects association with two-sided p<0.10 and minimum data/contrast gates; it was not a causal effect claim. The registered SUPPORT verdict survives that exact replay. Its use is capped at descriptive calibration.

Two factual premises of the July adversarial audit and September remediation are corrected:

1. The bottom and top quartiles each contain 115 **state-year rows**, with zero overlap in state-year keys. HI, MA, MD, MS, and NY appear in both state-name lists because different years enter different quartiles. This is not a row-overlap pipeline bug.
2. The treatment is the effective legal minimum wage divided by BLS median hourly wage. The outcome is the separate BLS tenth-percentile hourly wage. No high-quartile p10 wage equals the legal minimum exactly; two are one cent above it. The full-model R² cannot establish literal mechanical identity because it includes state and year effects.

The remaining limitation is material: treatment and outcome both use contemporaneous wage distributions, and statutory floors can respond to local wages. The evidence supports the **registered within-sample association** only; it cannot attribute a causal wage effect or validate a school's mechanism. The full decision and zero-score implementation are in the [calibration rescope audit](../../audits/pcw100_us_mw_bite_ratio_p10_wage_calibration_rescope_2026-10-09.md).

## Original run and historical correction

The original July run recorded `SUPPORTED`. On 2026-09-03, the remediation appended `quarantined_pending_v2` based on the two premises above. That September disposition and wording are retained in Git history and linked audit records; the 2026-10-09 replay and rescope supersede them. No source data, registered hypothesis, coefficient, or original replication runner was changed for this rescope.

## Registered decision rule

Expected-sign coefficient with two-sided p<0.10 is SUPPORTED; significant opposite sign is REFUTED; all other estimable results are PARTIAL. A failed data gate is INCONCLUSIVE.

## Estimate and contrast

- Method: OLS with state and year indicators and state-clustered covariance.
- Observations: 459; jurisdictions: 51; observed years: 9.
- Low/high treatment cutoffs: 0.4091433849 / 0.5050791685; gap: 0.0959357836.
- Bottom/top treatment quartiles: 115 state-year rows each, no state-year intersection.
- Coefficient: +0.5883855769; standard error: 0.0860611951; 95% CI: [+0.4197087340, +0.7570624198]; p-value: 8.0965928468e-12.
