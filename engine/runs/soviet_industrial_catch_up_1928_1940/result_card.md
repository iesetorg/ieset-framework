# Soviet industrial catch-up, 1928–1940

**Verdict:** partial — USSR cum-log growth +0.594 exceeds WE-mean +0.188 (differential +0.406) but falls short of the +0.50 log threshold the spec requires. Direction of the claim holds; magnitude does not.

## Headline numbers

- Series: Maddison MPD2020 total real GDP = `gdppc x pop` (2011 PPP $).
- USSR (`SUN`) GDP 1928 → 1940: `369,683,496` → `669,629,490` (cumulative +0.594 log; annualised +5.08%/yr).
- WE comparator panel (DEU, FRA, GBR, ITA) mean cumulative log-growth: `+0.188` (annualised `+1.58%/yr`).
- USA cumulative log-growth: `+0.139` (annualised `+1.17%/yr`).
- **Primary differential** (USSR – WE-mean): `+0.406` log points (threshold ≥ +0.50).
- Differential vs WE+USA mean: `+0.416` log points (harder denominator — US was largely insulated from WE Depression timing).

## WE comparator trajectories 1928 → 1940 (Maddison)

| Country | GDP 1928 | GDP 1940 | cum log | annualised |
|---|---:|---:|---:|---:|
| DEU |    419,777,967 |    601,419,020 | +0.360 | +3.04% |
| FRA |    289,936,150 |    264,163,000 | -0.093 | -0.77% |
| GBR |    389,190,542 |    527,013,728 | +0.303 | +2.56% |
| ITA |    188,592,898 |    226,094,759 | +0.181 | +1.52% |

## JST industrial-production index (WE+USA only — RUS not in panel)

| Country | cum log iy | annualised |
|---|---:|---:|
| FRA | -0.199 | -1.65% |
| GBR | -0.234 | -1.93% |
| ITA | +0.002 | +0.02% |
| USA | -0.117 | -0.97% |

WE-only JST `iy` panel mean: `-0.144`. WE+USA JST `iy` panel mean: `-0.137`. JST has no USSR row, so a strict industrial-production like-for-like comparison cannot be made from the parquet vintages.

## Threshold applied

- PRIMARY: `cum_log(USSR, 1928→1940) − mean(cum_log(WE, 1928→1940)) >= 0.50`.
- PARTIAL: differential positive but below threshold (direction holds, magnitude does not).
- REFUTED: differential ≤ 0.

## Caveats not adjusted for in the headline

- Maddison's USSR series for 1928-40 is itself the   Davies-Wheatcroft / Markevich-Harrison reconstruction debate   output, not an independent measurement. Different reconstructions   give USSR 1928→1940 log growth between roughly +0.7 and +1.0;   treat the level as load-bearing only at one significant figure.
- The WE base is the Great Depression. Picking 1928 = peak and   1940 = early-rearmament-recovery flatters any   fast-industrialiser comparison; a 1928→1937 window narrows the gap.
- The 1932-33 famine, gulag labour, and consumption collapse   (real wages, retail goods availability) are not in the headline.   The claim is *output growth*, not *welfare growth*; this run   scores the literal claim, not the broader policy verdict.

## Sources

- Maddison Project Database 2020 (vintage `mpd2020@2026-04-26T134326Z.parquet`).
- Jordà-Schularick-Taylor R6 (vintage `jst_r6@2026-04-26T134334Z.parquet`) — WE+USA only.

