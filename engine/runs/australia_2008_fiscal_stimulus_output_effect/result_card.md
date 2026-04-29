# Australia 2008 fiscal stimulus output effect

**Verdict:** SUPPORTED — AUS log GDP per capita rose +2.06pp 2007→2010 vs donor-mean -1.78pp; DiD = +3.84pp (≥ 2.0pp threshold). Pre-trend 2003→2007 DiD = -0.84pp (smaller). Donor pool: 12 countries excluding USA (ARRA).

## Summary

- Primary DiD (AUS minus donor-mean Δlog GDP per capita 2007→2010): **+3.84pp** (threshold ≥ +2.0pp).
- AUS 2007→2010 Δlog GDP per capita: +2.06pp.
- Donor-mean (excl. USA) 2007→2010 Δlog GDP per capita: -1.78pp.
- Pre-trend check 2003→2007 DiD: -0.84pp (should be smaller than the primary DiD).
- Robustness DiD with USA reincluded: +3.90pp.
- Secondary: AUS-vs-donor unemployment-rate change 2007→2010 = -0.53pp (negative = AUS labour-market outperformance).
- Secondary: AUS-vs-donor CPI-inflation change 2007→2010 = +0.75pp (small = MMT minimal-inflation-cost claim holds).
- Donor pool: CAN, GBR, NZL, DEU, FRA, ITA, JPN, KOR, CHE, NOR, SWE, NLD.

## Method

Spec called for synthetic-control matching of Australia 2008-2010 to a weighted OECD donor pool. The local venv has no synth library (`SyntheticControlMethods`, `pysynth`), so per the handoff doc's downgrade allowance this run uses an unweighted peer-mean DiD: AUS Δlog GDP per capita minus the simple mean of donor-pool Δlogs between 2007 and 2010. The donor pool is the spec's sample minus AUS minus USA (ARRA was the only sample peer with a comparable >2%-of-GDP cash-handout package; ~5.5% of GDP). Robustness with USA reincluded is reported separately.

Pre-trend 2003→2007 is checked against the primary 2007→2010 magnitude as a parallel-trends proxy. If the pre-trend is comparable or larger in absolute value than the primary effect, the verdict is downgraded to `weakened` regardless of the primary magnitude.

Secondary outcomes (unemployment-rate change, CPI inflation change) are reported as informative DiDs but do not gate the verdict.

## Data

- world_bank_wdi:NY.GDP.PCAP.KD
- world_bank_wdi:SL.UEM.TOTL.ZS
- world_bank_wdi:FP.CPI.TOTL.ZG
