# Result card — great_leap_forward_famine_output_collapse_1959_1961

**Verdict:** supported

> **QUARANTINED pending v2 re-score — adversarial audit remediation 2026-09-03.** See the Correction section below before citing this card. Primary finding: Metric 10 PENDING_EVAL.


**Reason:** 8 of 10 metrics met threshold (support threshold 7)

Pre-registered rule: SUPPORT if >= 7 of 10 metrics met; REFUTE if <= 3 met (impossible to hit support).

## Correction 2026-09-03 — adversarial audit remediation

**Disposition:** QUARANTINED pending v2 re-score · **Audit:** `engine/audits/ieset_adversarial_supported_claims_2026-07-31.md` (claim 5) · **Remediation:** `engine/audits/ieset_adversarial_audit_remediation_2026-09-03.md` · **Detectors:** `scripts/audit_integrity_detectors.py`

- Metric 10 PENDING_EVAL — the harness could not parse its own pre-registered threshold (X6).
- Metric 1 uses max-of-range fallback (36M of a contested 15–45M scholarly range) — disclosed-prior-shaped convenience.
- Metric 7 provincial dispersion scored NOT_MET on absent data — absence of data is not absence of dispersion.

**Verdict-migration note (X5):** prior verdict was `inconclusive (data gaps, HYPOTHESIS_FRAMEWORK_AUDIT.md §E7)`; the migration to `supported` was undocumented — now recorded in this remediation's ledger.

**Machine-detector confirmations in diagnostics.json (not counted toward the verdict pending v2):**
- metric `life_expectancy_collapse` [unit_typetag_mismatch]: threshold in years_absolute evaluated against percent-change stat 'peak_to_trough_pct_decline' — MET/NOT_MET mechanically manufactured
- metric `post_readjustment_recovery_speed` [unit_typetag_mismatch]: threshold in years_absolute evaluated against percent-change stat 'peak_to_trough_pct_decline' — MET/NOT_MET mechanically manufactured
- metric `excess_mortality_1958_1962`: 5 declared publishers share 1 vintage file(s) — all publishers byte-identical
- metric `grain_output_collapse`: 4 declared publishers share 2 vintage file(s) — fewer files than publishers
- metric `gdp_per_capita_contraction`: 2 declared publishers share 1 vintage file(s) — all publishers byte-identical
- metric `commune_coverage_rate`: 4 declared publishers share 1 vintage file(s) — all publishers byte-identical
- metric `crude_birth_rate_collapse`: 4 declared publishers share 1 vintage file(s) — all publishers byte-identical
- metric `life_expectancy_collapse`: 4 declared publishers share 2 vintage file(s) — fewer files than publishers
- metric `provincial_famine_severity_dispersion`: 5 declared publishers share 1 vintage file(s) — all publishers byte-identical
- metric `net_grain_export_during_famine`: 4 declared publishers share 1 vintage file(s) — all publishers byte-identical
- metric `backyard_steel_campaign_capital_waste`: 4 declared publishers share 1 vintage file(s) — all publishers byte-identical
- metric `post_readjustment_recovery_speed`: 4 declared publishers share 1 vintage file(s) — all publishers byte-identical

No original content has been deleted; this correction is additive.

**Counts:** 8 MET · 1 NOT_MET · 0 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** CHN

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | excess_mortality_1958_1962 | MET | 36 (1962) [max_in_window_fallback] | `>15 million excess deaths over 1958-1962` |  |
| 2 | grain_output_collapse | MET | 28.2 (1960) [peak_to_trough_pct_decline] | `>20% decline in national grain output from 1958 peak to 1960 trough` |  |
| 3 | gdp_per_capita_contraction | MET | 25.5 (1961) [peak_to_trough_pct_decline] | `>15% cumulative real GDP per capita contraction from 1958 peak to 1961 trough` |  |
| 4 | commune_coverage_rate | MET | 99.5 (1959) [max_in_window_fallback] | `>90% of rural households enrolled in People's Communes within 18 months of August 1958 Beidaihe Conference` |  |
| 5 | crude_birth_rate_collapse | MET | 51.3 (1961) [peak_to_trough_pct_decline] | `>25% decline in crude birth rate from 1957 baseline to 1961 trough` |  |
| 6 | life_expectancy_collapse | MET | 53.6 (1960) [peak_to_trough_pct_decline] | `>15 year decline in period life expectancy at birth from 1957 baseline to 1960 trough` |  |
| 7 | provincial_famine_severity_dispersion | NOT_MET | 0 (1962) [pct_increase_from_baseline] | `>=3 provinces with excess mortality exceeding 10% of 1957 provincial population` |  |
| 8 | net_grain_export_during_famine | MET | 4.16 (1959) [max_in_window_fallback] | `>1 million tonnes net grain exports in at least one of 1959 or 1960` |  |
| 9 | backyard_steel_campaign_capital_waste | MET | 47 (1958) [max_in_window_fallback] | `>25% of reported backyard-steel output classified as unusable, or >50 million labour-days diverted from 1958 autumn harvest` |  |
| 10 | post_readjustment_recovery_speed | PENDING_EVAL | 26.6 (1962) [peak_to_trough_pct_decline] | `Grain output recovers to >=1957 level within 5 years of the January 1962 readjustment; crude birth rate rebounds above 1957 level within 3 years` | threshold expression unparseable by regex |

## Claim

> Mao Zedong's Great Leap Forward (1958-1962), characterised by forced collectivisation into People's Communes, Lysenkoist rejection of scientific agronomy, diversion of rural labour to backyard steel production, and cadre-competition-driven inflation of reported harvests, produced a canonical institutional-economic collapse that manifests as >=7 of 10 pre-registered extreme-outcome metrics, each drawn from an independent data source or methodology family and measuring a different causal layer (demographic mortality, agricultural output, macroeconomic contraction, institutional coverage, human capital). The canonical-case claim is that no non-war peacetime economy in the 20th-century panel matches even 4 of these 10 thresholds simultaneously; China 1958-1962 matches most. A refutation (<=3 metrics met) would indicate that the consensus demographic and output reconstructions (Banister 1987, Ashton et al. 1984, Peng 1987, Yang Jisheng 2008) are substantially overstated, or that the institutional-quality coding of the GLF is misplaced.

## Interpretation

The canonical-case pattern match is satisfied: 8 of 10 pre-registered metrics meet their thresholds, above the support threshold of 7. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/great_leap_forward_famine_output_collapse_1959_1961.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
