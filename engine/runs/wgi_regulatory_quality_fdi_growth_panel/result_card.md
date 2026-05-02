# Regulatory quality predicts subsequent FDI intensity

**Verdict:** partial - one of the regression or raw-contrast gates clears, but not both.

## Predeclared Test

Supported if beta(regulatory_quality) >= 0.25 pp of GDP with p <= 0.10, and the top-minus-bottom RQ-tercile raw mean difference is >= 1.0 pp of GDP, with at least 800 observations and 40 countries.

## Results

- Usable panel: **1,345 observations**, **59 countries**.
- Clustered FE coefficient: **-1.130** (SE 0.955, p=0.2367, 95% CI [-3.002, 0.742]).
- Raw top-minus-bottom regulatory-quality tercile mean: **2.957**.

## Caveats

This is a compact local-data panel verdict. It is useful as a falsifiable first tranche, but it should not be read as a structural causal design without stronger identification.
