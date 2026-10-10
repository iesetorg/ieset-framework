# OECD tax / EU-SILC later-outcome family — pre-registration (2026-10-10)

This four-question **descriptive** family is registered after inspecting source manifests, file hashes, schema/dimension keys, prior claim text, and old result cards. Selected 2023 tax values, selected 2022/2025 `ilc_iw01`, `ilc_di01`, or `ilc_di12` values, and their null masks have not been read. An official-source web search did reveal 2025 *all-person* poverty observations and 2025 home-warmth observations in preliminary snippets. Those two series were withdrawn **before registration**; neither is a family outcome. Four separate per-case source locks will follow this registration commit before the first measured run. All four cases remain in the Bonferroni denominator even if a gate fails; no old archived hypothesis is silently converted.

## Source custody and timing

- OECD Global Revenue Statistics tax-to-GDP and top statutory PIT snapshots are pinned by `data/manifests/fetch_run_2026-07-23T153857Z_oecd_tax_structure.yaml`. The former is percent of GDP, not transfer spending; the latter is a statutory top rate, not an effective household tax rate. The official [OECD source](https://www.oecd.org/en/data/datasets/global-revenue-statistics-database.html) describes tax-to-GDP and tax structure as distinct comparative indicators.
- Eurostat `ilc_iw01` in-work poverty, `ilc_di01` bottom-quintile income share, and `ilc_di12` equivalised disposable-income Gini have tracked fetch manifests and exact hashes in the frozen runner. Their official dataset pages are https://ec.europa.eu/eurostat/databrowser/view/ilc_iw01/, https://ec.europa.eu/eurostat/databrowser/view/ilc_di01/, and https://ec.europa.eu/eurostat/databrowser/view/ilc_di12/.
- The exposure is **2023 OECD annual tax**. Baseline is **2022 EU-SILC survey**. Endpoint is **2025 EU-SILC survey**. [Eurostat methodology](https://ec.europa.eu/eurostat/en/web/income-and-living-conditions/information-data) states income survey year 2025 refers to **2024 income**. Thus 2022 income measures mainly reflect 2021 income, prior to exposure. This is a later outcome, not a 2025-income forecast or a tax intervention design.
- The source-key-only roster has **28 fixed countries**, with exact baseline/endpoint keys for all three Eurostat outcomes and total-tax 2023. Top-PIT 2023 has **24** of those country keys. Its SHA-256 is `44cf4948ee9ab46d90f462329a3e14be5e24dcc7cedb17a67fff315b29f4586c`. Country aggregates and unregistered substitutions are excluded. Key presence is an upper bound, not value completeness.

## Four distinct questions

| ID | 2023 exposure | 2022-to-2025 outcome change | Expected sign | Archive context |
| --- | --- | --- | --- | --- |
| `eu_tax_receipts_inwork_poverty_forward_2026` | OECD total tax revenue / GDP | Eurostat employed-adult in-work poverty | − | Prior tax-revenue / poverty result seen; later, narrower direct outcome |
| `eu_tax_receipts_gini_forward_2026` | OECD total tax revenue / GDP | Eurostat disposable-income Gini | − | Prior tax-revenue / Gini result seen; later direct outcome |
| `eu_top_pit_gini_forward_2026` | OECD top statutory PIT rate | Eurostat disposable-income Gini | − | Prior tax-rate / inequality results seen; different cross-country contrast |
| `eu_tax_receipts_bottom_quintile_forward_2026` | OECD total tax revenue / GDP | Eurostat bottom-quintile disposable-income share | + | Prior broad inequality result seen; later lower-tail direct outcome |

## Frozen estimator and admission gates

1. Require each registered exposure and both exact-dimension outcome cells finite in `[0,100]`. No imputation, alternate year, geography substitution, winsorization, or post-result country selection. A PIT case begins with 24 source-key countries; the other three begin with 28.
2. Regress the 2025-minus-2022 outcome in points on 2023 exposure divided by 10 and the 2022 outcome divided by 10, with intercept and HC3 uncertainty. Use two-sided Student `t(n−3)` p-values. This is a country-level descriptive association, not a causal or policy effect.
3. Require at least **20 complete countries**; exposure IQR at least **2 percentage points** for total tax/GDP or **5** for top PIT; full-rank design; no country above **20%** of squared exposure residualized on baseline outcome; maximum hat leverage at most **0.30**; positive finite HC3 SE and finite inference. Fail closed as INCONCLUSIVE before any directional label.
4. Fixed family alpha **0.01** over all four questions; Bonferroni two-sided `p ≤ 0.0025`. SUPPORTED is a coefficient in the registered direction at least **0.5 outcome point per 10 exposure points**; REFUTED is an equally strong significant opposite coefficient; otherwise an estimable case is PARTIAL. All four tests share the denominator even if any is INCONCLUSIVE.

No school, position, policy, causal, or featured credit can be assigned. These outcomes are correlated, the exposure is observational, and aggregate fiscal capacity does not identify tax-and-transfer mechanisms. Prior old results were seen and are disclosed in each spec and steelman.
