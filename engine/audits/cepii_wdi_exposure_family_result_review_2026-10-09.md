# CEPII Gravity × WDI three-test result review — 2026-10-09

The family was frozen in first-addition commit `a07e048ac1dbaf32d79e09e08a9b9267bf7a411d`, its seven narrow
vintages and official CEPII ZIP were locked in separate commit `cc51bd2b642e0911b58a65fc0c80de23b00b1e1d`,
and result packets were recorded in `530bd22cd76ffb0397a4dcac9a70b728e2f4be86`. The runner's read-only
`--verify` replay reproduced all three packets. The runner requires both
unchanged commits before its measured-value path can execute.

| Frozen association | Complete pairs / countries | Varying countries | Primary coefficient | Two-sided clustered p | Verdict |
| --- | ---: | ---: | ---: | ---: | --- |
| Foreign market-potential growth → next-year trade-share change | 4,674 / 122 | 122 | −10.1892 | 0.3669 | PARTIAL |
| FTA-covered distance-weighted market share → next-year private fixed-investment-share change | 1,310 / 69 | 49 | −1.2104 | 0.3435 | PARTIAL |
| FTA-covered partner-GDP share → next-year high-tech manufactured-export-share change | 1,145 / 104 | 60 | +3.0904 | 0.5808 | PARTIAL |

All three passed their complete-case and within-country variation floors;
the positive-share floors for the two FTA exposures also passed (868 and
1,036 rows). No coefficient clears the frozen two-sided Bonferroni threshold
of **p≤1/60** in either direction. These results therefore do not establish
the proposed positive associations. The third case has usable complete years
only from 2007–2020 despite its prospective 1995–2020 window; no year was
substituted or imputed.

The old 61-country CEPII FTA-growth roster was excluded, but eligible
countries and WDI vintages can overlap other IESET studies. B and C share
FTA coding and are correlated, so they are not independent replications.
Their exposure columns are unaffected by the `rta_coverage` label discrepancy
recorded in the separate CEPII cross-check. All three remain descriptive
calibrations with **zero causal, policy, featured, position, or school-score
credit**. Final public-tier inclusion requires the central evidence-tier,
preregistration, link, and scope audits; this note alone grants none.
