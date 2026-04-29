# Bismarckian welfare architectures — fiscal sustainability under ageing

**Verdict:** inconclusive (data gap on oecd:PensionExpenditure, oecd:ImplicitPensionDebt, oecd:NetReplacementRate, oecd:SocialContributionRate) — none of the four pre-registered pension-specific metrics (pension expenditure / GDP, implicit pension debt / GDP, net replacement rate, total social contribution rate) are in the current data vintage. The Bismarckian-vs-Beveridgean comparison cannot be dispositively scored until the OECD pension-system fetchers land. Auxiliary (NOT dispositive — general-government, not pension-specific): in 2018-2023 Bismarckian general-gov debt is +25.9pp of GDP vs Beveridgean (Bismarckian 88.6%, Beveridgean 62.8%); general-gov expenditure +6.0pp (Bismarckian 49.8%, Beveridgean 43.9%). Sign of the gap (positive = Bismarckian higher) is the opposite of what the ordoliberal claim predicts for the pension-specific metrics, but general-gov fiscal aggregates can diverge from pension-specific outcomes.

## Summary

Pre-registered four-metric checklist comparing contributory-Bismarckian welfare states (DEU, AUT, CHE, FRA, BEL, ITA per spec coding) against Beveridgean tax-financed states (GBR, IRL, DNK, SWE, FIN, NOR, NLD, USA), in the 2018-2023 window where both groups face severe demographic ageing.

1. **M1 (PRIMARY)** — pension expenditure / GDP. Bismarckian-mean must be ≥1.5pp LOWER than Beveridgean.
2. **M2 (PRIMARY)** — implicit pension debt / GDP. Bismarckian-mean must be ≥1.5pp LOWER than Beveridgean.
3. **M3 (informative)** — net replacement rate. Directionally lower in Bismarckian (≥5pp).
4. **M4 (informative)** — total social contribution rate / wage. Directionally higher in Bismarckian (≥3pp).

**SUPPORTED** if BOTH M1 and M2 pass (the dispositive primaries). **REFUTED** if BOTH show Bismarckian ≥ Beveridgean (opposite sign). **PARTIAL** otherwise.

## Metric results

### M1 — Pension expenditure / GDP (PRIMARY)

**DATA GAP — series not in current vintage.** Re-runs automatically when the OECD pension fetcher lands.

### M2 — Implicit pension debt / GDP (PRIMARY)

**DATA GAP — series not in current vintage.** Re-runs automatically when the OECD pension fetcher lands.

### M3 — Net replacement rate (informative)

**DATA GAP — series not in current vintage.** Re-runs automatically when the OECD pension fetcher lands.

### M4 — Total contribution rate / wage (informative)

**DATA GAP — series not in current vintage.** Re-runs automatically when the OECD pension fetcher lands.

## Auxiliary (INFORMATIVE-ONLY) — general government fiscal aggregates

These are **NOT the spec's pre-registered pension-specific metrics**, they cover all government activity. Reported here only because the primary metrics are missing.

| Group | Gen-gov debt 2018-2023 (% GDP) | Gen-gov exp 2018-2023 (% GDP) | Debt drift since 1990-1995 (pp) |
|---|---:|---:|---:|
| Bismarckian | 88.6 | 49.8 | +14.9 |
| Beveridgean | 62.8 | 43.9 | +4.0 |
| Gap (Bi − Be) | +25.9 | +6.0 | — |

Ordoliberal claim predicts Bismarckian-lower on pension-specific metrics. The general-government aggregates above can diverge from pension-specific outcomes (e.g. Italy's high general-gov debt is largely structural / pre-ageing rather than driven by Bismarckian pension architecture per se).

## Method

Multi-metric checklist comparing two pre-defined country groups (Bismarckian / Beveridgean per spec.variables.treatment) on four OECD pension-system indicators. For each metric: country-window-mean over 2018-2023 per country, then group-mean across countries with data. Pass criterion: gap between group means in claimed direction at the pre-registered pp threshold.

## Caveats

- All four pre-registered pension-specific OECD series (`PensionExpenditure`, `ImplicitPensionDebt`, `NetReplacementRate`, `SocialContributionRate`) are missing from the current data vintage — `data/vintages/oecd/` contains broader SDMX bulk parquets but no pension-system fetchers. The verdict is `inconclusive (data gap)` until those land.
- The auxiliary general-government fiscal leg is **informative only** and is not the primary outcome. General-gov debt is driven by many forces (e.g. Italy's pre-existing structural stock, France's social-democratic-style universal coverage on top of contributory pensions) that are not the Bismarckian-architecture treatment.
- The spec's country-coding follows Esping-Andersen typology cross-walked to OECD pension-system classification. ITA/FRA/BEL are coded Bismarckian per the spec; other typologies sometimes place ITA in a 'Mediterranean' cluster. v2 should report robustness to that recoding.
- Old-age-dependency-ratio matching, requested by the spec's controls block, is not implemented in v1: WDI dependency-ratio series (`SP.POP.DPND.OL`) is also missing from the vintage. v2 should weight country contributions by dependency-ratio similarity.

## Data

- **MISSING** `oecd:PensionExpenditure` (blocks the pension_expenditure_pct_gdp leg)
- **MISSING** `oecd:ImplicitPensionDebt` (blocks the implicit_pension_debt_pct_gdp leg)
- **MISSING** `oecd:NetReplacementRate` (blocks the net_replacement_rate leg)
- **MISSING** `oecd:SocialContributionRate` (blocks the contribution_rate_total leg)
- imf:GGXWDG_NGDP — `data/vintages/imf/GGXWDG_NGDP@2026-04-26T154716Z.parquet`
- imf:exp — `data/vintages/imf/exp@2026-04-26T154728Z.parquet`
- world_bank_wdi:SP.POP.TOTL — `data/vintages/world_bank_wdi/SP.POP.TOTL@2026-04-26T162358Z.parquet`

