# Global Findex financial pathways — preregistration (2026-10-10)

This is a six-question **descriptive** family. The specification, six hypotheses, one key-only roster, and frozen runner are committed before selected indicator values, their missingness, or fitted results are inspected. The exact raw workbook is locked in later commits, one source-lock record per question; only then does the runner read selected cells. Failed questions remain in the six-test denominator and are reported INCONCLUSIVE. There is no school, policy, position, causal, or featured credit.

## Source and blind boundary

- Official World Bank [Global Findex 2025 country workbook](https://www.worldbank.org/en/publication/globalfindex/download-data), with its `Data` and `Series Table` sheets; source URL: `https://thedocs.worldbank.org/en/doc/be6615202d1f08a25855c8ac2d615122-0050012025/related/GlobalFindexDatabase2025.xlsx`. The World Bank catalog states CC BY 4.0 for Global Findex country data. The raw workbook is held in the ignored `data/vintages/world_bank_findex/` cache. The later source locks pin its SHA-256 and exact path.
- The Series Table labels the selected variables as adult-survey percentages. Numeric cells in this workbook are proportions; the frozen runner multiplies valid values by 100 to obtain percentage points. The survey measures adults aged 15+ in repeated cross-sectional samples, not a panel of the same individuals.
- Before registration, I read sheet names/dimensions, indicator **names and codes**, and the first eight key columns (economy code, year, region, income, demographic group). I did **not** inspect selected 2017, 2021, or 2024 indicator values, null masks, fitted coefficients, or outcome signs. An initial inspection mistakenly treated the headerless CSV export as a header and printed a single Afghanistan 2011 row. That observation is disclosed; Afghanistan 2011 and all 2011 observations are outside the frozen design. No selected study cell was seen.
- The fixed key-only roster contains **150 economy-transition keys in 75 economies**, with both 2017→2021 and 2021→2024 waves, among World Bank low, lower-middle, and upper-middle income groups. Its SHA-256 is `767cdc617b9d210a4ddaa088ece47bbb22a1f73a573a5fb748485554314ad777`. The official workbook also has some 2022 survey rows, which are explicitly excluded. The roster is an upper bound; cell-level missingness may reduce the sample.
- World Bank survey methodology documents questionnaire/mode changes during COVID and a 2024 return to face-to-face interviewing in 22 economies. These are measured associations across changing survey samples. No apparent Findex trend will be attributed to a legal reform or digital-payment policy.

## Six theory-specific cells

`x` is the exposure at the first wave; `y` is the change in the named outcome from first to next wave. All inputs are adult percentages, in percentage-point units after multiplying workbook proportions by 100. Outcome demographics are direct Findex subgroup estimates; the unbanked-barrier exposures are percentages **among adults without an account** rather than percentages of all adults. The same indicator's baseline outcome is an adjustment variable, not an extra test.

| ID suffix | Baseline exposure `x` | Later outcome change `y` | Expected sign | Mechanism under test |
| --- | --- | --- | :---: | --- |
| `distance_account` | `fin11a.s`, unbanked citing distant institutions | `account.t.d`, all-adult account ownership | − | Physical access friction |
| `cost_poor_account` | `fin11b.s`, unbanked citing expensive services | `account.t.d`, poorest-40% account ownership | − | Cost barrier to low-income access |
| `documentation_women_account` | `fin11c.s`, unbanked citing missing documents | `account.t.d`, women's account ownership | − | Documentary access friction |
| `mobile_formal_saving` | `mobileaccount.t.d`, all-adult mobile-money account ownership | `fin17a.17a1.d`, all-adult formal/mobile-account saving | + | Account rails and saving use |
| `digital_wages_emergency_funds` | `fin32.acc.s`, wage recipients paid into an account | `fin24aP`, all-adult ability to raise emergency funds in 30 days | + | Payment formalization and liquidity |
| `digital_payments_business_borrowing` | `g20.any`, made or received a digital payment | `fin22e`, all-adult borrowing to start or operate a business, from any source | + | Payment participation and enterprise finance |

These are not a full Cartesian product of hundreds of Findex indicators. Some questions share underlying respondents, access pathways, or outcomes, and the outcome of business-purpose borrowing is **not** a registered-firm or formal-bank credit measure. Directional results, if any, remain ecological and associational.

## Frozen estimator and admission gates

1. For each roster economy and 2017 or 2021 anchor, require finite source proportions in `[0,1]` for exposure at anchor and the outcome at anchor and later survey wave. Do not impute, interpolate, switch source, winsorize, or replace an indicator. Keep only economies with **both** complete transitions; no geography substitution.
2. Fit ordinary least squares `Δoutcome_pp ~ exposure_pp/10 + baseline_outcome_pp/10 + economy fixed effects + transition fixed effect`, with economy-clustered CR1 covariance and two-sided Student `t(G−1)` inference. The exposure coefficient is the outcome-point difference per 10-point greater baseline exposure, conditional on the other columns. This specification has no causal identifying claim.
3. Require at least **100 complete economy-transition rows**, **50 economies**, both transitions, at least **20 economies** with ≥5-point 2017→2021 exposure change, full-rank design, positive finite cluster SE, and finite coefficient/p. Residualize exposure against every other design column; no single economy may carry >20% of squared residual exposure, the largest 1% of rows >20%, or either transition >60%. Fail closed as INCONCLUSIVE before assigning a directional label.
4. One fixed family of six tests uses two-sided family alpha 0.01, Bonferroni `p ≤ 0.0016666666666666668`. A coefficient in the expected direction of at least **0.5 outcome percentage point per 10 exposure points** at that p cutoff is SUPPORTED as a **descriptive association**. An equally strong and significant opposite sign is REFUTED. Other estimable outcomes are PARTIAL. Family failures are INCONCLUSIVE and remain counted in the six.
5. Keep the complete result packet, exact source hashes, original hypothesis copy, source lock, model diagnostics, fixed member roster, and a read-only exact replay. Require the first committed spec to validate against its original schema. Do not turn any displayed coefficient into school, position, causal, policy, or featured credit.

The local six-test correction controls only this declared family. It does not correct selection across the IESET archive. Survey sampling error, questionnaire differences, income classification, common trends, and reverse feedback remain possible explanations. A public PARTIAL record means the test was estimable and reviewable, not that its directional theory was confirmed.
