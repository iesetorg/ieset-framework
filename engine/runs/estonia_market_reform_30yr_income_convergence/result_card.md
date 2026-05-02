# Result card — estonia_market_reform_30yr_income_convergence

**Verdict:** supported — Estonia convergence slope +2.01pp/yr vs comparator median +0.62pp/yr (diff +1.39pp, threshold >= 0.5pp).

## Design

Estonia vs 18 post-Soviet/CEE comparators. Convergence measured as log
GDP-per-capita (PWT RGDPE) relative to Germany, endpoint slope 1991-2019.

## Threshold

SUPPORTED if Estonia annualised convergence slope ≥ comparator median + 0.5pp/yr.
REFUTED if Estonia slope ≤ comparator median.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Estonia slope | +2.01pp/yr |
| Comparator median | +0.62pp/yr |
| Comparator mean | +0.66pp/yr |
| Diff vs median | +1.39pp/yr |

## Country panel

| ISO3 | Log rel 1991 | Log rel 2019 | Slope | Group |
|---:|---:|---:|---:|:---|
| EST | -0.891 | -0.329 | +2.01pp | Estonia |
| LVA | -0.646 | -0.496 | +0.54pp | Comparator |
| LTU | -0.844 | -0.319 | +1.87pp | Comparator |
| POL | -1.258 | -0.439 | +2.92pp | Comparator |
| CZE | -0.367 | -0.236 | +0.47pp | Comparator |
| SVK | -0.675 | -0.467 | +0.74pp | Comparator |
| HUN | -0.864 | -0.439 | +1.52pp | Comparator |
| SVN | -0.459 | -0.262 | +0.70pp | Comparator |
| HRV | -1.017 | -0.629 | +1.39pp | Comparator |
| BGR | -0.870 | -0.818 | +0.19pp | Comparator |
| ROU | -1.405 | -0.582 | +2.94pp | Comparator |
| RUS | -0.676 | -0.584 | +0.33pp | Comparator |
| UKR | -0.978 | -1.395 | -1.49pp | Comparator |
| BLR | -0.695 | -0.884 | -0.67pp | Comparator |
| KAZ | -0.896 | -0.584 | +1.11pp | Comparator |
| GEO | -1.052 | -1.245 | -0.69pp | Comparator |
| ARM | -1.576 | -1.313 | +0.94pp | Comparator |
| AZE | -1.129 | -1.162 | -0.12pp | Comparator |
| MDA | -1.557 | -1.782 | -0.80pp | Comparator |

## Limitations

- Endpoint slope is sensitive to single-year measurement error in 1991 or 2019.
- Germany may not be the right frontier benchmark for all comparators.
- Does not control for initial reform intensity, EU accession timing, or
  geographic / trade advantages.
- Estonia's small population and proximity to Finland may confound reform effects.

## Next robustness checks

- Use EU-15 average instead of Germany as frontier.
- Control for initial income level (convergence conditional on β-convergence).
- Extend to 2022/2023 using WDI where PWT ends.
- Add Baltic peers (LVA, LTU) as a separate sub-group comparison.
