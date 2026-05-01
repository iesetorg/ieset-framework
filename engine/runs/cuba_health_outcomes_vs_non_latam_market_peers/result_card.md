# Cuba health outcomes vs non-LATAM market peers, 1960-2000

**Verdict:** PARTIAL — Cuba clears two of the three harder gates in the 21-country non-LATAM market-economy pool. Ranks: LE #6/21, IMR #7/21, income #18/21; mean-health-vs-income gap 11.5. Missed: IMR rank need <= 5.

## Primary thresholds

- Life expectancy rank in 2000 must be <= 7 within the 21-country pool.
- Infant mortality rank in 2000 must be <= 5 within the 21-country pool.
- Cuba's mean health rank must beat its income rank by at least 5.0 places.

## Cuba's standings

- 1960 ranks: LE #5, IMR #2.
- 2000 ranks: LE #6/21, IMR #7/21, income #18/21.
- Mean health rank in 2000: 6.5.
- Income minus health-rank gap: +11.5 places.

## 2000 rank table

| Country | LE rank | IMR rank | Income rank | Mean health rank | Income minus health |
|---|---:|---:|---:|---:|---:|
| JPN | 1 | 1 | 1 | 1.0 | +0.0 |
| ESP | 2 | 2 | 2 | 2.0 | +0.0 |
| GRC | 4 | 3 | 6 | 3.5 | +2.5 |
| ISR | 3 | 5 | 3 | 4.0 | -1.0 |
| PRT | 5 | 4 | 4 | 4.5 | -0.5 |
| CUB | 6 | 7 | 18 | 6.5 | +11.5 |
| KOR | 7 | 6 | 5 | 6.5 | -1.5 |
| MYS | 8 | 8 | 7 | 8.0 | -1.0 |
| TUN | 9 | 12 | 11 | 10.5 | +0.5 |
| JOR | 11 | 11 | 10 | 11.0 | -1.0 |
| THA | 12 | 10 | 9 | 11.0 | -2.0 |
| LKA | 13 | 9 | 14 | 11.0 | +3.0 |
| TUR | 10 | 14 | 8 | 12.0 | -4.0 |
| PHL | 15 | 13 | 17 | 14.0 | +3.0 |
| DZA | 14 | 15 | 12 | 14.5 | -2.5 |
| EGY | 16 | 16 | 13 | 16.0 | -3.0 |
| MAR | 17 | 18 | 16 | 17.5 | -1.5 |
| IDN | 18 | 17 | 15 | 17.5 | -2.5 |
| IND | 19 | 20 | 20 | 19.5 | +0.5 |
| BGD | 20 | 19 | 21 | 19.5 | +1.5 |
| PAK | 21 | 21 | 19 | 21.0 | -2.0 |

## Advanced-market subgroup check (ESP, PRT, GRC, ISR, JPN, KOR, plus Cuba)

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

Descriptive rank-table test only. The dispositive question is whether Cuba remains genuinely competitive once the comparison pool expands beyond a friendlier Latin American frame. Life expectancy and infant mortality come from WDI; income-rank context comes from the OWID-packaged Maddison GDP-per-capita series because the WDI PPP-per-capita vintage does not report a usable Cuba 2000 endpoint. Method-validity requires Cuba plus at least 18 of the 20 non-Cuban comparators at the 2000 endpoint on life expectancy, infant mortality, and income.

## Caveats

- WDI back-fills Cuba's 1960-2000 health series from Cuban official reporting; the usual official-data caveat still applies, especially for infant mortality classification practices and the lack of a full-window WHO-independent backfill.
- Income rank uses OWID's Maddison GDP-per-capita series rather than WDI PPP-per-capita because Cuba's WDI PPP endpoint is missing. That preserves cross-country comparability, but the exact income-rank gap should be read as an approximate context metric, not a causal control.
- A strong or weak rank in this pool does not by itself identify socialism as the cause: Soviet transfers, pre-revolution baseline, sanctions, public-health prioritisation, and state capacity remain bundled together.

## Provenance

- world_bank_wdi:SP.DYN.LE00.IN
- world_bank_wdi:SP.DYN.IMRT.IN
- owid:gdp-per-capita-maddison-2020

See `manifest.yaml` for exact vintages. Reproduces from `replication.py`.
