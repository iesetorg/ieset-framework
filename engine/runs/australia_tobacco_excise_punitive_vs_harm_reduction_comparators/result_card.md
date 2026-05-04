# Result — australia_tobacco_excise_punitive_vs_harm_reduction_comparators

## Verdict

**REFUTED** — REFUTED — AUS decline 11.3pp < comparator mean 21.07pp (threshold: <20.57pp)

## Summary

Australia's adult male smoking prevalence declined from 26.5% (2000) to 15.2% (2022), an absolute decline of **11.3 percentage points** (42.6% relative).

Comparator countries (harm-reduction approach):
- **New Zealand**: 17.8pp decline (31.2% -> 13.4%)
- **United Kingdom**: 22.4pp decline (38.5% -> 16.1%)
- **Sweden**: 23.0pp decline (51.9% -> 28.9%)

**Comparator mean decline: 21.07pp**

## Female smoking (informative)

- Australia: 11.6pp decline
- New Zealand: 18.5pp decline
- United Kingdom: 24.3pp decline
- Sweden: 24.8pp decline

## Method

Simple comparator calculation using WDI smoking-prevalence series (SH.PRV.SMOK.MA / .FE). No regression — the dispositive test is a direct comparison of absolute declines across four countries over 2000-2022.

## Data

- WDI male smoking prevalence: `./data/vintages/world_bank_wdi/SH.PRV.SMOK.MA@2026-04-30T114820Z.parquet`
- WDI female smoking prevalence: `./data/vintages/world_bank_wdi/SH.PRV.SMOK.FE@2026-04-30T114828Z.parquet`
