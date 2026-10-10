# WBES constraints and next-wave growth: measured-result audit

Date: 2026-10-10. Isolated results branch: `codex/ieset-wbes-results-2026`.
The blind family registration was committed at `cb4dee498b6235984f91030421bf999dda824306`; the frozen runner
at `e142e5f6c9b36fc4b1476b6eefc2fb8b71c01fc8`; and eight separate source locks ended at `590ea184f640149b7ec54e61d73cd9aca9287354` before
selected measurements were parsed. The post-lock text-decoding adapter and its
erratum were committed at `1b3e76f850c0bf5d7fa5185d7f1bfd11d7656d7b`, before the first measured run. All eight
measured packets were committed at `27aada91048ff27924fe95d0a2fe0f97f1e6b938`. No frozen specification,
roster, source lock, estimator, gate, or threshold was revised after results.

The exact World Bank Enterprise Surveys aggregate CSV has SHA-256
`bb3155ee0093c2833878b16e5f3587afa97b536ab3db0a893a8b870113d2b920`;
the official codebook has SHA-256
`6a7eab2649b80283960778194d053ad32b90685a710f91080c72de34c1d10bef`.
Both public CC BY 4.0 files remain in the ignored
`data/vintages/world_bank_enterprise/` source cache in this worktree. The
registration records the scout's isolated official-search outcome snippets;
the independent registrant saw only source metadata and survey keys.

| Baseline constraint | Later sales growth | Later employment growth |
| --- | --- | --- |
| Electricity rated a major obstacle (`in12`) | PARTIAL; slope -0.7819, p=0.52894 | PARTIAL; slope -0.2381, p=0.67628 |
| Finance rated a major obstacle (`fin16`) | INCONCLUSIVE; country influence gate | INCONCLUSIVE; country influence gate |
| Bribery incidence (`graft3`) | INCONCLUSIVE; country influence gate | INCONCLUSIVE; country influence gate |
| Senior management regulatory time (`reg1`) | PARTIAL; slope -0.8854, p=0.65088 | PARTIAL; slope +0.4324, p=0.69039 |

Slopes are annual growth percentage points per +10 percentage points of the
baseline constraint. Each cell had 114 complete adjacent-wave pairs across 49
countries before the influence gate. The four estimable cells passed all frozen
sample, variation, rank, uncertainty, and influence gates, but none met the
family Bonferroni two-sided `p <= 0.00125` rule. The finance and bribery cells
exceeded the registered 15% maximum concentration of residualized exposure in
one country, so no qualified coefficient is reported for them. The family
contains **0 SUPPORTED, 0 REFUTED, 4 PARTIAL, and 4 INCONCLUSIVE** results.

## Verification

- `python3 scripts/run_wbes_constraints_next_wave_encoding_adapter_2026.py --verify --source-root <local-source-root>` passed byte-exact replay for all eight packets after the result commit. `<local-source-root>` denotes the ignored local cache whose two source files match the frozen SHA-256 hashes.
- A packet's own `replication.py` invoked the same adapter and passed the eight-case exact replay.
- The strict preregistration index reported 962 strict registration pairs, 1,320 legacy same-commit pairs, and one unrelated unrun specification. All eight WBES records were `verified` in the evidence-tier audit.
- A read-only evidence-tier build using that fresh index classified the four PARTIAL cells as `calibration`, `public_visible=true`, and the four INCONCLUSIVE cells as `archive`, `public_visible=false` with `non_result_verdict`. The isolated branch had 661 public records among 2,283 hypotheses, four above its pre-result 657 count.
- `python3 scripts/validate_specs.py` passed: 6,469 spec files and clean cross-references. It emitted 28 permitted candidate-policy forward-reference warnings outside this family.

These are descriptive associations among changing formal-firm survey samples.
Shared source and overlapping outcome domains make the eight cells dependent;
they are not eight independent experiments. Survey timing, retrospective growth
windows, the 2022 sector-eligibility expansion, and country shocks limit
interpretation. The four public records receive no causal, policy-effect,
school, position, or featured credit. No integration, merge, or push was done
from this branch.
