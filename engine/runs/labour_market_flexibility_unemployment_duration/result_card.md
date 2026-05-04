# Result card — labour_market_flexibility_unemployment_duration

**Verdict:** refuted — primary EPL coefficient on long-term-unemp share is β=+1.952 (p=0.224); fails sign-and-significance test

Pre-registered: panel_FE_beta(EPL) on long_term_share > 0 at p<0.05 AND on duration > 0 at p<0.05 AND EPL beta survives p<0.10 after macro/UI control.

## Coefficient summary (TWFE country + year FE, clustered by country)

| Spec | Outcome | β(EPL_R) | SE | p | n_obs |
|---|---|---:|---:|---:|---:|
| primary | long_term_unemp_share | +1.9523 | 1.6020 | 0.224 | 566 |
| secondary | unemp_rate | +1.2601 | 1.6795 | 0.454 | 354 |
| robust | long_term_unemp_share + macro ctrl | +1.7188 | 1.1562 | 0.138 | 566 |

Sample N (primary): 566 country-year observations.

## Deviations from pre-registration

- Outcome substitution: Eurostat une_ltu_a long-term-unemployment share replaces OECD DSD_LMS median-duration (not in vintages).
- Workspace source substitution: Eurostat lfst_r_lfu3rt supplies long-term-unemployment rates because une_ltu_a is not on disk.
- Treatment substitution: inverted Fraser EFW area_5_regulation proxies labour/regulatory strictness because OECD EPL_R is not on disk.
- UI-generosity robustness control replaced with macro controls (trade openness + log GDP pc PPP) because OECD DSD_UBR not in vintages.
- Sample shrinks to EU/Eurostat-reporting countries (USA/JPN/KOR/MEX/AUS/NZL/CAN drop from primary because Eurostat lacks them).

## Steelman live concerns

See [hypotheses/steelman/labour_market_flexibility_unemployment_duration.md](../../../hypotheses/steelman/labour_market_flexibility_unemployment_duration.md) for the Bassanini-Duval heterogeneity argument, the flexicurity counterexample, and the v1-v2 EPL methodology break confound.
