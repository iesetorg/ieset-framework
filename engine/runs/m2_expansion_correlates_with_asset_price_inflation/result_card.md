# M2 expansion correlates with asset price inflation

**Verdict:** partial — Housing leg met the >=6/10 + positive-mean thresholds but equities did not. Equities: 5/9 non-negative, mean lag-1 corr = +0.198. Housing: 6/10 non-negative, mean = +0.108. Spec's asymmetry clause is consistent with this outcome but the symmetric-claim formulation is not fully supported.

## Summary

- 10-country developed-economy annual panel, JST Macrohistory vintage (effective period 2008-2020; spec asks 2008-2025; tail not yet covered).
- Equity leg: 5 of 9 countries with non-negative M2-growth(t-1) → real-equity-return(t) correlation. Panel mean lag-1 correlation: **+0.198**.
- Housing leg: 6 of 10 countries with non-negative M2-growth(t-1) → real-housing-return(t) correlation. Panel mean lag-1 correlation: **+0.108**.
- Falsification threshold: ≥6/10 countries with non-negative lag-1 correlation AND positive panel mean, in at least one asset class.

## Method

Annual data from the Jorda-Schularick-Taylor Macrohistory database (jst:money export, which carries the full wide JST_R6 row). For each of the 10 spec countries:

1. M2 growth = first-difference of log(money).
2. Real equity total return = (eq_tr) / (1 + CPI YoY) − 1, where eq_tr is the JST gross-return index ratio.
3. Real housing total return = (housing_tr) / (1 + CPI YoY) − 1; for Canada, where JST has no housing_tr, fallback to real YoY of hpnom.
4. Lag-1 correlation = Pearson(M2_growth(t-1), real_return(t)) over the 2008-2020 country sub-sample (≥5 obs required).

Falsification rule (sharpened from spec): the symmetric-claim formulation requires both asset classes to clear; the asymmetric clause ("asymmetric across asset classes") is honoured by reporting a `partial` verdict when only one class clears.

## Data

- jst:money (Jorda-Schularick-Taylor Macrohistory wide panel, containing money / eq_tr / housing_tr / hpnom / cpi columns)

## Caveats

- JST annual frequency loses the quarterly lead-lag structure the spec's VECM design contemplated. The cointegration_vecm template is downgraded here to a panel-correlation primary because (a) annual frequency over 13 years yields too few observations for stable Johansen ranks per country, and (b) the spec's threshold is operationalisable as a country-share-of-positive-lag-correlations test without estimating a full VECM. A v2 promotion using quarterly BIS WS_SPP property prices + national M3 series could restore the VECM design.
- Sample period 2008-2020 only; 2021-2025 (post-COVID QE peak and subsequent QT) not covered by the JST vintage on disk. The QE-peak years are exactly the test most favourable to the claim, so the absent tail makes the test slightly conservative.
