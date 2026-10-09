# Result card: trade_openness_private_consumption_geographic_holdout_v2

Verdict: **PARTIAL**. estimable holdout result clears neither directional threshold.

## Registered design

- Registration commit: `937d359c699df37fcb94ae6a1424cc9be9449e2d`
- Sample: 2839 complete country-years across 134 countries, [1996, 2023]
- Original 40-country sample overlap: 0
- Estimator: country and year FE, country-clustered standard errors
- Outcome: WDI real household consumption per capita
- Primary term: WDI trade openness as percentage of GDP
- Frozen family: 9 related tests; two-sided p <= 0.01

## Primary result

Coefficient +2.0628, clustered SE 3.48994, p=0.5545, 95% CI [-4.777363441242381, 8.902960308609336].

## Interpretation and limits

This geographic holdout measures an association in countries omitted from the old
PARTIAL study. It does not identify a causal welfare effect of trade policy.
