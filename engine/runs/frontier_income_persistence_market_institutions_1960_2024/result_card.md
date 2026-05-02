# Result card — frontier_income_persistence_market_institutions_1960_2024

**Verdict:** supported — High-liberal frontier retention 100.0% vs low-liberal 47.1% (diff +52.9%pp, threshold >= 15%).

## Design

Countries in the top quartile of Maddison GDP-per-capita in 1960 are classified as
"frontier". Among these, split by median V-Dem `v2x_liberal` (market-institution proxy).
Outcome: share retaining top-quartile income status by 2018.

## Threshold

SUPPORTED if high-liberal retention >= 50% AND
(high-liberal − low-liberal) >= 15%pp.
REFUTED if high-liberal retention < low-liberal retention.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Total countries with data | 136 |
| Frontier 1960 | 34 |
| High-liberal (≥ median) | 17 |
| Low-liberal (< median) | 17 |
| High-liberal retention | 100.0% |
| Low-liberal retention | 47.1% |
| Difference | +52.9%pp |
| High-liberal mean log growth | 1.362 |
| Low-liberal mean log growth | 1.115 |

## Country panel

| ISO3 | GDPpc 1960 | GDPpc 2018 | v2x_liberal | High liberal | Retained | Log growth |
|---|---:|---:|---:|:---:|:---:|:---:|
| ARG | 8861 | 18556 | 0.655 | no | no | 0.739 |
| AUS | 14013 | 49831 | 0.946 | yes | yes | 1.269 |
| AUT | 10391 | 42988 | 0.821 | no | yes | 1.420 |
| BEL | 11081 | 39756 | 0.900 | yes | yes | 1.278 |
| BRB | 5316 | 11995 | 0.739 | no | no | 0.814 |
| CAN | 13952 | 44869 | 0.897 | yes | yes | 1.168 |
| CHE | 16358 | 61373 | 0.928 | yes | yes | 1.322 |
| CHL | 6781 | 22105 | 0.685 | no | no | 1.182 |
| DEU | 12282 | 46178 | 0.964 | yes | yes | 1.324 |
| DNK | 14046 | 46312 | 0.981 | yes | yes | 1.193 |
| FIN | 9931 | 38897 | 0.963 | yes | yes | 1.365 |
| FRA | 11792 | 38516 | 0.847 | yes | yes | 1.184 |
| GBR | 13780 | 38058 | 0.863 | yes | yes | 1.016 |
| HUN | 5816 | 25623 | 0.269 | no | no | 1.483 |
| IRL | 6825 | 64684 | 0.867 | yes | yes | 2.249 |
| ISL | 10959 | 43439 | 0.868 | yes | yes | 1.377 |
| ISR | 7433 | 32955 | 0.829 | no | yes | 1.489 |
| ITA | 9430 | 34364 | 0.837 | no | yes | 1.293 |
| JPN | 6354 | 38674 | 0.911 | yes | yes | 1.806 |
| KWT | 45929 | 65521 | 0.431 | no | yes | 0.355 |
| LBN | 5812 | 12559 | 0.479 | no | no | 0.771 |
| LUX | 15870 | 57428 | 0.891 | yes | yes | 1.286 |
| NLD | 13209 | 47474 | 0.946 | yes | yes | 1.279 |
| NOR | 11483 | 84580 | 0.945 | yes | yes | 1.997 |
| NZL | 15087 | 35336 | 0.896 | yes | yes | 0.851 |
| POL | 5125 | 27455 | 0.400 | no | no | 1.678 |
| QAT | 52299 | 153764 | 0.217 | no | yes | 1.078 |
| RUS | 5557 | 24669 | 0.062 | no | no | 1.490 |
| SAU | 5928 | 50305 | 0.150 | no | yes | 2.138 |
| SWE | 13849 | 45542 | 0.962 | yes | yes | 1.190 |
| TTO | 9964 | 28549 | 0.717 | no | yes | 1.053 |
| URY | 7643 | 20186 | 0.839 | no | no | 0.971 |
| USA | 18057 | 55335 | 0.838 | no | yes | 1.120 |
| VEN | 12116 | 10710 | 0.778 | no | no | -0.123 |

## Limitations

- V-Dem `v2x_liberal` is a liberal-democracy component, not a direct market-institution
  index. It correlates with property rights and rule of law but also captures judicial
  independence and legislative constraints.
- 1960 V-Dem scores are back-projected via expert coding for some countries.
- No direct measure of state-directed-credit intensity in 1960; low-liberal group is an
  imperfect proxy for the developmentalist-comparison group in the original hypothesis.
- Income threshold is relative (top quartile), not absolute frontier.

## Next robustness checks

- Use WGI Rule of Law (1996 earliest) as alternative institution proxy.
- Use absolute US-relative frontier threshold instead of quartile.
- Control for initial population size and resource endowments.
