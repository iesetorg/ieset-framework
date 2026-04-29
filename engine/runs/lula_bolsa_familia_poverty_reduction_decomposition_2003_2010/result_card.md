# Result card — lula_bolsa_familia_poverty_reduction_decomposition_2003_2010

**Verdict:** partial — Some Shapley conditions met but not all: BF+MW poverty share 9% < 40%; BF+MW Gini share 6% < 30%. Brazil 2003→2010 delta: poverty -9.4pp, Gini -4.3.

## Pre-registered thresholds

- BF + minimum-wage Shapley share of poverty change: >= 0.40
- BF + minimum-wage Shapley share of Gini change: >= 0.30
- Commodity-boom Shapley share on either outcome: <= 0.60

## Shapley shares

| Channel | Poverty share | Gini share |
|---|---:|---:|
| bf_intensity | +4.8% | +2.9% |
| min_wage_log | +3.7% | +3.6% |
| gdp_pc_growth | +7.9% | +3.8% |
| urban | +83.5% | +89.7% |
| **BF + minimum wage (policy)** | **+8.6%** | **+6.5%** |

Full-spec R^2 (poverty): 0.978 (baseline FE: 0.944; explainable above FE: 0.034).
Full-spec R^2 (gini): 0.946 (baseline FE: 0.932; explainable above FE: 0.014).

## Brazil observed change, 2003 → endpoint

- Extreme-poverty headcount: 17.1 → 7.8 (endpoint 2010, delta -9.4pp).
- Gini coefficient (×100): 57.6 → 53.3 (endpoint 2010, delta -4.3).

## Method

Panel: BRA + 5 LatAm donors (MEX, COL, PER, CHL, ARG), 1995-2012,
with Argentina 2001-2003 and Mexico 2009 dropped per spec
exclusion_rules. Decomposition window 2003-2010. OLS with country
and year FE plus four channels (BF intensity, real-min-wage log,
per-capita GDP growth as commodity-boom proxy, urbanisation rate).
Shapley value for each channel is the average marginal incremental
R^2 over all subset orderings, normalised to the explainable-R^2
share above the country+year-FE baseline.

## Data

- world_bank_wdi:SI.POV.DDAY (extreme-poverty headcount, USD 2.15 PPP)
- world_bank_wdi:SI.POV.GINI (Gini × 100)
- world_bank_wdi:NY.GDP.PCAP.KD.ZG (per-capita real-GDP growth)
- world_bank_wdi:SP.URB.TOTL.IN.ZS (urbanisation rate)

## Caveats

- Bolsa Família intensity and the real-minimum-wage index are
  constructed BRA-only series (zero for donors), calibrated to
  published IPEA / MDS / DIEESE timelines. Errors-in-variables on
  these channels could attenuate their attributed share.
- The commodity channel is reduced-form (per-capita growth), not a
  terms-of-trade index — partly absorbing the same general boom
  signal that drives donor-pool poverty declines but missing
  cross-country heterogeneity in commodity-export concentration.
- Synthetic-control robustness on BRA is deferred to v1.1.
