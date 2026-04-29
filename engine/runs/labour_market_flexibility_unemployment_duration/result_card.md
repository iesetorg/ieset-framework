# Result card — labour_market_flexibility_unemployment_duration

**Verdict:** refuted — primary EPL coefficient on long-term-unemp share is β=-1.364 (p=0.308); fails sign-and-significance test

Pre-registered: panel_FE_beta(EPL) on long_term_share > 0 at p<0.05 AND on duration > 0 at p<0.05 AND EPL beta survives p<0.10 after macro/UI control.

## Coefficient summary (TWFE country + year FE, clustered by country)

| Spec | Outcome | β(EPL_R) | SE | p | n_obs |
|---|---|---:|---:|---:|---:|
| primary | long_term_unemp_share | -1.3640 | 1.3358 | 0.308 | 262 |
| secondary | unemp_rate | -1.2271 | 2.0264 | 0.545 | 262 |
| robust | long_term_unemp_share + macro ctrl | -0.2612 | 0.7883 | 0.741 | 262 |

Sample N (primary): 262 country-year observations.

## Deviations from pre-registration

- Outcome substitution: Eurostat une_ltu_a long-term-unemployment share replaces OECD DSD_LMS median-duration (not in vintages).
- UI-generosity robustness control replaced with macro controls (trade openness + log GDP pc PPP) because OECD DSD_UBR not in vintages.
- Sample shrinks to EU/Eurostat-reporting countries (USA/JPN/KOR/MEX/AUS/NZL/CAN drop from primary because Eurostat lacks them).

## Steelman live concerns

See [hypotheses/steelman/labour_market_flexibility_unemployment_duration.md](../../../hypotheses/steelman/labour_market_flexibility_unemployment_duration.md) for the Bassanini-Duval heterogeneity argument, the flexicurity counterexample, and the v1-v2 EPL methodology break confound.
