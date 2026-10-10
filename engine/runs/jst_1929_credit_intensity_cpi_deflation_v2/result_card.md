# jst_1929_credit_intensity_cpi_deflation_v2

**Verdict: PARTIAL.** Valid descriptive test; the registered positive
association was not supported or refuted at the two-test family threshold.

The 1929 private-loans/GDP entry measure and 1929–1933 consumer price level
loss were measured in **17** complete JST R6
advanced economies; 1 of 18 roster countries failed
the common complete-case rule. Credit-intensity spread was
**128.47 percentage points**; outcome-loss
spread was **23.09 log percentage points**.
All frozen source, sample, and variation gates passed.

- Spearman rank correlation: **-0.029**
- Two-sided permutation p-value (99,999 fixed-seed draws): **0.91230**
- Leave-one-country-out rho range: **-0.235 to 0.091**
- Family significance rule: p<=0.025 for each of two prespecified outcomes

The point estimate gives no reliable support for a positive
credit-intensity/severity relationship. The two outcomes are correlated
measurements of one question, not independent replications. Shared
Depression shocks and policy responses remain confounded; this record
adds **zero causal, policy, school, position, or featured credit**.

Registration: `fc2f718a82d9628c960cf8507aae864b27f8b75c`.
Metadata-only source lock: `8d877a863f15f186bfd3cc9d673cae4224ac40c4`.
Source: JST Macrohistory Database R6,
https://www.macrohistory.net/database/ ;
Jordà, Schularick and Taylor (2017), *Macrofinancial History and the
New Business Cycle Facts*. Licensed CC BY-NC-SA 4.0. Raw and
country-level values are not committed.

Exact replay: `python3 scripts/run_jst_interwar_credit_severity_2026.py
verify --source-parquet <local-JST-R6-parquet>`.
