# Vietnam Doi Moi developmental pattern — growth effect

**Verdict:** SUPPORTED — Vietnam log-GDP-per-capita ran +0.34 log-points (≈ +40%) above the equal-weighted SE-Asian donor pool (PHL, IDN, KHM, LAO, BGD, MMR) by 2010, base year 1990. Threshold was +0.25 log-points; cleared by +0.09. Long-window gap to 2019: +0.33 log-points (≈ +39%).

## Summary

Equal-weighted SE-Asian donor-pool counterfactual for Vietnam's post-Doi-Moi GDP-per-capita PPP. Vietnam treated in 1986; data effectively begins 1990 (WDI VNM coverage). Donor pool (at base year): PHL, IDN, KHM, LAO, BGD, MMR.

- **Primary log-gap by 2010**: **+0.34 log-points** (≈ +40% in levels) vs threshold +0.25.
- **Long-window gap to 2019**: **+0.33 log-points** (≈ +39% in levels).
- VNM log-index at 2010: +1.08; donor mean: +0.75.
- Overlap years base→2010: 21 (need ≥10).

## Informative metrics

- **mfg_value_added_pct_gdp**: data gap (missing series).
- **exports_pct_gdp**: data gap (missing series).
- **PWT TFP**: not available on this vintage.

## Method

- **Treatment**: Vietnam, year ≥ 1986 (Doi Moi).
- **Donor pool**: PHL, IDN, KHM, LAO, BGD, MMR (Southeast-Asian peers with comparable 1986 income, excluding the East Asian Tigers THA/MYS which are reference comparators rather than donors).
- **Counterfactual**: equal-weighted mean of donor pool log-GDP-pc-PPP, anchored to the first overlapping year (typically 1990 for WDI). No optimisation of donor weights — equal-weighting is a conservative baseline because it includes KHM/LAO/MMR which had their own catch-up booms post-1990; a true synth-DiD weight optimiser would likely down-weight these and INCREASE the gap.
- **Primary statistic**: cumulative log-GDP-pc gap (VNM minus donor-mean) at 2010.
- **Dispositive threshold**: +0.25 log-points (≈ +28% in levels). The spec asked for >+25%, rendered in log-space here.
- **Method validity gates**: ≥3 donors with data at base year, ≥10 overlap years base→2010.

## Caveats

- WDI's NY.GDP.PCAP.PP.KD coverage for VNM begins 1990, not 1986. The script anchors the index at the first overlapping year (1990 in current vintage). Pre-Doi-Moi macro data for VNM is sparse and not in WDI on the PPP basis — synth-DiD pre-trend matching in the strict sense is not feasible without alternate sources.
- Equal-weighted donor-pool counterfactual is NOT a true synth-DiD weight optimisation. v2 should run a proper synth with pre-1986 covariate matching where data permits, or fall back to PPP from PWT (which has earlier coverage).
- Donor pool excludes THA/MYS (East Asian Tiger / NIE peers). If those were included, the counterfactual would be higher and the Vietnam gap would be smaller. v2 robustness check.
- Author's market-liberal priors interpret Vietnam's success as primarily about market opening, not state-led pattern replication; this could under-weight industrial-policy evidence.

## Data

- world_bank_wdi:NY.GDP.PCAP.PP.KD — `data/vintages/world_bank_wdi/NY.GDP.PCAP.PP.KD@2026-04-27T091022Z.parquet`
- **MISSING** `world_bank_wdi:NV.IND.MANF.ZS`
- **MISSING** `world_bank_wdi:NE.EXP.GNFS.ZS`
- pwt:rtfpna — `data/vintages/pwt/rtfpna@2026-04-27T090915Z.parquet`

