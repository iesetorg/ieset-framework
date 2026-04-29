# Ethiopia developmental-state growth effect (1995-2010)

**Verdict:** partial — Ethiopia grew faster than the peer median (+20.6 log-points) and ranked #3/12, but did not meet both primary thresholds (rank #1 AND gap >= 20 log-points). Synthetic counterfactual gap at 2010 = -7.3 log-points.

## Summary

- Ethiopia cumulative log-GDP-per-capita (PPP) growth 1995-2010: **+59.7 log-points** (~82% in levels).
- SSA peer-pool median cumulative growth: **+39.1 log-points**; Ethiopia gap to median: **+20.6** (threshold 20).
- Ethiopia rank: **#3 of 12** (threshold #1).
- Synthetic-control-lite counterfactual gap at 2010: **-7.3 log-points**.

## Ranking

  1. MOZ: +84.6 log-points
  2. RWA: +64.7 log-points
  3. ETH: +59.7 log-points
  4. UGA: +55.5 log-points
  5. TZA: +45.4 log-points
  6. ZMB: +43.2 log-points
  7. GHA: +39.1 log-points
  8. MWI: +27.7 log-points
  9. SEN: +18.3 log-points
  10. KEN: +7.9 log-points
  11. MDG: -1.6 log-points
  12. BDI: -17.8 log-points

## Method

Two dispositive primary tests, then synthetic-control-lite as an informative robustness check:

1. Cumulative log-difference of WDI NY.GDP.PCAP.PP.KD from 1995 to 2010, computed for Ethiopia and each peer; Ethiopia must rank #1 (P1) AND its gap to the peer median must be at least 0.20 log-points (P2). The 0.20 threshold corresponds to roughly 22% extra per-capita PPP growth over 15 years versus the median peer — the magnitude a fair reader of "fastest sustained African growth" would expect to see for the Ethiopian developmental state to count as the binding cause.
2. Synthetic-control-lite using a Dirichlet sample search to weight the 11 SSA donor countries on pre-treatment (1991-1994) levels of log GDP per capita PPP. Counterfactual log GDPpc at 2010 reported.

Donor weights are not meant to compete with Abadie-Diamond-Hainmueller's quadratic programming SC; the panel is small and the donor pool is the spec's pre-specified peer pool, so the synth gap is reported as informative, not dispositive.

Mechanism diagnostics (gross capital formation share and trade openness, both as % of GDP) are reported as 1995->2010 changes for context but do not enter the verdict.

## Data

- world_bank_wdi:NY.GDP.PCAP.PP.KD (primary outcome)
- world_bank_wdi:NE.GDI.TOTL.ZS (gross capital formation, % of GDP)
- world_bank_wdi:NE.TRD.GNFS.ZS (trade, % of GDP)
