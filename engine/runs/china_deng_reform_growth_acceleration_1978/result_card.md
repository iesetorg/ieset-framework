# Result card — China Deng-era reform growth acceleration, structural break at 1978

**Verdict:** SUPPORTED — post-1978 annualised log-growth +8.07%/yr vs pre-1978 +3.33%/yr; acceleration +4.74pp/yr (threshold +3.00pp/yr).

## Headline numbers

- Series: WDI `NY.GDP.PCAP.KD` (constant 2015 USD).
- Pre-reform window 1965-1977 annualised log-growth: +3.332%/yr (cumulative +0.400 log-points, ~+49%).
- Post-reform window 1979-2019 annualised log-growth: +8.073%/yr (cumulative +3.229 log-points, ~+2426%).
- **Acceleration: +4.741pp/yr** (post − pre).
- Robustness (1965↔1977 endpoint slope vs 1979↔2019 endpoint slope): +4.741pp/yr.

## Threshold applied

- PRIMARY: `annualised_log_growth(1979-2019) − annualised_log_growth(1965-1977) >= 0.03` (3pp/yr).
- INFORMATIVE robustness: endpoint-slope acceleration `>= 0.025`.

| Component | Threshold | Realised | Pass |
|---|---:|---:|:---:|
| Annualised acceleration | >= +3.00pp/yr | +4.741pp/yr | yes |
| Endpoint-slope robustness | >= +2.50pp/yr | +4.741pp/yr | yes |

## Interpretation

This is a within-country structural-break descriptive comparison; results are a pattern match, not causal identification. There is no counterfactual China and no control for global commodity demand, the simultaneous Asian regional take-off, or the demographic dividend. The acceleration magnitude is overwhelming, which is why the canonical narrative attributes it to the 1978 reform package — but the descriptive estimator only documents the break; it cannot rule out alternative explanations on its own.

## Sources

- World Bank WDI `NY.GDP.PCAP.KD` (vintage NY.GDP.PCAP.KD@2026-04-28T125340Z.parquet).

## Steelman live concerns

See `hypotheses/steelman/china_deng_reform_growth_acceleration_1978.md`.
