# UK Attlee-era reforms: health outcomes & growth path (1945–1969)

**Verdict:** refuted — Only 0 of 3 primaries hold. Failed: life-expectancy, infant-mortality, 1950s growth. UK 1950s growth +1.69%/yr; LE gain +3.29y (peer-mean +4.45y); IMR cut 41.4% (peer-mean 53.5%).

## Summary

- **Life expectancy** at birth, UK 1948→1969: **68.37 → 71.66** years (gain +3.29y). Peer-mean gain across 8 continental peers: **+4.45y** (SD 1.80y). UK lag vs peer-mean: +1.16y; UK SD-distance from peer mean: -0.64.
  - PRIMARY 1 (FAIL): UK gain ≥ 3.0y AND UK lag ≤ 1.0y.
- **Infant mortality**, UK 1950→1969: **3.15 → 1.84** (OWID per-100 units), a **41.4%** reduction. Peer-mean reduction (8 peers, DEU dropped — coverage starts 1968): **53.5%**. UK lag: +12.1pp; UK SD-distance: -1.73.
  - PRIMARY 2 (FAIL): UK reduction ≥ 40% AND UK lag ≤ 10pp.
- **1950s real GDP per capita growth** (Maddison 1950→1959 mean YoY log-growth), UK: **+1.69%/yr**. Peer-mean: +3.74%/yr (range +2.41% to +7.83%).
  - PRIMARY 3 (FAIL): UK ≥ 2.0%/yr.

## Method

Three pre-registered primary statistics, all dispositive:

1. UK life-expectancy gain 1948→1969 vs the 9-country continental peer mean (DEU,FRA,NLD,BEL,ITA,SWE,DNK,NOR,CHE). Anchor 1948 instead of 1945 to avoid wartime-mortality asymmetry (NLD 1944 famine, FRA German occupation, ITA front, etc.) — using 1945 would mechanically advantage UK vs continental peers.
2. UK infant-mortality proportional reduction 1950→1969 vs peer-mean reduction. DEU is dropped from this peer set (OWID infant-mortality coverage starts 1968 only). Anchor 1950 rather than 1949 broadens peer coverage from 3 to 8. The OWID series appears to be expressed per-100 live births rather than the more common per-1000 — this does not affect proportional-reduction comparisons.
3. UK Maddison real GDP per capita YoY log-growth, mean over 1950-1959, against the spec's stated 2%/yr threshold.

Verdict logic: 3/3 → SUPPORTED, 2/3 → partial, ≤1/3 → refuted.
INFORMATIVE (non-gating): UK SD-distance vs peer-mean for both health metrics; peer-country growth comparison.

**Important caveat (in spec disclosure):** none of these primary tests are causal. Postwar global growth tailwinds and welfare-state convergence confound clean attribution to the Attlee bundle (NHS, nationalisations, public housing, National Insurance). Even if all three primaries pass, this evidence is *consistent with* the democratic-socialist claim, not proof of it.

## Data

- owid:life-expectancy (1543–2023, broad coverage)
- owid:infant-mortality (1949+ for most peers; DEU 1968+)
- maddison:mpd2020 (gdppc, real GDP per capita)
- world_bank_wdi:SP.POP.TOTL (population control, manifest only)
