# Result card — India 1991 liberalisation growth acceleration

**Verdict:** SUPPORTED — post-1991 annualised log-growth +4.67%/yr vs pre-1991 +1.96%/yr; acceleration +2.70pp/yr (threshold +2.00pp/yr).

## Headline numbers

- Series: WDI `NY.GDP.PCAP.KD` (constant 2015 USD).
- Pre-reform window 1965-1990 annualised log-growth: +1.961%/yr (cumulative +0.490 log-points, ~+63%).
- Post-reform window 1992-2019 annualised log-growth: +4.666%/yr (cumulative +1.260 log-points, ~+252%).
- **Acceleration: +2.705pp/yr** (post − pre).
- Trimmed-pre robustness (1975-1990 vs 1992-2019): +2.353pp/yr.

## Threshold applied

- PRIMARY: `annualised_log_growth(1992-2019) − annualised_log_growth(1965-1990) >= 0.02` (2pp/yr).
- INFORMATIVE: trimmed-pre window (1975-1990) yields a similar or larger acceleration.

| Component | Threshold | Realised | Pass |
|---|---:|---:|:---:|
| Annualised acceleration | >= +2.00pp/yr | +2.705pp/yr | yes |
| Trimmed-pre robustness | >= primary | +2.353pp/yr | no |

## Interpretation

This is a within-country structural-break descriptive comparison; results are a pattern match, not causal identification. The 1991 BoP-crisis liberalisation package is bundled with subsequent reforms (1990s telecoms, 2000s services-export boom) and global tailwinds (China-driven commodity supercycle, IT-services offshoring). The descriptive estimator documents the break; it does not isolate the marginal contribution of 1991-specific instruments.

## Sources

- World Bank WDI `NY.GDP.PCAP.KD` (vintage NY.GDP.PCAP.KD@2026-04-28T125340Z.parquet).

## Steelman live concerns

See `hypotheses/steelman/india_1991_liberalisation_growth_acceleration.md`.
