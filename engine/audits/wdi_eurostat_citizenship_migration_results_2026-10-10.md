# WDI prior growth → Eurostat immigration by foreign citizenship: 30-cell result audit

Preregistration `c4468c0b3104fecdc4fb462f1f2a71f8dd360668`; source lock `8dd8ef2a2fcd23c245e83c86131b16b2e9c55e41`. Selected Eurostat outcome values and null masks were opened only after both commits. The 30 citizenship groups are disjoint counts but their destination exposure, years and shocks overlap.

Family alpha 0.01; Bonferroni two-sided per-test p≤0.000333333333333; |beta| threshold 0.5. Verdicts: SUPPORTED=0, REFUTED=0, PARTIAL=18, INCONCLUSIVE=12.

| Citizenship | Complete/key | ≥50 each year | Zero 2017/2019 | <100 2017/2019 | Beta | p | Verdict | Failed gates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `AL` | 24/24 | 16 | 0/0 | 11/8 | +3.434 | 0.03043 | **PARTIAL** | none |
| `AR` | 25/25 | 11 | 0/0 | 18/16 | not estimated | not estimated | **INCONCLUSIVE** | min_material_destinations |
| `BD` | 25/25 | 14 | 3/2 | 13/11 | not estimated | not estimated | **INCONCLUSIVE** | min_material_destinations |
| `BR` | 25/25 | 14 | 0/0 | 11/10 | not estimated | not estimated | **INCONCLUSIVE** | min_material_destinations |
| `CN` | 26/26 | 23 | 0/0 | 7/6 | -0.52 | 0.7907 | **PARTIAL** | none |
| `CO` | 25/25 | 12 | 2/0 | 16/15 | not estimated | not estimated | **INCONCLUSIVE** | min_material_destinations |
| `DE` | 25/25 | 23 | 0/0 | 5/6 | -0.1988 | 0.8502 | **PARTIAL** | none |
| `DZ` | 25/25 | 10 | 2/0 | 18/17 | not estimated | not estimated | **INCONCLUSIVE** | min_material_destinations |
| `ES` | 25/25 | 18 | 0/0 | 8/8 | -0.2922 | 0.9056 | **PARTIAL** | none |
| `FR` | 25/25 | 20 | 0/0 | 8/7 | +0.7534 | 0.75 | **PARTIAL** | none |
| `UK` | 26/26 | 24 | 0/0 | 4/3 | +2.444 | 0.1548 | **PARTIAL** | none |
| `GH` | 25/25 | 12 | 4/3 | 15/17 | not estimated | not estimated | **INCONCLUSIVE** | min_material_destinations |
| `IN` | 26/26 | 20 | 0/0 | 7/5 | +2.57 | 0.3223 | **PARTIAL** | none |
| `IT` | 26/26 | 24 | 0/0 | 5/4 | +0.7198 | 0.6577 | **PARTIAL** | none |
| `MA` | 25/25 | 14 | 1/1 | 12/13 | not estimated | not estimated | **INCONCLUSIVE** | min_material_destinations |
| `MD` | 24/24 | 11 | 1/1 | 15/14 | not estimated | not estimated | **INCONCLUSIVE** | min_material_destinations |
| `MX` | 25/25 | 13 | 2/0 | 14/13 | not estimated | not estimated | **INCONCLUSIVE** | min_material_destinations |
| `NG` | 25/25 | 15 | 2/1 | 13/12 | +6.551 | 0.09684 | **PARTIAL** | none |
| `NL` | 25/25 | 16 | 0/0 | 10/10 | +2.043 | 0.3692 | **PARTIAL** | none |
| `PK` | 26/26 | 14 | 1/1 | 13/11 | not estimated | not estimated | **INCONCLUSIVE** | min_material_destinations |
| `PH` | 25/25 | 15 | 0/0 | 12/9 | +5.894 | 0.05456 | **PARTIAL** | none |
| `PL` | 26/26 | 21 | 0/0 | 8/8 | +2.152 | 0.2475 | **PARTIAL** | none |
| `PT` | 26/26 | 18 | 0/1 | 11/9 | +0.5006 | 0.7683 | **PARTIAL** | none |
| `RO` | 27/27 | 22 | 0/0 | 7/7 | -2.101 | 0.2992 | **PARTIAL** | none |
| `RU` | 25/25 | 23 | 0/0 | 3/3 | +0.471 | 0.559 | **PARTIAL** | none |
| `TR` | 24/24 | 19 | 0/0 | 7/4 | +0.1487 | 0.9434 | **PARTIAL** | none |
| `UA` | 25/25 | 23 | 0/0 | 2/2 | +3.894 | 0.1075 | **PARTIAL** | none |
| `US` | 25/25 | 21 | 0/0 | 6/5 | -0.3769 | 0.7886 | **PARTIAL** | none |
| `VE` | 25/25 | 9 | 2/1 | 18/17 | not estimated | not estimated | **INCONCLUSIVE** | min_material_destinations |
| `VN` | 24/24 | 13 | 3/2 | 12/11 | not estimated | not estimated | **INCONCLUSIVE** | min_material_destinations |

Every finite nonnegative count, including zero and low flows, enters estimation; ≥50 in both years is a preregistered *sample quality gate*, not a value-based exclusion. All 30 cells remain in the correction denominator. Per-cell diagnostics include missing and invalid counts, exposure leverage and exact measured destination list. The preserved Eurostat parquet has no quality-flag column.

Citizenship is legal nationality, not country of previous residence, birth or departure. Immigration is residence establishment for at least 12 months. National statistical systems and policy differ. This is one observational episode of prior destination GDP growth and later immigrant-flow change; no causal, policy, school, position or featured credit. Local Bonferroni does not account for the wider IESET archive.
