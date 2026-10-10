# JST interwar credit-intensity family — measured result, 2026-10-10

Two frozen, distinct outcome records ask one research question: whether greater
private loans relative to output at the 1929 entry year predicts deeper
1929–1933 real-GDP-per-person loss and CPI-index decline across the JST R6
advanced-economy panel. The two outcomes share an exposure, source,
countries, and years. They are **one correlated family**, not two independent
replications or two policy claims.

## Custody and frozen design

- Registration commit: `fc2f718a82d9628c960cf8507aae864b27f8b75c`.
- Real-output metadata-only source lock: `7e72876fc7eab2382af3e3316359e54335089b43`.
- Price-level metadata-only source lock: `8d877a863f15f186bfd3cc9d673cae4224ac40c4`.
- Measured result and packets: `96d6cacd8472f4c78215411c3d58ed58691c9b7a`.
- Licensed JST R6 local source SHA-256:
  `4219d53e595e50b05430b5e4edd91f5f9ebff3987e3d0b6f21d2f2f50bc03a6f`.
  The 36 fixed country-year keys and required field types were source-locked
  before any selected outcome values or null masks were read. Raw and
  country-level values were not committed.
- Frozen common complete-case floor: 12 countries; observed: **17 of 18**.
  The loan/GDP spread was **128.47 percentage points**, exceeding the 20-point
  floor. Both outcomes cleared their 5-log-point spread floors. Each test used
  a two-sided 99,999-draw fixed-seed permutation test and a **p<=0.025**
  Bonferroni threshold for the two-test family.

| Fixed outcome | Spearman rho | Two-sided permutation p | Leave-one-out rho range | Verdict |
| --- | ---: | ---: | ---: | --- |
| 1929–1933 real GDP per person loss | -0.250 | 0.33456 | -0.465 to -0.174 | PARTIAL |
| 1929–1933 CPI index decline | -0.029 | 0.91230 | -0.235 to +0.091 | PARTIAL |

Both rank estimates fail the prespecified positive-direction and corrected
significance rules. Neither is a statistically supported opposite-sign
refutation, so the frozen verdict for each is **PARTIAL**. A PARTIAL verdict
means a valid, inspectable test with no qualified directional finding, not
support for the credit-vulnerability claim. A larger source sample, different
episode, or alternative adjustment was not substituted after observing
these results.

## Schema erratum and public tier

The original registration commit contained `sample.temporal_structure:
cross_section` in both specs. The long-standing hypothesis schema accepts
`cross_section_with_justification`; the original files also lacked the
formal `cross_section_justification` field. The original registration
therefore **failed schema validation**, despite recording the 18-country
cross-sectional design, fixed estimator, family correction, and sample
gates in prose before value access. This defect was detected after the
measured result commit. A later metadata-only correction makes the current
top-level specs schema-valid and explicitly records this erratum; it leaves
the first registration blobs and measured outputs intact. It cannot
retroactively turn the tests into schema-valid blind preregistrations.

The source-locked public gate now validates the **original committed**
specification against the hypothesis schema and also requires current
byte identity. Both records therefore remain **ARCHIVE**, regardless of the
inspectable PARTIAL computations. They add **zero public conversions** and
zero school/position/featured/policy credit. The branch base public ledger
was 574; after counting the already tracked unrun ACS teen spec as an
additional archive, the corrected branch ledger is expected to be
**574 public / 2,145 total**, subject to regenerated checks. The original
result-commit replay passed exactly against the pinned source; the current
tip's original-runner verifier intentionally fails after the metadata edit.
To reproduce the measured computation, use an isolated checkout at
`96d6cacd8472f4c78215411c3d58ed58691c9b7a` and the same local
SHA-256-matched source. Do not rerun from altered current spec text.

The calculations do not identify the effect of private credit, monetary
policy, protectionism, or any Depression intervention. The source covers
18 advanced economies and splices historical series. Gold-standard
regimes, banking failures, trade shocks, and policy responses remain
confounded. The JST interwar trade-share calibration overlaps in
countries and years, so this family is not an independent replication of
that result.

Publisher and license: Jordà-Schularick-Taylor Macrohistory Database R6,
https://www.macrohistory.net/database/ ; Jordà, Schularick and Taylor (2017),
*Macrofinancial History and the New Business Cycle Facts*; CC BY-NC-SA 4.0.
