# Result card — german_manufacturing_va_decline_2017_2024

**Verdict:** refuted — DEU manuf-VA share change -1.76pp does not meet -2pp threshold (2017→2023)

**DEU manufacturing VA share (NACE C / TOTAL):** 22.49% (2017) → 20.74% (2023). Change: **-1.76 pp** (spec threshold: ≤ -2.0 pp).

## TWFE decomposition (country + year FE, DEU + EU peers)

| Spec | β(deu_post_2017) | SE | p | n_obs |
|---|---:|---:|---:|---:|
| baseline (DEU-post-2017 only) | -0.0446 | 0.0208 | 0.035 | 112 |
| full (+ REER + log wage cost + trade openness) | -0.0254 | 0.0173 | 0.145 | 112 |

Residual share (|full / baseline|): **0.569**
Channels absorb: **43%** of the DEU-post-2017 log-manuf-share effect.

## Single-channel attenuation shares

| Channel | β(deu_post_2017) when added alone | share of total attenuation |
|---|---:|---:|
| log_reer | -0.0467 | -0.11 |
| log_wage_cost | -0.0319 | +0.66 |
| trade_openness | -0.0344 | +0.53 |

Monocausal flag (any channel > 60% of attenuation): **True**.

Sample N: 112 country-year observations, DEU + FRA, ITA, NLD, SWE, ESP, BEL, AUT, 2010-2023.

## Deviations from pre-registration

- Eurostat nama_10r_3gva (NACE-C share of TOTAL GVA, current price) supplies the manufacturing-share trajectory.
- Energy-cost channel: NRG_PC_205 not in vintages; substituted via BIS REER (broad basket) and Eurostat nama_10_lp_ulc national-accounts ULC index. The substitution captures cost-competitiveness but NOT the energy-specific Energiewende+gas-shock pathway directly.
- China import-penetration channel and external-demand channel both skipped (TiVA + trade-weighted destination GDP not in vintages).
- Period clipped to 2010-2023; final 2024 numbers will require re-run when data refreshes.

## Steelman live concerns

See [hypotheses/steelman/german_manufacturing_va_decline_2017_2024.md](../../../hypotheses/steelman/german_manufacturing_va_decline_2017_2024.md) for the secular-deindustrialisation framing, the COVID-recovery composition argument, and the auto-sector-restructuring critique.
