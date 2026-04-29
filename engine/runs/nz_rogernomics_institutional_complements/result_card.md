# NZ Rogernomics — institutional complements vs deregulation alone

**Verdict:** refuted — full-stack 1994-2000 NZ-vs-donor-pool growth gap is -0.69pp/yr (NEGATIVE — NZ lagged the donor pool even after the RBA Act + FRA). Institutional complements failed to lift growth above the counterfactual; deregulation-only window gap was -1.93pp/yr.

## Summary

Three-window decomposition of the NZ-vs-donor-pool real-GDP-per-capita growth gap, where the donor pool is the equally-weighted mean of AUS, USA, GBR, CAN (per `spec.sample.countries`).

- **Pre 1980-1983** (baseline): donor-pool growth typically faster.
- **Window A 1984-1988** (deregulation only): if NZ lagged or matched donors, the institutional-complements story is consistent. If NZ already led by >=+1.0pp/yr, the story is refuted.
- **Window B 1989-1993** (deregulation + RBA Act): inflation-targeting begins; transition.
- **Window C 1994-2000** (full stack incl. FRA): if NZ now leads by a >=+1.0pp/yr lift over Window A, the complements story is supported.

## Window-by-window real-GDP-per-capita growth

| Window | NZ growth %/yr | Donor-pool mean %/yr | Donor n | Gap pp |
|---|---:|---:|---:|---:|
| Pre 1980-1983 | +1.86 | +0.32 | 4 | +1.54 |
| A 1984-1988 (dereg only) | +1.42 | +3.35 | 4 | -1.93 |
| B 1989-1993 (+RBA) | -0.32 | +0.64 | 4 | -0.96 |
| C 1994-2000 (full stack) | +2.39 | +3.08 | 4 | -0.69 |

**Window-C minus Window-A lift: +1.24pp/yr** (threshold for SUPPORT: ≥+1.0pp/yr).

## Informative legs (do not gate verdict)

**PWT log-TFP gap (NZ − donor mean):** pre +0.056, A +0.013, B -0.005, C -0.010 (log units; lift C−A: -0.023).

**NZ CPI inflation by window:** pre 14.0%, A 11.4%, B 3.3%, C 1.8%. RBA-Act mechanism check (B − A): -8.0pp (negative = inflation fell after the RBA Act, consistent with the inflation-targeting mechanism).

## Method

Window-mean of WDI annual real-GDP-per-capita growth (`NY.GDP.PCAP.KD.ZG`) for NZ and for the donor-pool mean across AUS, USA, GBR, CAN. Three pre-registered sub-windows mapping to the three sequential reform stages (1984 deregulation, 1989 RBA Act, 1994 FRA). PRIMARY (dispositive) verdict gates on the *pattern* of the gap across windows, not on a t-statistic — N is far too small (5 countries × ~5 years/window) for inferential statistics to carry weight. Informative TFP and inflation legs are reported for context but do not gate.

## Caveats

- Small-N (5 countries, 4 windows): sequential treatments overlap; clean attribution is impossible. This is a descriptive-comparative test of an institutionalist framing, not a causal-identification claim.
- Donor pool (AUS, USA, GBR, CAN) inherits its own contemporaneous shocks (e.g. AUS deregulated in parallel under Hawke-Keating; UK ran Thatcher-era reforms; USA had Reagan disinflation). The donor pool is NOT a clean no-reform counterfactual — it is the spec's chosen comparator for a 'similar Anglosphere economies' framing.
- Window boundaries are calendar-year aligned; reform implementation lags can shift effective treatment dates by 1-2 years.
- A market-liberal counter-reading (deregulation J-curve) predicts the same temporal pattern via different causal mechanism. This test cannot distinguish them — see `steelman` in the spec.

## Data

- world_bank_wdi:NY.GDP.PCAP.KD — `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-04-27T090917Z.parquet`
- pwt:rtfpna — `data/vintages/pwt/rtfpna@2026-04-27T090915Z.parquet`
- world_bank_wdi:FP.CPI.TOTL.ZG — `data/vintages/world_bank_wdi/FP.CPI.TOTL.ZG@2026-04-27T093450Z.parquet`

