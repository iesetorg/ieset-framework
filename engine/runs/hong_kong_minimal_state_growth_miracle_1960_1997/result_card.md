# Result card — Hong Kong minimal-state growth miracle, 1960–1997

**Verdict:** SUPPORTED — HKG/USA per-capita ratio 1997 = 0.80 (>=0.80); HKG annualised growth 1960-1997 = +5.22%/yr (>=5.0).

## Headline numbers

- Series: Maddison MPD2020 `gdppc` (2011 PPP $).
- HKG GDP-pc 1960 → 1997: $5,088 → $33,386 (cumulative +1.881 log-points; annualised +5.22%/yr).
- USA GDP-pc 1997: $41,723; HKG/USA ratio 1997 = 0.800.
- Comparator pool (USA, GBR, SGP, KOR, JPN, TWN) mean cumulative log-growth: +1.757; mean annualised: +4.89%/yr.

## Per-country trajectory 1960 → 1997 (Maddison 2011 PPP $)

| Country | GDP-pc 1960 | GDP-pc 1997 | cum log-growth | annualised |
|---|---:|---:|---:|---:|
| KOR |   1,548 |  21,056 | +2.610 | +7.31% |
| TWN |   2,157 |  23,438 | +2.386 | +6.66% |
| SGP |   3,464 |  34,868 | +2.309 | +6.44% |
| HKG |   5,088 |  33,386 | +1.881 | +5.22% |
| JPN |   6,354 |  33,038 | +1.649 | +4.56% |
| USA |  18,057 |  41,723 | +0.838 | +2.29% |
| GBR |  13,780 |  29,260 | +0.753 | +2.06% |

## Threshold applied

- PRIMARY: `HKG GDP-pc(1997) / USA GDP-pc(1997) >= 0.80` AND `annualised real growth(HKG, 1960-1997) >= 5.0%/yr`.

| Component | Threshold | Realised | Pass |
|---|---:|---:|:---:|
| HKG/USA ratio 1997 | >= 0.80 | 0.800 | yes |
| HKG annualised growth | >= 5.00%/yr | +5.216% | yes |

## Interpretation

This is a descriptive comparison; results are pattern matches, not causal identification. The Cowperthwaite-era policy regime is not separable in this estimator from (a) entrepôt geography at the mouth of the Pearl River Delta, (b) post-war waves of skilled mainland migration, (c) the regional East Asian manufacturing boom, or (d) British rule-of-law inheritance. Singapore (SGP) achieved comparable convergence with much heavier state intervention (HDB, CPF, GLCs), which is why a synthetic-control design is the right next step; the descriptive run only documents that the trajectory exists.

## Sources

- Maddison Project Database 2020 (vintage mpd2020@2026-04-28T124253Z.parquet).

## Steelman live concerns

See `hypotheses/steelman/hong_kong_minimal_state_growth_miracle_1960_1997.md`.
