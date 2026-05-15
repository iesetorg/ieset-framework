# Result card — argentina_peronism_recurring_fiscal_inflation_cycle_1945_2023

**Verdict:** PARTIAL — cointegration rank=1, α_infl=-0.003073235091341579; episode precedence 2/5 below 8/12 threshold.

## Joint-system Johansen cointegration test

- Window: 2002-2024 (n=22)
- Exclusions: [1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2020]
- Trace stats: [23.467, 0.022]
- Trace 5% CVs: [15.494, 3.841]
- Max-eig stats: [23.446, 0.022]
- Max-eig 5% CVs: [14.264, 3.841]
- **Rank @5%: 1**

## VECM(1,1) — rank 1

- Cointegrating vector (β, normalised): {'deficit_pct_gdp': 1.0, 'log_inflation': -220.7165575436453}
- α (deficit eq):    +0.0391 (p=0.002)
- α (inflation eq):  -0.0031 (p=0.000)
- **Half-life of deviation:** 225.20 years

## Inflation episodes >50% (1944-2025)

- Total episodes: 5
- Preceded by deficit > 4% GDP in t-1 or t-2 (where deficit data exists): 2

| Episode start | end | deficit t-1 | deficit t-2 | preceded |
|---|---|---|---|---|
| 1959 | 1959 | None | None | False |
| 1972 | 1973 | None | None | False |
| 1975 | 1991 | None | None | False |
| 2019 | 2019 | 5.4 | 6.7 | True |
| 2022 | 2024 | 4.3 | 8.7 | True |

## Data limitations

Argentine fiscal balance (IMF GGXCNL_NGDP) only covers 1993- in vintages. The 1945-1992 portion of the YAML claim cannot be tested with current vintaged data; the inflation-episode count uses full BIS WS_LONG_CPI (1944-2025) but the deficit-precedence half of each episode-row is missing where deficit data is unavailable.

## Falsification rule (YAML)

- Cointegration rank ≥1 at 5% (proxy for Granger causality at p<0.01)
- α on inflation equation negative + significant
- Episode precedence ≥ 8/12

## Provenance

Reproduces from vintages in `manifest.yaml`. See `replication.py`.
