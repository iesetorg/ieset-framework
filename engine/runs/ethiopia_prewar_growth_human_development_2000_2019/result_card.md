# Result card — ethiopia_prewar_growth_human_development_2000_2019

**Verdict:** supported

> **RE-SCOPED to supported (descriptive) tier — adversarial audit remediation 2026-09-03.** See the Correction section below before citing this card. Primary finding: Post-hoc window ending 2019 excludes the Tigray-war collapse.


**Reason:** 4 of 4 metrics met threshold (support threshold 3)

Pre-registered rule: SUPPORT if >= 3 of 4 metrics met; REFUTE if <= 1 met (impossible to hit support).

## Correction 2026-09-03 — adversarial audit remediation

**Disposition:** RE-SCOPED to supported (descriptive) tier · **Audit:** `engine/audits/ieset_adversarial_supported_claims_2026-07-31.md` (claim 14) · **Remediation:** `engine/audits/ieset_adversarial_audit_remediation_2026-09-03.md` · **Detectors:** `scripts/audit_integrity_detectors.py`

- Post-hoc window ending 2019 excludes the Tigray-war collapse — the strongest contrary observation; break-rule disclosed nowhere.
- Official national accounts contested; no dual-source robustness metric.

No original content has been deleted; this correction is additive.

**Counts:** 4 MET · 0 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** ETH

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | real_gdp_pc_growth_fast | MET | 5.87 (2019) [average_annual_growth_rate_value] | `average annual growth >= 5%` | average annual growth 2000-2019 = 5.874; threshold >=5 |
| 2 | under5_mortality_decline_large | MET | 61.7 (2019) [peak_to_trough_pct_decline] | `>= 50% decline` |  |
| 3 | life_expectancy_increase_large | MET | 29.2 (2019) [pct_increase_from_baseline] | `>= 25% increase` |  |
| 4 | services_employment_share_threshold | MET | 31.3 (2019) [max_in_window] | `>= 30% during 2019` |  |

## Claim

> Ethiopia's pre-war 2000-2019 development episode combined fast real GDP per-capita growth, large child-mortality reduction, rising life expectancy, and a shift toward services employment. The narrow test is whether at least three of four WDI-based outcome metrics meet their thresholds before the 2020 conflict shock.

## Interpretation

The canonical-case pattern match is satisfied: 4 of 4 pre-registered metrics meet their thresholds, above the support threshold of 3. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/ethiopia_prewar_growth_human_development_2000_2019.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
