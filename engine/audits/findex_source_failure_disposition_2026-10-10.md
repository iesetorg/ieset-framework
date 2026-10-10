# Global Findex prospective source disposition (2026-10-10)

**Decision: six INCONCLUSIVE archival packets; zero graduates and zero public credit.** This was a genuinely new direct-survey source family, but its frozen 2017→2021 and 2021→2024 LMIC panel cannot support these six forward claims under the registered gates. Keep all six members in the Bonferroni denominator. Do not replace indicators, waves, countries, thresholds, or the exposure-concentration rule after measurement.

## Custody and sequence

- Official source: [World Bank Global Findex Database 2025 country workbook](https://www.worldbank.org/en/publication/globalfindex/download-data), 17,935,735 bytes, SHA-256 `b6c991f8e46bcbd4b6423cc962d5b2fa030e3db99832b9016bb4f400f57c772f`; the source [data catalog](https://datacatalog.worldbank.org/search/dataset/0039935/global-financial-inclusion-global-findex-database) lists CC BY 4.0. The workbook is cached locally and ignored by Git.
- `b36e693586f3ff00448a5eef344c10c423b77403` registered the six distinct claims, source-key-only 150-transition roster (SHA-256 `767cdc617b9d210a4ddaa088ece47bbb22a1f73a573a5fb748485554314ad777`), and frozen estimator before inspecting selected 2017/2021/2024 indicator values or missingness. The pre-registration audit discloses one accidentally printed **2011 Afghanistan** row from a preliminary headerless CSV export; that row is outside every registered panel cell.
- Six separate per-case source locks followed in commits `af628bf94313ffa0a19bee540aecceb1dc7e0853`, `3fb77b9395c2bdef0f364782030d2b9773b428b1`, `3ec95ed2e92de8166ce00d3f97e6ffd2797917bb`, `3546f93d4a44779691a4b83cf91589cd75108515`, `913c38cc91bea5567576d359f8ea441541a471d6`, and `b5adc3cd1d6ebcae71341c5dd449a258d5dd0547`. Only then did the measured run `58780eb56e7844d8df230502bb2e1a0ad92818eb` read the registered cells. Its six packets pass frozen exact replay with `python3 scripts/run_findex_financial_pathways_2026.py --verify`.
- The registered design requires at least 100 paired transitions, 50 economies, 20 with ≥5-point exposure movement, and no country or top 1% of rows carrying >20% of residualized exposure. Two-sided family alpha is 0.01 across all six tests. These are descriptive ecological questions, with no causal, policy, school, position, or featured claim.

## Failed source and admission gates

| Registered member | Frozen diagnostic | Disposition |
| --- | --- | --- |
| `findex_distance_account_forward_2026` | `fin11a.s` exposure missing/out of range on all 150 roster transitions; zero complete pairs | INCONCLUSIVE, no coefficient |
| `findex_cost_poor_account_forward_2026` | `fin11b.s` exposure missing/out of range on all 150; zero complete pairs | INCONCLUSIVE, no coefficient |
| `findex_documentation_women_account_forward_2026` | `fin11c.s` exposure missing/out of range on all 150; zero complete pairs | INCONCLUSIVE, no coefficient |
| `findex_mobile_formal_saving_forward_2026` | 110 complete pairs / 55 economies, but largest country and top 1% residualized-exposure share each `0.23928140038143092` against frozen `0.20` cap | INCONCLUSIVE, no admitted coefficient |
| `findex_digital_wages_emergency_funds_forward_2026` | 76 complete pairs / 38 economies after paired-transition rule, below 100 / 50 floors | INCONCLUSIVE, no coefficient |
| `findex_digital_payments_business_borrowing_forward_2026` | Business-borrowing outcome missing/out of range on 75 baseline and 76 later transition cells; zero economies with both transitions | INCONCLUSIVE, no coefficient |

The `fin11a.s`–`fin11c.s` columns exist in the workbook's series catalog, but no selected roster exposure cell is usable. Column presence alone did not establish time-series coverage. The business-borrowing column likewise cannot form this frozen two-transition panel. The mobile-saving case has enough nominal observations but fails its precommitted influence cap. These are source/admission failures, not negative association estimates or refutations. The [World Bank survey methodology](https://www.worldbank.org/en/publication/globalfindex/methodology) also documents collection differences across waves, limiting any interpretation of changes even if a panel passes the numeric gates.

For future source selection, inspect **key coverage and survey-wave definitions** before opening or choosing values, then register a genuinely distinct claim and source lock prospectively. Do not rerun these failed members with convenient substitutes or count them toward the user's graduate target.
