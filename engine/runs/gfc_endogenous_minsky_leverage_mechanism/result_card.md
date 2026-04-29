# GFC endogenous Minsky leverage build-up — pre-crisis scorecard

**Verdict:** SUPPORTED — 3 of 4 Minsky indicators passed (>=5 of 9 sample countries showing BOTH significant upward 2000-2007 trend AND magnitude threshold). I1: 7/8 PASS | I2: 4/8 fail | I3: 6/7 PASS | I4: 8/9 PASS

## Summary

- Sample: 9-country panel (USA, GBR, IRL, ISL, ESP, NLD, DEU, FRA, ITA), 2000Q1-2007Q4 quarterly.
- 3 of 4 Minsky indicators passed the cross-country test (need >=3 for SUPPORTED, <2 = REFUTED).
- METHOD_VALID gate: 8/9 countries have >=3 indicators on disk (floor: 6). PASS.

## Per-indicator results

- **I1** BIS private non-fin credit-to-GDP ratio (level) — 7/8 countries passed (need >=5). PASS — passing: ESP, FRA, GBR, IRL, ITA, NLD, USA.
- **I2** BIS credit-to-GDP gap (deviation from HP-trend) — 4/8 countries passed (need >=5). FAIL — passing: ESP, IRL, ITA, USA.
- **I3** BIS household debt-service ratio — 6/7 countries passed (need >=5). PASS — passing: ESP, FRA, GBR, ITA, NLD, USA.
- **I4** BIS real residential property price index — 8/9 countries passed (need >=5). PASS — passing: ESP, FRA, GBR, IRL, ISL, ITA, NLD, USA.

## Method

For each (country, indicator) cell over 2000Q1-2007Q4: fit a plain OLS time trend (in quarter-index units; log-transformed for the real-house-price indicator I4) and test whether the slope is positive at p<0.10. Separately compute the magnitude change from 2000Q1 to 2007Q4 and compare against an indicator-specific BIS early-warning-literature threshold:

  - I1 credit-to-GDP level: rise >= 20.0pp.
  - I2 credit-to-GDP gap: peak >= 10.0pp during 2005-2007 (Drehmann-Borio-Tsatsaronis 2011 'warning' band).
  - I3 household debt-service ratio: rise >= 1.0pp.
  - I4 real residential property price: cumulative log-rise >= 0.18 (~20%).

Country-indicator cell passes iff BOTH conditions hold. Indicator passes iff >=5 of 9 countries pass. Hypothesis SUPPORTED iff >=3 of 4 indicators pass; REFUTED iff <2 pass; PARTIAL if exactly 2 pass.

P-values are computed from a normal-tail approximation to the OLS-slope t-statistic (sample n~32 quarters; the threshold p<0.10 is far from any boundary case in this run, so the t-vs-normal gap is immaterial).

## Data

- bis:WS_CREDIT_GAP — credit-to-GDP ratio (CG_DTYPE=A) and gap (CG_DTYPE=C).
- bis:WS_DSR — household debt-service ratio (DSR_BORROWERS=H).
- bis:WS_SPP — real residential property prices (VALUE=R).

## Caveats

- Iceland (ISL) is not in BIS WS_CREDIT_GAP or WS_DSR; it carries only the real-house-price indicator. It is treated as missing (not as a failed test) per the METHOD_VALID rule.
- Ireland (IRL) is not in WS_DSR.
- Indicators are stipulated proxies for the original spec's broker-
dealer leverage and MBS-issuance series, neither of which is on disk. If those become available in a future fetcher pass, the spec should be re-promoted to v2.
- This is an associational pre-crisis trajectory test, not a causal identification of crisis origin. Even a clean SUPPORTED verdict is consistent with deregulation-driven (rather than purely endogenous) leverage build-up.
