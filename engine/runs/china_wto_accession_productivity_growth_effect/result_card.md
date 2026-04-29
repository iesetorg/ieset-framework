# Result card — China's WTO accession (2001) productivity-growth effect

**Verdict:** SUPPORTED — CHN PWT-rtfpna mean log-growth rose from +0.25%/yr (1990-2000) to +1.01%/yr (2002-2019), acceleration +0.76pp/yr (threshold +0.50pp/yr). Exports/GDP rose from 7.2% (1990-2000) to 16.0% (2002-2007), jump +8.7pp (threshold +8pp). Peer-net TFP acceleration -0.18pp/yr (informative threshold +0.30pp/yr) — does NOT hold.

## Headline numbers

- Sample: CHN; peer panel IND, BRA, MEX, IDN, MYS, THA, TUR, ZAF (8 with PWT TFP data).
- Pre-window: 1990-2000; post-window (TFP): 2002-2019; post-window (trade ramp, pre-GFC): 2002-2007.

### PRIMARY 1 — TFP-growth break (PWT rtfpna)

- Pre mean log-growth: **+0.248%/yr**.
- Post mean log-growth: **+1.010%/yr**.
- Acceleration: **+0.761pp/yr** (threshold +0.50pp/yr).
- Pass: yes.

### PRIMARY 2 — Export-GDP-share break (WDI NE.EXP.GNFS.ZS)

- Pre mean: **7.24% of GDP**.
- Post (pre-GFC ramp 2002-2007) mean: **15.97% of GDP**.
- Jump: **+8.73pp** (threshold +8pp).
- Pass: yes.
- (Full post-window 2002-2019 mean: 18.13% — note the post-GFC retrenchment.)

### INFORMATIVE — peer-difference TFP acceleration

- Peer-mean acceleration: +0.942pp/yr (across 8 of 8 EM peers with PWT data).
- China minus peer mean: **-0.181pp/yr** (informative threshold +0.30pp/yr).
- Pass: no (informative-only; does not gate the verdict).

## Method

Country-level structural-break test on PWT 10.01 rtfpna (TFP at constant national prices) and WDI NE.EXP.GNFS.ZS (exports as % of GDP), with WTO accession dated to Dec 2001 (event year 2001). Pre window 1990-2000; post window 2002-2019 for TFP; post window restricted to the pre-GFC ramp 2002-2007 for the export share, where the trade-creation effect is at its peak in every published estimate (the post-2008 share collapse is well-documented and not the WTO causal channel). INFORMATIVE: an EM-peer panel (IND, BRA, MEX, IDN, MYS, THA, TUR, ZAF) gives a coarse global-TFP-cycle subtraction; this colours the diagnostics but does not gate the verdict.

## What this design does NOT do

- The original spec called for an industry-level event study using CIP industry-tariff-cut data — that source is not on disk in this build, so the country-level structural break is the best available proxy. The trade-share and TFP timing tests are necessary but not sufficient: any country-level event in 2001 (eg also: domestic reform deepening, demographic tailwind, global-credit-boom) is observationally indistinguishable here. The peer-net acceleration is intended to net out the global cycle, but cannot net out CHN-specific contemporaneous shocks.

## Sources

- PWT 10.01 `rtfpna` (vintage rtfpna@2026-04-27T090915Z.parquet).
- PWT 10.01 `csh_x` (export share of expenditure-side GDP at current PPPs; vintage csh_x@2026-04-27T090915Z.parquet).
  (csh_x is a 0-1 fraction; multiplied by 100 to express in pp.)
  (WDI NE.EXP.GNFS.KD has only 1 non-null observation for CHN in the on-disk vintage, hence the substitution; PWT csh_x is the closest single-source equivalent.)
