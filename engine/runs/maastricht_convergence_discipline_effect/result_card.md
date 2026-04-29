# Maastricht convergence: discipline effect on inflation

**Verdict:** SUPPORTED — Treated peripheral states (ITA/ESP/PRT/GRC/IRL) narrowed their inflation gap to the German anchor by 5.81pp from 1985-1991 to 1996-2002, vs only 1.32pp for non-Eurozone controls (GBR/USA/JPN/CAN). DiD = -4.49pp (<= -3.0pp dispositive threshold). Mean treated inflation fell from 9.47% to 3.20%.

## Summary

- Pre-Maastricht window: 1985-1991.
- Post-Maastricht / convergence-test window: 1996-2002.
- Anchor (Bundesbank): DEU. Pre 1.85%, post 1.39%.
- Treated periphery (ITA/ESP/PRT/GRC/IRL): mean inflation 9.47% -> 3.20%, mean gap-closure to DEU -5.81pp.
- Non-Eurozone controls (GBR/USA/JPN/CAN): mean inflation 3.95% -> 1.53%, mean gap-closure to DEU -1.32pp.
- **DiD (primary statistic): -4.49pp.** Threshold for SUPPORTED: <= -3.0pp; partial range: (-3.0, -1.0]; refuted: > -1.0pp.

## Per-country results

**Treated periphery:**

| Country | Pre infl. | Post infl. | |gap to DEU| pre -> post | Closure |
|---|---|---|---|---|
| ITA | 6.26% | 2.49% | +4.40pp -> +1.10pp | -3.30pp |
| ESP | 6.73% | 2.82% | +4.88pp -> +1.43pp | -3.45pp |
| PRT | 12.81% | 3.02% | +10.96pp -> +1.63pp | -9.33pp |
| GRC | 17.97% | 4.47% | +16.12pp -> +3.08pp | -13.04pp |
| IRL | 3.59% | 3.20% | +1.74pp -> +1.81pp | +0.07pp |

**Controls:**

| Country | Pre infl. | Post infl. | |gap to DEU| pre -> post | Closure |
|---|---|---|---|---|
| GBR | 5.58% | 1.84% | +3.73pp -> +0.45pp | -3.28pp |
| USA | 3.95% | 2.40% | +2.09pp -> +1.01pp | -1.08pp |
| JPN | 1.72% | -0.02% | +0.14pp -> +1.41pp | +1.27pp |
| CAN | 4.56% | 1.92% | +2.71pp -> +0.53pp | -2.18pp |

## Method

Difference-in-differences on the absolute inflation gap to the Bundesbank anchor (DEU). For each country we compute window-mean WDI FP.CPI.TOTL.ZG over the 1985-1991 (pre-Maastricht) and 1996-2002 (post-Maastricht convergence-test) periods, then the absolute gap to DEU's window-mean. Per-country gap closure = |post-gap| - |pre-gap| (negative = convergence). Primary statistic is the difference of group-mean closures (treated - control).

Yields convergence is informative-only: vintage 10y sovereign yields for ITA/ESP/PRT/GRC across 1985-1991 are not unified on disk; falsification is on inflation alone.

## Data

- world_bank_wdi:FP.CPI.TOTL.ZG (CPI inflation, %YoY)
- imf:GGXWDG_NGDP (general government debt %GDP, informative)
