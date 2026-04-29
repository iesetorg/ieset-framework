# Result card — eu_regulatory_burden_productivity_drag

**Verdict:** SUPPORTED — EU post-2018 productivity differential β=-0.0639 log points (p=0.082); placebo clean. Consistent with Draghi-report style competitiveness drag.

**Estimator:** panel_fe (linearmodels TWFE, country + year FE, country-clustered SE)  
**N obs:** 260  
**N treated EU countries (in panel):** 25  
**N non-EU controls (in panel):** 9  
**Period:** 2010-2024  
**Outcome:** log labour productivity (OECD PDB GVAHRS, real USD-PPP per hour)

## Primary spec (EU × post-2018)

| Term | Estimate | SE | 95% CI | p | t |
|---|---:|---:|:---:|---:|---:|
| eu_post_2018 | -0.0639 | 0.0365 | [-0.136, +0.008] | 0.082 | -1.75 |

## Cumulative spec (EU × post-2018 + EU × post-2022 incremental)

- **eu_post_2018**: β=-0.0685 (SE=0.0339, p=0.045)
- **eu_post_2022**: β=+0.0147 (SE=0.0229, p=0.522)

## PMR-channel sensitivity (controls for OECD PMR forward-filled)

- **eu_post_2018**: β=-0.0671 (p=0.072)

## Placebo (EU × post-2014 in pre-2018 sample)

- β_placebo = -0.0110 (p=0.599); placebo CLEAN (|t|<1.65).

## Falsification rule (from YAML)
Not supported if β_eu_post_2018 is non-negative or insignificant at p<0.10, OR if effect vanishes after PMR/COVID controls, OR if pre-2018 placebo registers.

## Caveats

- Single-control USA strengthening: panel includes CAN, AUS, JPN, KOR, CHE, NOR, NZL, GBR. 
  Identification still rests on cross-EU/non-EU differential post-2018, with country FE absorbing levels.
- COVID + energy shock confounds 2020-2022 window. Year FE soak common shocks, not heterogeneous ones.
- PMR vintages: only 2018 + 2023 observed; forward-filled ⇒ channel control is approximate.
- Productivity measurement is real-PPP-converted; level effects reflect OECD harmonisation choices.
