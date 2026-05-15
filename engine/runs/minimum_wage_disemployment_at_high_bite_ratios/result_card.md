# Minimum-wage disemployment at high bite ratios, 1990-2022

**Verdict:** inconclusive — data gap on bls:LAU_state_teen_employment_population_ratio_panel, bls:OES_state_median_hourly_wage_panel. The spec's primary stratified Callaway-Sant'Anna DiD on US-state cohorts split by bite ratio (state-min / state-median-hourly-wage) cannot be estimated without (a) the BLS LAU state teen employment-population panel, (b) the USDOL state minimum-wage history, and (c) the BLS OES state median-hourly-wage panel. On-disk BLS vintages currently include only national LNS/CES/CUUR series; the state fan-out has not been fetched. OECD contextual panels are present but cannot replace the preregistered US state cohort design. No coefficients computed.

## Summary

- Tests the Chicago-monetarist claim that high bite-ratio (state-min / state-median-hourly-wage ≥ 0.55) cohorts show measurable extra teen disemployment vs low bite-ratio (< 0.45) cohorts in the 1990-2022 US-state panel.
- Primary statistic: ATT(high-bite) − ATT(low-bite) on teen E/P, percentage points. SUPPORTED iff ≤ −0.020 pp at p<0.10.
- Informative: Dube-Lester-Reich border-county elasticity on QCEW NAICS-722 (food services); cross-country OECD bite-ratio panel regression for the 15 spec countries.
- Required series: 1 outcome, 2 treatment (state min-wage history + state median hourly wage), 1 border-pair, 2 OECD = 6 total.
- Found on-disk: 4 of 6.
- Missing primary outcome: ['bls:LAU_state_teen_employment_population_ratio_panel'].
- Missing treatment: ['bls:OES_state_median_hourly_wage_panel'].
- Missing border-pair: (none).
- Missing OECD cross-country: (none).
- Hold marker: HOLD until sibling-panel signs reconcile with the preregistered high-bite disemployment direction.

## Method

Pre-registered specification (50-state panel, 1990-2022, excluding 2020-2021 COVID labour-market shock):

    Step 1: bite_ratio_{s,t} = state_min_wage_{s,t} /
                                state_median_hourly_wage_{s,t}
    Step 2: assign each (state, treatment-cohort) to
            HIGH-BITE if max(bite_ratio) >= 0.55
            LOW-BITE  if max(bite_ratio) <  0.45
    Step 3: Callaway-Sant'Anna 2021 staggered DiD on teen E/P,
            state and year FE, never- and late-treated controls,
            state-clustered SE.
    Step 4: Differential = ATT_high - ATT_low (percentage points).

Falsification thresholds (dispositive):
  PRIMARY: differential ≤ -0.020 pp at p<0.10 → SUPPORTED.
  REFUTED if differential ≥ 0 at p<0.10 (Chicago direction wrong).
  REFUTED if |differential| < +0.005 pp with sufficient power (effect too small to support the claim).

Informative (not gating):
  Border-county DLR elasticity on QCEW NAICS-722 employment for state-pairs whose bite ratios diverge by ≥ 0.10.
  OECD MWUSD bite-ratio panel: low-skill unemployment rate ~ bite-ratio + country FE + year FE on the 15-country spec sample.

## Data

Required (per spec):

- `bls:LAU_state_teen_employment_population_ratio_panel` — **missing**
- `usdol:state_minimum_wage_history` — available
- `bls:OES_state_median_hourly_wage_panel` — **missing**
- `bls:QCEW_county_NAICS722_employment_panel` — available
- `oecd:MWUSD` — available
- `oecd:DSD_LMS_low_education_unemployment_rate` — available

Promotion verdict: inconclusive (method-validity gate fails on data availability — the primary state-level BLS outcome and median-wage bite-ratio inputs are not on disk; OECD contextual panels are present but cannot replace the preregistered US state cohort design). Per HANDOFF_TO_RUN_AGENT.md a data gap is NOT a refutation — the scoreboard treats this as neutral. Re-run when (a) the BLS state fan-out lands (LAU state teen E/P panel, OES state median hourly wage), and (b) sibling-panel signs reconcile with the preregistered high-bite disemployment direction.
