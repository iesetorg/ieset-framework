# Result card — us_median_wage_stagnation_1973_2000_decomposition

**Verdict:** weakened — bands not jointly satisfied. Feldstein wedge -35%; Gini-proxied top-strata residual 0%; compositional residual 135%. Pre-registered top-strata band [0.15, 0.50] violated: True

Pre-registered: 0.50 ≤ compositional_and_measurement_share ≤ 0.85 AND 0.15 ≤ top_strata_residual ≤ 0.50.

## Cumulative US 1973→2000 (data: JST Macrohistory wage/cpi/rgdpmad/gdp)

| Quantity | log change |
|---|---:|
| Real wage (JST wage / JST cpi) | +0.080 |
| Real GDP per capita (Maddison) | +0.542 |
| **Raw wage-productivity gap** | **+0.462** |

## Channel decomposition (illustrative, not all channels available)

| Channel | Share of raw gap |
|---|---:|
| (c) Feldstein CPI-vs-GDP-deflator measurement wedge | -35% |
| (d) Top-strata residual (Gini-proxied) | +0% |
| (a)+(b) compositional + benefit-substitution residual | +135% |
| Compositional + measurement combined | +100% |

Gini Δ 1973→2000: 0.4 → 0.4 (+0.0 points). Top-strata share derived via illustrative 0.015×Δgini/raw_gap mapping; WID top-1% share would be the correct series.

Sample N: 28 country-years (USA, 1973-2000).

## Deviations from pre-registration

- BLS CES0500000008 (production-and-nonsupervisory wage) not in vintages; JST Macrohistory `wage` substituted.
- BLS CES0500000002 (total compensation) not in vintages; benefit-substitution channel (a) skipped.
- WDI SL.TLF.CACT.FE.ZS (female LFP) not in vintages; compositional channel (b) skipped.
- OWID top-1-share-of-total-income not in vintages; OWID Gini substituted (coarser proxy).
- GDP deflator proxied as JST nominal GDP / Maddison real GDP, not BEA NIPA.
- The v1 result tests a weakened version of the spec: only the measurement wedge (c) is identified directly; (a), (b) are absorbed into the residual; (d) is illustrative via Gini.

## Steelman live concerns

See [hypotheses/steelman/us_median_wage_stagnation_1973_2000_decomposition.md](../../../hypotheses/steelman/us_median_wage_stagnation_1973_2000_decomposition.md) for the Bivens-Mishel rent-extraction reading, the EPI compensation-vs-output measurement debate, and the Feldstein-Lebergott household-vs-establishment series critique.
