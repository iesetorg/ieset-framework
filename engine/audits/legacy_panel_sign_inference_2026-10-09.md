# Legacy panel sign inference audit

This is a metadata-only review queue, **not a corrected verdict set or graduation**. The generic legacy rule mentioned a treatment coefficient and then `p<0.10`. The former parser could read that p-value inequality as a negative coefficient sign. The parser now requires an inequality directly attached to the coefficient token and fails closed on this unpinned generic rule.

- Current generic-rule panel records: **64**
- Also in historical snapshot `e786a95e676c`: **64**
- Historical-to-stored inferred direction changes: **57**
- Stored directions differing from the fail-closed runner: **62**
- Historical-to-stored verdict label changes: **22**

A claim sentence such as ‘higher tax burden predicts lower participation’ needs a manually pinned sign. The current runner returns an unknown direction for these generic rules, so a future rerun cannot award SUPPORT or REFUTATION by text inference. A human must review the original claim and frozen rule before changing any old verdict. The legacy runs remain same-commit and archived; this audit adds no school credit.

## Highest-risk examples

| Hypothesis | Historical sign/verdict | Stored sign/verdict | Current runner sign |
| --- | --- | --- | --- |
| `market_income_school_completion` | +/REFUTED | -/SUPPORTED | ? |
| `market_reform_female_education` | +/INCONCLUSIVE_DATA_PENDING | -/SUPPORTED | ? |
| `market_entry_uniform_code_productivity` | +/SUPPORTED | -/REFUTED | ? |
| `payroll_tax_labor_force_participation` | +/PARTIAL | -/PARTIAL | ? |

All selected IDs and their paths, stored estimates, and label changes are in the JSON report.
