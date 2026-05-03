# Ready No-Run Results - 2026-05-03

## Methodology Gate

- Pre-registration commit: `91b4750`
- Runner fix commit: `8fa3f1c09ef8f11f26b1a4a9960a404c267d7692`
- Estimation was run only after the 7 specs were promoted to `pre_registered` and committed.
- Stale reciprocal `covers_claims` were removed before pre-registration, so these runs are hypothesis evidence, not school-scoreboard mappings yet.
- Each run directory includes `diagnostics.json`, `result_card.md`, and `replication.py`.

## Counts

- REFUTED: 1
- PARTIAL: 6

## FDR q<=0.10

- No SUPPORTED/REFUTED verdicts survive q<=0.10.

## Results

- `flat_tax_reform_growth_panel`: PARTIAL | coef=-0.5794 | p=0.4599 | q=0.4599 | n=443 | countries=18 | flags=none
- `government_spending_tfp_drag_panel`: PARTIAL | coef=-0.001654 | p=0.1846 | q=0.2769 | n=1988 | countries=73 | flags=none
- `mortgage_market_liberalisation_homeownership_panel`: PARTIAL | coef=+1.307 | p=0.3788 | q=0.4545 | n=1469 | countries=61 | flags=none
- `privatisation_transition_tfp_panel`: PARTIAL | coef=+1.368e-14 | p=0.002655 | q=0.01593 | n=337 | countries=20 | flags=effect_magnitude_effectively_zero, fallback_estimator
- `oecd_product_market_deregulation_tfp_panel`: PARTIAL | coef=+0.09578 | p=NA | q=NA | n=35 | countries=35 | flags=p_value_not_estimable, fallback_estimator
- `unemployment_benefit_generosity_employment_drag`: PARTIAL | coef=+26.25 | p=0.1238 | q=0.2475 | n=767 | countries=38 | flags=none
- `workfare_conditionality_employment_effect`: REFUTED | coef=+1.311 | p=0.04651 | q=0.1395 | n=805 | countries=38 | flags=none
