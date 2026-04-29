# Keynes 1930 'Possibilities for Our Grandchildren' growth-target check

**Verdict:** SUPPORTED — Population-weighted mean ratio of real GDP per capita (2018/1930) across the 18-country OECD panel is 6.66x, above Keynes's lower bound of 4x. 18/18 countries individually meet the 4x threshold; 4/18 also clear the 8x upper bound.

## Summary

- Anchor year **1930**, latest year **2018** (Maddison MPD2020).
- Population-weighted mean ratio (latest/1930): **6.66x**.
- Equal-weighted country mean: **7.34x**; median **6.40x**.
- 18 of 18 countries individually clear Keynes's 4x lower bound; 4 also clear his 8x upper bound.

## Threshold applied

- PRIMARY (dispositive): population-weighted mean of (GDP-pc[latest] / GDP-pc[1930]) across the 18-country panel >= **4x** (Keynes's lower bound).
- INFORMATIVE: equal-weighted mean, median, share of countries >= 4x, count of countries >= 8x (upper bound).
- METHOD_VALID: at least 14 of 18 panel countries observed at both endpoints — pass (18/18).

## Per-country ratios (Maddison 2011 PPP $)

| Country | GDP-pc 1930 | GDP-pc 2018 | ratio | >=4x? |
|---|---:|---:|---:|:---:|
| NOR |   5,781 |  84,580 | 14.63x | yes |
| IRL |   4,618 |  64,684 | 14.01x | yes |
| JPN |   3,334 |  38,674 | 11.60x | yes |
| FIN |   4,250 |  38,897 |  9.15x | yes |
| AUT |   5,716 |  42,988 |  7.52x | yes |
| ITA |   4,631 |  34,364 |  7.42x | yes |
| DEU |   6,333 |  46,178 |  7.29x | yes |
| SWE |   6,755 |  45,542 |  6.74x | yes |
| AUS |   7,504 |  49,831 |  6.64x | yes |
| CHE |   9,969 |  61,373 |  6.16x | yes |
| CAN |   7,669 |  44,869 |  5.85x | yes |
| DNK |   8,513 |  46,312 |  5.44x | yes |
| FRA |   7,224 |  38,516 |  5.33x | yes |
| NLD |   8,931 |  47,474 |  5.32x | yes |
| USA |  10,695 |  55,335 |  5.17x | yes |
| BEL |   7,936 |  39,756 |  5.01x | yes |
| NZL |   7,906 |  35,336 |  4.47x | yes |
| GBR |   8,673 |  38,058 |  4.39x | yes |

## Method

Long-run descriptive comparison. For each panel country with Maddison MPD2020 observations at both 1930 and the dataset's latest year (2018), compute the per-capita GDP ratio in 2011 PPP $. Aggregate across countries by:

1. Population-weighted mean (weights: end-year population); this is the dispositive primary statistic.
2. Equal-weighted country mean; reported as informative cross-check.
3. Median; informative for skew.

Maddison MPD2020 is the only published source that covers 1930 for the full advanced-economy panel; the WDI series `NY.GDP.PCAP.KD` only starts in 1960. The spec's secondary WDI series is therefore not used in this primary test.

## Caveats

- Maddison ends in 2018; Keynes's 100-year horizon was 2030. Adding the further ~10-15 years of observed OECD growth at trend (~1.5%/yr) would raise the ratios by another factor of ~1.15-1.25 — does not change a SUPPORTED verdict, would only tighten margins.
- 2011 PPP $ chaining tracks output, not subjective standard of living; Keynes's 'economic problem' framing is broader than GDP.
- The hypothesis is **descriptive**: a ratio computation, not a causal claim. The degrowth reframing question (whether the growth imperative still binds given the threshold has been met) is downstream, not tested here.
- Missing endpoint data: none.

## Data

- maddison:mpd2020 (vintage mpd2020@2026-04-26T134326Z.parquet)
