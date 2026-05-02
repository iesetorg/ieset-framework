# Result card — developmental_state_to_market_transition_success

**Verdict:** partial — Transitioned +2.71%/yr vs persistent-dev +2.60%/yr (diff +0.11pp) and vs persistent-market +2.29%/yr (diff +0.43pp); does not meet both thresholds.

## Design

Countries classified by V-Dem `v2clstown` (state ownership of economy, higher = less
state ownership) in 1980 and 2010.

- **Persistent developmental**: bottom quartile in both years.
- **Persistent market**: top half in both years.
- **Transitioned**: bottom quartile in 1980, top half in 2010.

Outcome: annualised log GDP-per-capita growth 1980-2019 (PWT).

## Threshold

SUPPORTED if transitioned mean growth ≥ persistent-dev mean + 0.5pp/yr
AND transitioned mean growth ≥ persistent-market mean − 0.5pp/yr.
REFUTED if transitioned mean growth < persistent-dev mean growth.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Total countries | 140 |
| Persistent developmental | 9 |
| Persistent market | 46 |
| Transitioned | 10 |
| Persistent dev growth | +2.60%/yr |
| Persistent market growth | +2.29%/yr |
| Transitioned growth | +2.71%/yr |
| Diff vs dev | +0.11pp/yr |
| Diff vs market | +0.43pp/yr |

## Country panel

| ISO3 | v2clstown 1980 | v2clstown 2010 | Group | Growth |
|---:|---:|---:|:---|---:|
| SWE | 1.077 | 1.481 | persistent_market | +2.21% |
| CHE | 1.036 | 2.219 | persistent_market | +1.84% |
| ZAF | 1.060 | 1.445 | persistent_market | +0.45% |
| JPN | 1.551 | 2.980 | persistent_market | +1.63% |
| MMR | -2.096 | -0.997 | persistent_dev | +4.50% |
| ALB | -3.956 | 1.433 | transitioned | +3.10% |
| COL | 0.947 | 1.896 | persistent_market | +1.50% |
| POL | -1.443 | 1.618 | transitioned | +4.08% |
| BRA | 0.055 | 1.031 | persistent_market | +2.30% |
| USA | 1.851 | 2.532 | persistent_market | +1.85% |
| PRT | 0.542 | 1.300 | persistent_market | +2.89% |
| SLV | 0.907 | 2.309 | persistent_market | +5.16% |
| HTI | 0.320 | 1.285 | persistent_market | -0.29% |
| HND | 0.051 | 1.765 | persistent_market | +1.39% |
| MLI | -0.064 | 1.873 | persistent_market | +3.28% |
| PER | -1.002 | 1.940 | transitioned | +2.68% |
| ARG | 0.283 | 1.029 | persistent_market | +3.99% |
| KEN | -0.915 | 1.267 | transitioned | +1.61% |
| KOR | 0.917 | 1.313 | persistent_market | +5.33% |
| LBN | 1.718 | 1.718 | persistent_market | +2.81% |
| NGA | -0.069 | 1.057 | persistent_market | +0.12% |
| TWN | 0.168 | 1.200 | persistent_market | +3.72% |
| THA | 0.325 | 1.063 | persistent_market | +4.13% |
| KHM | -1.204 | 1.526 | transitioned | +3.99% |
| NPL | -1.536 | 1.214 | transitioned | +3.60% |
| GIN | -1.662 | 1.066 | transitioned | -0.91% |
| CAN | 1.027 | 1.027 | persistent_market | +1.48% |
| AUS | 1.092 | 2.010 | persistent_market | +1.93% |
| CAF | 0.611 | 1.163 | persistent_market | -0.44% |
| CHL | 1.251 | 1.613 | persistent_market | +2.89% |
| CRI | 0.145 | 1.016 | persistent_market | +2.12% |
| FRA | 0.382 | 1.584 | persistent_market | +1.50% |
| DEU | 1.337 | 2.397 | persistent_market | +2.16% |
| GTM | 2.661 | 2.661 | persistent_market | +1.76% |
| IRN | -1.078 | -1.116 | persistent_dev | +2.91% |
| IRL | 0.525 | 1.313 | persistent_market | +5.03% |
| ITA | 0.231 | 2.310 | persistent_market | +1.63% |
| JOR | 0.236 | 1.281 | persistent_market | +2.19% |
| LBR | 0.280 | 1.241 | persistent_market | -1.70% |
| NLD | 1.193 | 1.366 | persistent_market | +1.98% |
| PAN | 0.025 | 1.191 | persistent_market | +3.81% |
| ESP | 1.121 | 1.898 | persistent_market | +2.44% |
| TUR | 0.461 | 1.650 | persistent_market | +3.03% |
| GBR | 1.187 | 1.662 | persistent_market | +1.97% |
| DZA | -2.359 | -1.913 | persistent_dev | -0.27% |
| TCD | 1.179 | 1.219 | persistent_market | +1.33% |
| CHN | -1.375 | -0.932 | persistent_dev | +5.43% |
| COG | -1.864 | -1.180 | persistent_dev | +1.64% |
| DOM | 0.845 | 1.861 | persistent_market | +3.29% |
| LAO | -2.844 | -1.475 | persistent_dev | +5.50% |
| BEL | 1.555 | 1.438 | persistent_market | +1.87% |
| BGR | -3.899 | 1.390 | transitioned | +2.60% |
| CYP | 0.268 | 2.117 | persistent_market | +2.75% |
| GNQ | -1.129 | -1.183 | persistent_dev | +6.18% |
| GRC | 0.203 | 1.156 | persistent_market | +1.65% |
| HKG | 2.140 | 1.755 | persistent_market | +3.27% |
| ISL | 0.005 | 1.017 | persistent_market | +1.73% |
| LUX | 2.123 | 2.123 | persistent_market | +3.14% |
| MUS | 2.172 | 1.314 | persistent_market | +3.40% |
| NZL | 0.054 | 1.701 | persistent_market | +2.16% |
| PRY | 0.701 | 1.877 | persistent_market | +2.59% |
| ROU | -3.602 | 1.102 | transitioned | +3.70% |
| SAU | -1.172 | -1.233 | persistent_dev | +0.75% |
| ARE | -1.763 | -1.020 | persistent_dev | -3.21% |
| HUN | -2.382 | 1.595 | transitioned | +2.72% |

## Limitations

- V-Dem `v2clstown` measures state ownership of the economy, not the full
  developmental-state toolkit (directed credit, industrial policy, export discipline).
- Classification into quartiles is mechanical and may mislabel countries with
  idiosyncratic ownership structures (e.g., Singapore, Norway).
- 1980 V-Dem coverage is good but some scores are back-projected.
- No control for initial income level, commodity booms, or geopolitical shocks.

## Next robustness checks

- Use WGI RQ or Fraser EFW as alternative transition proxy.
- Vary the classification years (1990, 2000).
- Control for initial GDP per capita and population.
- Add a "failed transition" group (high state ownership that rose then fell).
