# Result card - argentina_cepo_lift_2015_fx_inflation_reserves

**Verdict:** SUPPORTED - 3/3 metrics passed (support >= 2; refute <= 1).

## Claim

Argentina's December 2015 cepo lift produced a discrete official-peso devaluation and higher short-run monthly inflation, while BCRA reserves did not collapse over the next 90 days.

## Metrics

| Metric | Value | Threshold | Pass | Details |
|---|---:|---|:---:|---|
| official_fx_devaluation | 38.345 | >30% devaluation | yes | 9.91 to 13.71 ARS/USD |
| reserves_not_depleted | 20.344 | reserve change > -20% | yes | 24164 to 29080 USD mn |
| inflation_pass_through | 1.083 | >1pp increase in average monthly CPI | yes | 2.33% to 3.42% average monthly |

## Interpretation

This is a compact predeclared event-window verdict using local cached national-statistics vintages. It is strong for timing and magnitude, but not a full causal structural decomposition.

## Provenance

See `manifest.yaml` for exact vintage files and SHA-256 hashes. Re-run with `replication.py`.
