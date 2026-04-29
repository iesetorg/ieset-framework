# Vienna social-housing rent-burden comparative

**Verdict:** partial — Only the rent-burden primary held; the HPI-no-runaway primary failed. AT overburden gap -2.8pp; AT cum HPI log-change +74.6% vs pool +43.5% (+31.1pp).

## Summary

- AT mean housing-cost-overburden rate 2010-2024: **18.4%**.
- Comparator-pool unweighted mean: **21.2%** (n=10 countries).
- Gap (AT minus pool): **-2.8pp** (threshold for SUPPORTED: <= -2.0pp).
- AT cumulative HPI log-change 2010-2024: **+74.6%**; pool mean **+43.5%**; gap **+31.1pp** (threshold for SUPPORTED: <= +5pp).
- Informative: AT mean monthly rent-CPI yoy **3.90%** vs pool **2.11%**.

## Method

Country-level descriptive comparison of Austria (Vienna's social-housing model is the dominant rental form in the capital) against an unweighted pool of European-capital countries: DEU, FRA, NLD, BEL, DNK, SWE, IRL, ESP, ITA, CZE. Period 2010-2024 (HPI series start in 2010 for AT).

Two pre-registered primary tests:

1. **Rent burden gap.** Mean of `ilc_mded01` (housing-cost overburden rate, total household, total income, % of population) for AT minus unweighted comparator-country mean. Threshold: AT must trail by >= 2pp.
2. **No HPI runaway.** Cumulative log-change in `prc_hpi_a` (annual HPI, purchase=TOTAL with DW_EXST fallback) over the window for AT minus pool mean. Threshold: AT must not exceed the pool by more than +5pp.

Informative-only: mean monthly rent-CPI yoy (`prc_hicp_manr`, coicop=CP041) for AT vs pool, annualised by simple mean of the monthly yoy series.

## Caveats

- Country-level comparison; Vienna is dominant in the AT rental stock but not the entire country. Capital-city subnational series are not in vintages — when they land this hypothesis can be respecced as a capital-vs-capital cohort.
- GBR (London) excluded: Eurostat coverage ends 2018-2020 due to Brexit reporting changes.
- HPI window starts at 2010 (AT first observation in `prc_hpi_a`); earlier-period dynamics are not tested here.
- Eurostat building-permits / completions series (`bldg_pi_lt` in the spec) is not in vintages; the supply-collapse falsifier uses HPI-runaway as a proxy (a true supply collapse would show as AT prices outrunning peers). When permit data lands, supply growth should be re-tested directly.

## Data

- eurostat:ilc_mded01 (housing-cost overburden rate)
- eurostat:prc_hpi_a (house price index, annual)
- eurostat:prc_hicp_manr (HICP yoy, coicop=CP041 actual rents)
