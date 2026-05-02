# Result card — ireland_market_opening_fdi_frontier_1987_2024

**Verdict:** supported — Ireland FDI 14.3% of GDP vs OECD median 2.7%; convergence slope +4.10pp/yr vs median +0.46pp/yr (diff +3.64pp).

## Design

Ireland vs 29 OECD comparators, 1987-2019. Mean FDI inflows
(% of GDP, WDI) and log GDP-per-capita convergence slope relative to US (PWT).

## Threshold

SUPPORTED if Ireland mean FDI/GDP ≥ comparator median AND convergence slope
≥ comparator median + 0.5pp/yr.
REFUTED if Ireland slope < comparator median.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Ireland mean FDI/GDP | 14.3% |
| OECD median FDI/GDP | 2.7% |
| Ireland convergence slope | +4.10pp/yr |
| OECD median slope | +0.46pp/yr |
| Diff vs median | +3.64pp/yr |

## Country panel

| ISO3 | Mean FDI/GDP | Log rel 1987 | Log rel 2019 | Slope | Group |
|---:|---:|---:|---:|---:|:---|
| AUS | 2.9 | -0.289 | -0.221 | +0.21pp | Comparator |
| AUT | 1.8 | -0.481 | -0.131 | +1.09pp | Comparator |
| BEL | 10.4 | -0.456 | -0.216 | +0.75pp | Comparator |
| CAN | 2.7 | -0.147 | -0.250 | -0.32pp | Comparator |
| CHE | 4.0 | +0.048 | +0.125 | +0.24pp | Comparator |
| CHL | 5.6 | -1.652 | -0.988 | +2.07pp | Comparator |
| DEU | 1.8 | -0.433 | -0.206 | +0.71pp | Comparator |
| DNK | 2.0 | -0.287 | -0.126 | +0.50pp | Comparator |
| ESP | 2.7 | -0.860 | -0.427 | +1.35pp | Comparator |
| FIN | 2.9 | -0.424 | -0.295 | +0.40pp | Comparator |
| FRA | 1.9 | -0.412 | -0.347 | +0.21pp | Comparator |
| GBR | 3.8 | -0.448 | -0.317 | +0.41pp | Comparator |
| GRC | 0.9 | -0.858 | -0.787 | +0.22pp | Comparator |
| HUN | 8.7 | -1.042 | -0.645 | +1.24pp | Comparator |
| IRL | 14.3 | -0.832 | +0.479 | +4.10pp | Ireland |
| ISL | 2.7 | -0.041 | -0.078 | -0.11pp | Comparator |
| ISR | 2.6 | -0.514 | -0.394 | +0.37pp | Comparator |
| ITA | 0.9 | -0.427 | -0.425 | +0.00pp | Comparator |
| JPN | 0.2 | -0.486 | -0.470 | +0.05pp | Comparator |
| KOR | 0.8 | -1.344 | -0.440 | +2.82pp | Comparator |
| LUX | 26.2 | +0.001 | +0.578 | +1.80pp | Comparator |
| MEX | 2.3 | -1.120 | -1.189 | -0.22pp | Comparator |
| NLD | 15.3 | -0.376 | -0.123 | +0.79pp | Comparator |
| NOR | 1.9 | -0.273 | -0.013 | +0.81pp | Comparator |
| NZL | 1.8 | -0.524 | -0.413 | +0.35pp | Comparator |
| POL | 3.0 | -1.432 | -0.645 | +2.46pp | Comparator |
| PRT | 3.2 | -1.070 | -0.615 | +1.42pp | Comparator |
| SWE | 3.8 | -0.272 | -0.126 | +0.46pp | Comparator |
| TUR | 1.1 | -1.216 | -0.865 | +1.10pp | Comparator |
| USA | 1.6 | +0.000 | +0.000 | +0.00pp | Comparator |

## Limitations

- FDI/GDP is a flow measure that can be distorted by corporate-tax routing
  (double-Irish, etc.). Does not distinguish real investment from pass-through.
- Endpoint slope sensitive to 1987 and 2019 levels.
- Tax competitiveness and trade openness are not directly measured.
- US is used as frontier benchmark; EU-15 average may be more appropriate for Ireland.

## Next robustness checks

- Use EU-15 average instead of US as frontier.
- Control for initial income level.
- Use median FDI instead of mean to reduce outlier sensitivity.
- Separate pre- and post-Celtic-Tiger periods.
