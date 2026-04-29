# Result card — gdpr_digital_sector_firm_scale_effect

**Verdict:** NOT SUPPORTED at sectoral aggregate — none of (ICT log GVA-per-hour, ICT log emp, ICT emp share) shows EU-post-2018 negative differential at p<0.10. This is the falsification path flagged in the YAML notes — sector aggregate may mask firm-scale-distribution effects, which need v1.1 commercial firm data.

**Estimator:** panel_fe (TWFE, country + year FE, country-clustered SE)  
**Period:** 2010-2024  
**Outcomes (sector proxy):** OECD PDB ICT-sector (ACTIVITY=J) GVA per hour, employment, employment share  

## Sector-aggregate specs (EU × post-2018)

| Outcome | β | SE | 95% CI | p | t | n |
|---|---:|---:|:---:|---:|---:|---:|
| log_ict_lp (GVA/hr) | -0.0444 | 0.0778 | [-0.197,+0.109] | 0.569 | -0.57 | 444 |
| log_ict_emp | +0.0263 | 0.0333 | [-0.039,+0.092] | 0.430 | +0.79 | 473 |
| ict_emp_share | -0.0002 | 0.0010 | [-0.002,+0.002] | 0.843 | -0.20 | 473 |

## Cumulative DMA/DSA (EU × post-2022 incremental)

- **eu_post_2018** on log_ict_lp: β=-0.0462 (p=0.518)
- **eu_post_2022** on log_ict_lp: β=+0.0047 (p=0.892)

## Placebo (fake EU × post-2014, pre-2018 sample)

- β_placebo on log_ict_lp = -0.0081 (p=0.872); placebo CLEAN.

## Falsification rule
Hypothesis target outcomes (firm-revenue, scale-up rate, VC per firm) are data-gated on commercial Crunchbase / PitchBook. v1 weak proxy uses sector-aggregate ICT GVA-per-hour, employment, and employment share. Falsification: non-negative β on at least 2 of 3 outcomes at p<0.10, OR placebo flags pre-trend.

## Caveats

- This is the YAML's explicitly-flagged WEAK v1: sector-aggregate ICT outcomes 
  do not test firm-scale distribution (the hypothesis's true target). v1.1 needs 
  Crunchbase/PitchBook firm-level data.
- Sectoral productivity rising AND employment falling is consistent with smaller-
  firm exit + surviving-firm scale, which the firm-level test would distinguish.
- Capital-market depth (EU VC thinness pre-dates GDPR) is not controlled here.
