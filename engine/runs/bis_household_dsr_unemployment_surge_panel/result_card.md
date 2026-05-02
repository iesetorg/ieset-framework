# Household debt-service stress predicts unemployment surge

**Verdict:** partial - one of the regression or raw-contrast gates clears, but not both.

## Predeclared Test

High DSR is BIS household DSR >= 12 percent and >= country p75; outcome is WDI unemployment-rate change from year t to t+2.

## Results

- Usable panel: **3,366 observations**, **17 countries**.
- Clustered FE coefficient: **-0.583** (SE 0.551, p=0.2897, 95% CI [-1.662, 0.496]).
- Raw high-minus-normal mean: **0.888** (0.708 vs -0.180); treated observations: **306**.

## Caveats

This is a compact local-data panel verdict. It is useful as a falsifiable first tranche, but it should not be read as a structural causal design without stronger identification.
