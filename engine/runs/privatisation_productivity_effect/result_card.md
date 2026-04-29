# Thatcher-era UK privatisations and productivity

**Verdict:** refuted — GBR TFP growth FELL post-1984 (-0.51pp/yr, pre +0.97% → post +0.46%) AND underperformed the comparator-OECD mean (-0.55pp/yr; comparator post +1.01%). The productivity-from-privatisation premise does not show in PWT country-level TFP.

## Summary

- GBR mean annual TFP growth (PWT rtfpna) over 1975-1983 (pre): **+0.97%/yr**.
- GBR mean annual TFP growth over 1984-1990 (post): **+0.46%/yr**.
- Pre/post change: **-0.51pp/yr** (PRIMARY 1 threshold: ≥ +0.5pp; FAIL).
- Comparator-OECD post-1984 mean (FRA, DEU, ITA, ESP, NLD, SWE, USA, JPN): **+1.01%/yr**.
- GBR – comparator post: **-0.55pp/yr** (PRIMARY 2 threshold: ≥ +0.3pp; FAIL).
- DiD (post − pre, GBR vs comparator): **-1.01pp/yr**.
- Labour-productivity DiD (rgdpna/emp): **-0.80pp/yr** (informative).

## Method

Country-level TFP DiD around the 1984 BT privatisation anchor:

1. PWT 10.x rtfpna (TFP at constant national prices), log-differenced year-on-year for GBR and 8 OECD comparators.
2. Pre-window 1975-1983 (9 years, ending the year before BT). Post-window 1984-1990 (7 years, ending before the 1991 recession).
3. PRIMARY 1: pre/post change inside GBR ≥ +0.5pp/yr. PRIMARY 2: GBR – comparator-mean over 1984-1990 ≥ +0.3pp/yr.
4. Labour productivity (rgdpna/emp) reported as INFORMATIVE only.

**Caveats** (see steelman): country-level TFP cannot isolate the privatised-sector productivity effect from the rest-of-economy effect. The pre-1984 baseline includes Thatcher's 1979-1983 labour-shedding-under-public-ownership phase, which Florio (2004) argues did most of the lifting; this lifts the pre-mean and works AGAINST a privatisation-from-1984 finding. The 1980-1981 recession and recovery dynamics are an OECD-wide phenomenon and the comparator DiD addresses that confound. The price-reduction and cost-shifting components of the original claim are not tested.

## Data

- pwt:rtfpna
- pwt:rgdpna
- pwt:emp
