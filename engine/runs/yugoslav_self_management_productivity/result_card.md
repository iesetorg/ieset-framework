# Yugoslav self-management productivity 1965-1980

**Verdict:** SUPPORTED — Yugoslav real GDP-per-capita grew 4.67%/yr (log) over 1965-1980, vs southern-European peer mean 4.29%/yr (ITA 3.66, ESP 4.24, GRC 4.59, PRT 4.67). Ratio 1.089 is within the [0.75, 1.25] band; YUG outperformed by +0.38pp/yr. Productivity claim survives the descriptive test on this proxy.

## Summary

- **YUG** mean annual log-growth of real GDP per capita 1965-1980: **4.67%/yr** (n=15 year-on-year obs).
- **Southern-European peer mean** (ITA, ESP, GRC, PRT): **4.29%/yr**.
- **Ratio YUG / peer-mean**: **1.089** (test band [0.75, 1.25]).
- YUG vs peer-mean differential: **+0.38pp/yr**.

## Country growth 1965-1980 (mean annual log-Δ gdppc)

| Country | Mean log-growth (%/yr) | n yoy obs |
|---|---:|---:|
| YUG | 4.67 | 15 |
| ITA | 3.66 | 15 |
| ESP | 4.24 | 15 |
| GRC | 4.59 | 15 |
| PRT | 4.67 | 15 |

## Successor-state growth 1965-1980 (Maddison back-cast)

| Republic | Mean log-growth (%/yr) | n yoy obs |
|---|---:|---:|
| HRV | 4.96 | 15 |
| SVN | 5.27 | 15 |
| SRB | 4.79 | 15 |
| BIH | 4.09 | 15 |
| MKD | 4.64 | 15 |
| MNE | 4.95 | 15 |

## Method

- **Productivity proxy:** Maddison `mpd2020` real GDP per capita (2011 international dollars). PWT TFP (`rtfpna`) and PWT real GDP (`rgdpna`) do not cover Yugoslavia for 1965-1980 — PWT successor-state series begin 1990-1994. JST industrial-production lacks YUG. Maddison gdppc is the canonical long-run substitute when an employment series is unavailable.
- **Statistic:** mean of yoy log-differences of gdppc, 1966-1980 (15 obs per country). Robust to start/end-year noise relative to an endpoint CAGR.
- **Threshold:** the claim asserts *comparable* growth. We operationalise 'comparable' as YUG growth within ±25% of the unweighted southern-European peer mean (ITA, ESP, GRC, PRT). A symmetric band penalises both 'YUG fell behind' and 'YUG vastly outperformed' (the latter would re-open the question of whether commodity windfalls or external borrowing flattered the comparison — see steelman).

## Steelman against this verdict

Skeptics (the author included) would argue Yugoslav 1965-1980 growth was inflated by (a) Marshall-Tito remittance flows and external borrowing that funded above-trend investment, and (b) Maddison's back-cast for YUG that splices republican accounts with imperfect deflators. The high YUG growth shown here might therefore reflect financial leverage rather than self-managed firm productivity. A sharper test would condition on net external borrowing and decompose growth into TFP vs capital-deepening — but PWT TFP for YUG is unavailable, foreclosing that decomposition with on-disk vintages. Result is supportive of the market-socialist claim conditional on the proxy.

## Data

- maddison:mpd2020 (real GDP per capita, 2011 intl $)
