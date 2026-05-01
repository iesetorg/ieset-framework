# Cuba health outcomes vs advanced-market peers, 1960-2000

**Verdict:** REFUTED — Cuba does not clear the advanced cutoff in the 7-country advanced-market subgroup. Ranks: LE #6/7, IMR #7/7, income #7/7; mean-health-vs-income gap 0.5.

## Primary thresholds

- Life expectancy rank in 2000 must be <= 4 within the 7-country subgroup.
- Infant mortality rank in 2000 must be <= 4 within the 7-country subgroup.
- Cuba's mean health rank must beat its income rank by at least 1.0 places.

## Cuba's standings

- 1960 ranks: LE #5, IMR #2.
- 2000 ranks: LE #6/7, IMR #7/7, income #7/7.
- Mean health rank in 2000: 6.5.
- Income minus health-rank gap: +0.5 places.

## 2000 rank table

| Country | LE rank | IMR rank | Income rank | Mean health rank | Income minus health |
|---|---:|---:|---:|---:|---:|
| JPN | 1 | 1 | 1 | 1.0 | +0.0 |
| ESP | 2 | 2 | 2 | 2.0 | +0.0 |
| GRC | 4 | 3 | 6 | 3.5 | +2.5 |
| ISR | 3 | 5 | 3 | 4.0 | -1.0 |
| PRT | 5 | 4 | 4 | 4.5 | -0.5 |
| CUB | 6 | 7 | 7 | 6.5 | +0.5 |
| KOR | 7 | 6 | 5 | 6.5 | -1.5 |

## Soviet-subsidy sub-period

- Cuba life expectancy: 73.8 in 1991 -> 75.9 in 2000.
- Cuba infant mortality: 10.3 in 1991 -> 6.8 in 2000.

## Method

This is the intentionally mean stress test. The comparator pool is restricted to Southern European and East Asian / Israeli market economies that are materially richer than Cuba and often cited as high-performing non-socialist health systems. The threshold asks for upper-half placement on life expectancy and infant mortality plus at least a one-place health-over-income overperformance. If Cuba still clears that bar, the claim has real reach; if it does not, the universal-superiority story is much weaker than the LATAM-only framing suggests.

## Caveats

- The Cuban health series still inherits official-reporting risk, and the rich-comparator pool is small enough that one-rank changes matter.
- Income rank again uses OWID's Maddison GDP-per-capita series because the WDI PPP endpoint is missing for Cuba. That choice is transparent, but the ranking should be treated as contextual rather than dispositive in itself.
- This subgroup test is descriptive, not causal. It is best read as a credibility stress test of broad Marxist-Leninist health-superiority rhetoric, not as a clean estimator of the effect of socialism.

## Provenance

- world_bank_wdi:SP.DYN.LE00.IN
- world_bank_wdi:SP.DYN.IMRT.IN
- owid:gdp-per-capita-maddison-2020

See `manifest.yaml` for exact vintages. Reproduces from `replication.py`.
