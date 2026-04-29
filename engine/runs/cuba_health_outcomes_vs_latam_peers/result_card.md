# Cuban health outcomes vs LATAM peers, 1960-2000

**Verdict:** SUPPORTED — Cuba's 2000 LE was 75.9y vs LATAM peer mean 72.8y (gap +3.1y, threshold +1.0y). Cuban IMR was 6.8/1k vs peer mean 21.1/1k (ratio 0.32, threshold ≤0.50). LE rank 3/12, IMR rank 1/12. IMR-ratio improved (0.36 → 0.32) but the LE gap NARROWED (+6.0y → +3.1y) — peers caught up on life expectancy.

## Endpoint comparison

| Metric | Cuba 1960 | Cuba 2000 | Peer mean 1960 | Peer mean 2000 | 2000 gap / ratio |
|---|---:|---:|---:|---:|---:|
| Life expectancy (y) | 63.3 | 75.9 | 57.3 | 72.8 | **+3.1y** (need ≥ +1.0y) |
| Infant mortality (per 1k) | 36.6 | 6.8 | 102.8 | 21.1 | **0.32** (need ≤ 0.50) |

At 2000 Cuba ranks **#3/12** on life expectancy (higher = better) and **#1/12** on infant mortality (lower = better) within the 12-country pool (Cuba + 11 peers).

## Did Cuba pull away or just start ahead?

- LE gap 1960: +6.0y → 2000: +3.1y (change -2.9y).
- IMR ratio 1960: 0.36 → 2000: 0.32 (improvement +0.03).
- Pulled away on at least one metric: **True**.

## Soviet-subsidy sub-period (1991-2000)

Soviet bloc collapse cut Cuban subsidies hard from 1991. If the gap held or widened in 1991-2000, that points more towards system-architecture; if the gap narrowed, subsidies were doing more of the work.

- LE gap 1991: +3.5y → 2000: +3.1y.
- IMR ratio 1991: 0.32 → 2000: 0.32.

## Method

Descriptive endpoint comparison; no causal panel estimator. The thresholds come from a fair-reader interpretation of 'outperform' for a primary-care-emphasising system: at least one year better on LE at the endpoint, half-or-less infant-mortality vs the peer pool. The peer pool is the spec's 11 LATAM middle-income countries (MEX, BRA, ARG, CHL, COL, VEN, DOM, ECU, PER, URY, CRI). Method-validity gate: at least 8 of 11 peers must have data at the 2000 endpoint.

## Caveats

- WDI back-fills the Cuban 1960-2000 series from Cuban government sources. WHO GHO   independent life-expectancy estimates start around 2000, so a contemporaneous WHO   cross-check across the full window is not possible from current vintages.
- This is descriptive only — it does not separate Cuban primary-care architecture   from Soviet subsidy effects (1960-1991) or from primary-care diffusion across   peer countries (Costa Rica's primary care expanded substantially over the same   window and tracks Cuba closely).
- The 2000 ranking conditions on whichever peer countries had both an embargo-style   shock and a non-Cuban political system; Venezuela's 1999 oil collapse and   Argentina's 2001 crisis sit at the back end of this window.

## Provenance

- world_bank_wdi:SP.DYN.LE00.IN
- world_bank_wdi:SP.DYN.IMRT.IN

See `manifest.yaml` for exact vintages. Reproduces from `replication.py`.
