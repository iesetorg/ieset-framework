# Result card - argentina_paso_2019_fx_reserves_inflation_base_money_lag

**Verdict:** SUPPORTED - 3/4 metrics passed (support >= 3; refute <= 2).

## Claim

Argentina's 2019 PASO shock generated an immediate official-FX break, reserve loss, and inflation pass-through; the 2020 base-money expansion was followed by a lagged inflation pickup by Q4.

## Metrics

| Metric | Value | Threshold | Pass | Details |
|---|---:|---|:---:|---|
| paso_fx_devaluation | 33.577 | >25% devaluation within one week | yes | 46.55 to 62.18 ARS/USD |
| reserves_drawdown | 24.461 | >10% reserve fall within about 30 days | yes | 66309 to 50089 USD mn |
| inflation_pass_through | 4.950 | Aug-Sep 2019 average monthly CPI >4.5% | yes | 4.95% average monthly |
| base_money_lagged_inflation | 1.933 | base money +20% Mar-Sep and Q4 inflation > Q2 by 1pp | no | base 2292083 to 2393695; CPI avg 1.73% to 3.67% |

## Interpretation

This is a compact predeclared event-window verdict using local cached national-statistics vintages. It is strong for timing and magnitude, but not a full causal structural decomposition.

## Provenance

See `manifest.yaml` for exact vintage files and SHA-256 hashes. Re-run with `replication.py`.
