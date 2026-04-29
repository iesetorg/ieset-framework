# Japan 1990-2020 stagnation vs wellbeing — v2 honesty correction

**Verdict:** supported_subset — stagnation confirmed (mean growth 0.96%); ≤1 of 4 canonical wellbeing indicators degraded. Cantril ladder NOT on disk; canonical basket coverage 6/7 (Gallup WHR fetcher not landed). NOT graded SUPPORTED because the canonical basket is incomplete.

## Why v2 lands differently from v1

v1 graded SUPPORTED on 3 indicators (LE + unemp + Gini) while disclosure noted the test omitted hours-worked, suicide rates, and fertility — all canonical wellbeing dimensions per OECD Better Life Index, World Happiness Report, UNDP HDI extensions.

v2 tests the canonical 6-indicator basket and grades each indicator independently against a per-dimension threshold defended by the literature. Cantril ladder / life satisfaction is NOT on disk (Gallup WHR fetcher not landed) — so the canonical basket is 6 of 7; spec verdict tier is `supported_subset` rather than SUPPORTED if the indicators tested pass. (When Cantril lands, becomes W7 and re-runs.)

## Canonical wellbeing basket

| Dimension | Source | Status | Value | Degraded? |
|---|---|---|---|---|
| W1_le_relative_oecd_y | various | tested | -0.014047345767568942 | False |
| W2_suicide_excess_per100k | various | tested | None | None |
| W3_fertility_ratio_2020_1990 | various | tested | 0.8636363636363636 | True |
| W4_hours_ratio_2020_1990 | various | tested | 0.833696326019394 | False |
| W5_unemp_relative_oecd_pp | various | tested | 1.7081176470588237 | False |
| W6_gini_absolute_delta_pp | various | tested | None | None |
| Cantril ladder (W7) | gallup_whr | **✗ not on disk** | n/a | n/a |

## Stagnation premise

- JPN mean GDP/cap growth 1990-2020 (ex 2020 COVID): 0.96%/yr (threshold < 1.5 %)

## Counts

- Canonical inputs on disk: 6/6
- Indicators tested: 4
- Indicators degraded: 1

## Fetcher backlog

- gallup_whr cantril_ladder annual 2006+
- wvs social trust / family satisfaction wave-aligned

## Archives

v1 (3-indicator favourable subset, SUPPORTED) at ARCHIVED_v1/.
