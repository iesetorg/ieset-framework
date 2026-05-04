# Intergenerational mobility — cross-country decomposition

**Verdict:** inconclusive - data gap on oecd:OECD.EDU.IMEP_DSD_EAG_FIN_DF_FIN_RESOURCES_1.0, oecd:OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0. The spec's primary regression cannot be estimated without a mobility outcome series and all three institutional-channel series. The v1 notes explicitly data-gate this test on an OWID or OECD intergenerational-mobility mirror, OECD Education-at-a-Glance subnational spending dispersion, and OECD Affordable Housing Database income-segregation indices. No coefficients computed.

## Summary

- The hypothesis requires a cross-country regression of mobility on three institutional channels (education-spending inequality, residential segregation, housing affordability) plus controls.
- The v1 spec flags the data gap explicitly: OECD SDD SOC mobility extension, Chetty opportunity-atlas (US-only), OECD Education-at-a-Glance subnational spending dispersion, and OECD Affordable Housing Database income-segregation support are not fully present in the local vintage set.
- 2026-05-04 source repair: the live OWID elasticity chart was mapped and fetched as the preregistered earnings-elasticity outcome; the bottom-to-top-quintile robustness outcome and the two OECD institutional-channel vintages remain unavailable.
- Required series: 2 outcome, 3 institutional-channel, 4 controls.
- Found on-disk: 6 of 9.
- Missing outcome: ['owid:share-of-children-in-the-bottom-quintile-who-make-it-to-the-top-quintile'].
- Binding missing series: ['oecd:OECD.EDU.IMEP_DSD_EAG_FIN_DF_FIN_RESOURCES_1.0', 'oecd:OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0'].
- Missing channels: ['oecd:OECD.EDU.IMEP_DSD_EAG_FIN_DF_FIN_RESOURCES_1.0', 'oecd:OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0'].
- Missing controls: (none).

## Method

Pre-registered specification (cross-section, n ~ 20):

    mobility ~ edu_inequality + residential_segregation
             + housing_affordability + log(GDP_pc) + Gini + gov_eff

Primary statistic: partial R-squared of the three institutional channels relative to the controls-only model. Secondary: partial R-squared of Gini alone, leave-one-out sign stability of each channel coefficient.

Falsification thresholds: partial_R2_channels >= 0.40 AND partial_R2_channels > partial_R2_gini_alone AND no single country flips a channel sign.

## Data

Required (per spec):

- `owid:intergenerational-earnings-elasticity` — available
- `owid:share-of-children-in-the-bottom-quintile-who-make-it-to-the-top-quintile` — **missing**
- `oecd:OECD.EDU.IMEP_DSD_EAG_FIN_DF_FIN_RESOURCES_1.0` — **missing**
- `oecd:OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0` — **missing**
- `bis:WS_SPP` — available
- `world_bank_wdi:NY.GDP.PCAP.PP.KD` — available
- `world_bank_wdi:SI.POV.GINI` — available
- `wgi:GOV_WGI_GE.EST` — available
- `world_bank_wdi:SE.TER.CUAT.BA.ZS` — available

Promotion verdict: inconclusive (method-validity gate fails on data availability). Per HANDOFF_TO_RUN_AGENT.md a data gap is NOT a refutation - the scoreboard treats this as neutral. Re-run when the remaining OECD subnational fetchers are wired.
