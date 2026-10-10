# Three-domain forward calibration — result review

The three designs were frozen together in preregistration commit
`0321a985831c690cd839d99ff80708ee8c504525`; source files and their lock
entered the later commit `4483ef1f424fb945eb0504ce059421e31d07e135`.
After that lock, an out-of-range endpoint exposed a transformation-order bug.
Commit `e2e7336a1ddb5094f7dd43ee0c468363fc5f4033` moved the existing range
exclusion before its logarithm; the first attempt wrote no result artifacts.
The preregistered sources, endpoints, estimator, thresholds, and three-test
Bonferroni denominator were unchanged.

| Frozen question | Complete/key countries | HC3 slope | Two-sided p | Verdict | Binding gate |
| --- | ---: | ---: | ---: | --- | --- |
| Rule-of-law gain 2000→2010; homicide reduction 2010→2020 | 117/119 | −0.1391 | 0.3815 | PARTIAL | None |
| Tractor-stock gain 1990→2000; food-index growth 2000→2010 | 98/100 | −0.0192 | 0.4885 | PARTIAL | None |
| Self-employment-share decline 2000→2010; GDP-per-worker growth 2010→2020 | 176/215 | +0.0043 | 0.4884 | INCONCLUSIVE | Exposure p90−p10 spread 7.056 < 8; top-country residualized exposure share 0.178 > 0.12 |

The family cutoff was two-sided p≤0.01/3 (0.0033333). Neither estimable
association reaches it. The third question retains its `INCONCLUSIVE` verdict
even though a coefficient was computed, because two preregistered gates failed.
No result is a causal finding, policy effect, school win/loss, featured item, or
new supported graduation.

FAOSTAT's matching raw archive and derived parquet have identical selected
`Agricultural tractors` / `In Use` / `No` records at both exposure years:
273 selected-category rows match by M49/year, numeric value, and flag.
Among the 196 endpoint readings in the 98 complete tractor countries, 86 are
official (`A`), 108 are estimated (`E`), and 2 come from international
organizations (`X`). Thus the tractor association relies heavily on estimated
historical stock figures. No tracked fetch-manifest entry for that FAOSTAT
archive or parquet was found; hash custody and selected-row parity do not
establish an independent publisher ingestion trail.

Exact replay under system `python3` (NumPy 1.26.4) matched all generated
artifacts. `validate_specs.py` passed 6,294 specs, with 36 permitted existing
policy forward-reference warnings. Read-only link reciprocity found zero errors
or warnings; read-only scope alignment found zero errors and seven warnings.
The three evidence packets agree with diagnostics and manifests on verdicts,
family size three, and zero causal/policy/school/position/featured credit.
