# Result card — liberal_democracy_managerial_flywheel_drift

**Verdict:** REFUTED — median final drift = -2.50 (13/26 positive, share = 50%). The corpus does not show monotonic statist drift across the liberal-democracy panel.

## Headline numbers

- Liberal-democracy panel size (in corpus): **26 of 26**
- Net-positive drift: **13** countries · zero: **0** · net-negative: **13**
- Median final composite drift: **-2.50**
- Median per-decade slope: **-2.05**
- One-sided binomial p (vs 50% null): **0.5775**

## Falsification legs

- (a) median final > 0: **FAIL** (-2.50)
- (b) share-positive significantly > 50% at p<0.05: **FAIL** (p=0.5775)
- (c) median per-decade slope > 0: **FAIL** (-2.05)

## Per-country panel (sorted by final drift, statist-leaning first)

| Country | First year | Final drift | Slope/decade | Movements |
|---|---:|---:|---:|---:|
| [USA](/country/USA) | 1976 | +56.0 | +6.27 | 24 |
| [DEU](/country/DEU) | 1976 | +38.0 | +7.97 | 19 |
| [AUT](/country/AUT) | 1976 | +31.0 | +4.02 | 15 |
| [JPN](/country/JPN) | 1976 | +28.0 | +3.35 | 18 |
| [IRL](/country/IRL) | 1979 | +24.0 | -0.04 | 17 |
| [KOR](/country/KOR) | 1976 | +18.0 | +1.95 | 11 |
| [FRA](/country/FRA) | 1976 | +17.0 | -0.71 | 17 |
| [SWE](/country/SWE) | 1976 | +15.0 | -0.45 | 14 |
| [POL](/country/POL) | 1976 | +12.0 | -1.01 | 16 |
| [AUS](/country/AUS) | 1976 | +12.0 | +1.20 | 9 |
| [NOR](/country/NOR) | 1976 | +2.0 | -1.48 | 9 |
| [BEL](/country/BEL) | 1976 | +1.0 | -2.62 | 14 |
| [CHE](/country/CHE) | 1976 | +1.0 | +1.51 | 2 |
| [GBR](/country/GBR) | 1976 | -6.0 | -0.43 | 20 |
| [HUN](/country/HUN) | 1976 | -8.0 | -3.12 | 10 |
| [NLD](/country/NLD) | 1977 | -11.0 | -6.66 | 18 |
| [ESP](/country/ESP) | 1977 | -13.0 | -5.02 | 15 |
| [DNK](/country/DNK) | 1976 | -17.0 | -5.63 | 9 |
| [CZE](/country/CZE) | 1993 | -19.0 | -5.84 | 10 |
| [NZL](/country/NZL) | 1976 | -20.0 | -5.66 | 10 |
| [ISR](/country/ISR) | 1977 | -20.0 | -7.93 | 16 |
| [FIN](/country/FIN) | 1979 | -27.0 | -6.60 | 12 |
| [PRT](/country/PRT) | 1976 | -28.0 | -8.08 | 10 |
| [ITA](/country/ITA) | 1976 | -29.0 | -11.05 | 25 |
| [CAN](/country/CAN) | 1980 | -29.0 | -6.58 | 10 |
| [GRC](/country/GRC) | 1976 | -36.5 | -9.69 | 14 |

## Steelman live concerns

See `hypotheses/steelman/liberal_democracy_managerial_flywheel_drift.md` for the strongest opposing case. Particularly relevant: the index measures legislated direction not absolute level (so Greece's negative value reflects forced post-memoranda austerity from a high baseline, not a low-state outcome), and the axis weighting is author-chosen (reweighting environmental + financial regulation could flip the sign for several countries).

## Provenance

Reproduces from `data/derived/country_drift.json` (rebuilt by `scripts/compute_country_drift.py`). Run with `python3 engine/runs/liberal_democracy_managerial_flywheel_drift/replication.py`.
