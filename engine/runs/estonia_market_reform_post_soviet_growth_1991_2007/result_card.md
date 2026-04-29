# Result card — Estonia market reform post-Soviet growth 1991-2007

**Verdict:** PARTIAL — recovery threshold pass=True (year_recovered=1998, 2007 vs 1991 = 70.53282727739165); Baltic−CIS gap pass=False (gap=5.1509956229348575)

## Recovery speed

| Country | 1991 level | Year recovered | 2007 vs 1991 (%) |
|---|---:|---:|---:|
| EST | 15350.6349 | 1998 | 70.53282727739165 |
| LVA | 13774.934 | 2003 | 52.758383452145765 |
| LTU | 12999.3089 | 2003 | 54.9195619160954 |
| POL | 7625.8427 | 1992 | 136.92369106957844 |
| HUN | 9255.9096 | 1993 | 113.52618547614162 |
| CZE | 12724.5409 | 1992 | 99.4791615625205 |
| SVK | 10537.4103 | 1994 | 100.333271638858 |
| SVN | 16401.9591 | 1994 | 69.69170347461726 |
| BLR | 11170.7611 | 2004 | 32.998599352375365 |
| UKR | 8899.0967 | 2006 | 16.369320944675202 |
| RUS | 12012.2355 | 2002 | 66.6477734306824 |

## Synthetic control (donors: LVA, LTU, POL, HUN, CZE, SVK, SVN)

- Pre-fit RMSE (log): 0.0054
- Post-1992 avg gap (log): -0.1595 (-14.74%)
- Donor weights: {'LVA': 0.0, 'LTU': 1.952697496183374e-17, 'POL': 1.3898768236911855e-17, 'HUN': 0.012156531183910859, 'CZE': 0.0, 'SVK': 0.11714201487355967, 'SVN': 0.8707014539425295}

## DiD: Baltics vs CIS, pre/post 1992 (entity FE, log GDP-pc)

- β_did = +0.0790 (p=0.413)
- 95% CI: [-0.112, +0.270]
- n = 114

## Cumulative growth 1995-2007

- Baltic mean: 82.59175697149156 pp
- CIS mean: 77.4407613485567 pp
- **Gap (Baltic − CIS)**: 5.1509956229348575 pp (threshold: ≥15 pp)

## Provenance

Reproduces from vintages in `manifest.yaml`. See `replication.py`.
