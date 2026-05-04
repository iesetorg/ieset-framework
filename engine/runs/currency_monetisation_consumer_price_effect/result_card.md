# Currency monetisation and CPI pass-through

**Verdict:** SUPPORTED - USA and Japan both show base/CPI pass-through below 0.20 by regression coefficient and cumulative ratio.

## Results

| Country | Period | N | CPI/base coefficient | p-value | Cumulative pass-through |
|---|---|---:|---:|---:|---:|
| USA | 2008-01-01 to 2019-12-31 | 132 | -0.020 | 0.128 | 0.140 |
| JPN | 1998-04-01 to 2020-12-31 | 261 | 0.016 | 0.316 | 0.004 |

## Method

For each country, regress 12-month CPI inflation on 12-month monetary-base or central-bank-asset growth with HAC(12) standard errors. The registered support threshold is pass-through below 0.20 on both the regression coefficient and the cumulative CPI/base log-growth ratio.
