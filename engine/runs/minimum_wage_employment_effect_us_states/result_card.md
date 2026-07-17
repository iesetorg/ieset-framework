# US state minimum-wage employment effects, 1990-2024

**Verdict:** inconclusive — data gap on bls:LAU_state_teen_employment_population_ratio_panel, bls:CES_state_NAICS722_employment_panel. The spec's primary Callaway-Sant'Anna staggered DiD on the 1990-2024 US-state panel cannot be estimated without the state-level BLS LAU teen employment-to-population series and the USDOL state minimum-wage history. On-disk BLS vintages currently include only national-level series (LNS*, CES05*, CUUR*); the state fan-out (SMS*, LAUST*, ENU*-county QCEW) and the USDOL state-history table have not been fetched. No coefficients computed.

## Summary

- The hypothesis tests the post-1990 Card-Krueger / Dube-Lester-Reich consensus that state-level minimum-wage elasticities are small (in the [-0.15, +0.05] band) against the Neumark-Wascher claim of elasticities < -0.2.
- Primary statistic: Callaway-Sant'Anna staggered-DiD elasticity of teen employment-to-population ratio with respect to log state minimum wage on the 1990-2024 US-state panel.
- Secondary: Dube-Lester-Reich contiguous-county-pair elasticity on QCEW NAICS-722 (accommodation/food services) county employment.
- Required series: 2 outcome, 1 treatment, 2 border-pair, 2 controls = 7 total.
- Found on-disk: 2 of 7.
- Missing primary outcome: ['bls:LAU_state_teen_employment_population_ratio_panel', 'bls:CES_state_NAICS722_employment_panel'].
- Missing treatment: (none).
- Missing border-pair: ['manual:vaghul_zipperer_county_minimum_wage'].
- Missing controls: ['bls:LAU_state_unemployment_rate_panel', 'fred:state_real_gdp_panel'].

## Method

Pre-registered specification (50-state panel, 1990-2024, excluding 2020 COVID and federal-floor-binding state-years):

    log(teen_E/P)_{s,t} = beta * log(min_wage)_{s,t}
                        + alpha_s + tau_t + X_{s,t}'gamma + e

with state and year fixed effects, Callaway-Sant'Anna 2021 estimator using never- and late-treated states as controls. Standard errors clustered by state. Border-pair robustness uses Dube-Lester-Reich 2010 contiguous-county-pair fixed effects on QCEW NAICS-722 employment.

Falsification thresholds (dispositive):
  PRIMARY: CS_ATT_elasticity in [-0.15, +0.05] with 95% CI crossing zero → SUPPORTED.
  CS_ATT_elasticity < -0.15 significant at 5% → REFUTED (Neumark-Wascher direction).
  CS_ATT_elasticity > +0.10 significant at 5% → REFUTED (positive-effect direction).
  SECONDARY: border_pair_elasticity in [-0.20, +0.05] required for full SUPPORTED verdict.

## Data

Required (per spec):

- `bls:LAU_state_teen_employment_population_ratio_panel` — **missing**
- `bls:CES_state_NAICS722_employment_panel` — **missing**
- `usdol:state_minimum_wage_history` — available
- `bls:QCEW_county_NAICS722_employment_panel` — available
- `manual:vaghul_zipperer_county_minimum_wage` — **missing**
- `bls:LAU_state_unemployment_rate_panel` — **missing**
- `fred:state_real_gdp_panel` — **missing**

Promotion verdict: inconclusive (method-validity gate fails on data availability — state-level BLS series are not on disk; the BLS fetcher currently exposes only national LNS/CES/CUUR series). Per research documentation a data gap is NOT a refutation — the scoreboard treats this as neutral. Re-run when the BLS state fan-out (LAU state teen E/P, SMS state CES, ENU county QCEW) and USDOL state minimum-wage history fetchers are wired and the Vaghul-Zipperer county-minimum dataset is dropped into data/manual/.
