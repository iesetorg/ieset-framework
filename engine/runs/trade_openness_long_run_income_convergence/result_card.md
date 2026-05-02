# Result card — trade_openness_long_run_income_convergence

**Verdict:** supported — TWFE β_trade=+0.000243 (SE 0.000069, p=0.000, n=6344), R²=0.116. Higher trade openness predicts stronger income growth.

## Design

Broad panel 1960-2019. Outcome: 5-year-forward annualised log GDP-per-capita
growth (PWT RGDPE). Treatment: WDI trade openness (`NE.TRD.GNFS.ZS`, % of GDP).
Controls: log initial GDP per capita. Estimator: TWFE (country + year fixed effects),
clustered SE by country.

## Threshold

SUPPORTED if β_trade > 0 and p < 0.05.
REFUTED if β_trade < 0 and p < 0.05.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Observations | 6344 |
| Countries | 160 |
| β_trade | +0.000243 |
| SE | 0.000069 |
| 95% CI | [+0.000107, +0.000379] |
| p-value | 0.000 |
| R² within | 0.116 |

## Limitations

- Trade/GDP is a crude openness measure that includes re-exports and can be
  inflated for small, entrepôt economies.
- No direct industrial-policy intensity measure for the comparison claimed in
  the original hypothesis.
- Reverse causality: faster-growing countries may import more as a share of GDP.
- TWFE assumptions may be violated with heterogeneous treatment effects.

## Next robustness checks

- Use tariff-weighted openness or WITS trade data where available.
- Instrument with geographic trade-propensity (Frankel-Romer).
- Test with 10-year-forward growth windows.
- Control for institutional quality and human capital.
