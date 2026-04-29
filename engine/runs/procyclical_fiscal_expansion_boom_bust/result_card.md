# Result card — procyclical_fiscal_expansion_boom_bust

**Verdict:** PARTIAL — recession-depth gap procyclical−countercyclical = -3.09 pp meets the ≤-2 pp threshold (ARG+GRC+ESP+GBR mean min-5yr-fwd = -4.87% vs CHL+NOR+SWE+DNK+FIN -1.78%), and the local-projection IRF shows persistent negative cumulative growth at h=0..8. The 5-yr forward output-volatility primary spec is null (β=-0.0002, p=0.451), so the falsification is not jointly satisfied. The mechanism — procyclical fiscal in booms produces deeper subsequent recessions — is supported by the canonical cases; the volatility metric was the wrong summary statistic for it.

## Primary spec — 5-yr forward output volatility on boom-era procyclical impulse

| Term | Estimate | SE | 95% CI | p | t | n |
|---|---:|---:|:---:|---:|---:|---:|
| procyclical_impulse | -0.0002 | 0.0002 | [-0.001, +0.000] | 0.451 | -0.75 | 779 |

## Local-projection IRF (cumulative Δlog-GDP)

| Horizon h | β | SE | 95% CI | p | n |
|---:|---:|---:|:---:|---:|---:|
| 0 | -0.0017 | 0.0008 | [-0.003, -0.000] | 0.034 | 925 |
| 1 | -0.0033 | 0.0013 | [-0.006, -0.001] | 0.014 | 891 |
| 2 | -0.0048 | 0.0017 | [-0.008, -0.001] | 0.005 | 857 |
| 3 | -0.0066 | 0.0023 | [-0.011, -0.002] | 0.004 | 823 |
| 4 | -0.0062 | 0.0023 | [-0.011, -0.002] | 0.008 | 789 |
| 5 | -0.0060 | 0.0026 | [-0.011, -0.001] | 0.023 | 755 |
| 6 | -0.0060 | 0.0028 | [-0.011, -0.001] | 0.029 | 721 |
| 7 | -0.0049 | 0.0025 | [-0.010, -0.000] | 0.050 | 687 |
| 8 | -0.0052 | 0.0024 | [-0.010, -0.000] | 0.031 | 653 |
| 9 | -0.0040 | 0.0021 | [-0.008, +0.000] | 0.056 | 619 |
| 10 | -0.0028 | 0.0022 | [-0.007, +0.001] | 0.201 | 585 |

## Canonical-case comparison (boom-era 5-yr fwd minimum log growth)

- Procyclical canonicals (ARG, GRC, ESP, GBR): mean min5_fwd = -0.05099621501471131 log (-4.870291461938932%), n=53
- Countercyclical canonicals (CHL, NOR, SWE, DNK, FIN): mean min5_fwd = -0.018395693980437448 log (-1.778592959769862%), n=67
- **Gap (pro - ctr) in pp**: -3.0916985021690704

Falsification threshold: gap ≤ -2 pp.

## Provenance

Reproduces from vintages in `manifest.yaml`. See `replication.py`.
