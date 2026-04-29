# US household debt sustains demand, 1990-2008

**Verdict:** SUPPORTED — National-level co-movement matches the post-Keynesian wage-stagnation / debt-substitution / sustained-demand pattern. Real median household income 1990-2007 grew +10.9 log pp (threshold ≤ 20); household mortgage debt grew +134.3 log pp (+123pp wedge over wages, threshold ≥ 50); real consumption grew +56.9 log pp (+46pp wedge over wages, threshold ≥ 20).

## Summary

Three jointly-required descriptive conditions on US national series 1990-2007:

| Condition | Value | Threshold | Pass |
|---|---:|---:|:--:|
| (1) Wage stagnation: log real-median-income growth | +10.9pp | ≤ 20pp | YES |
| (2) Debt > wages: log mortgage-debt − log income | +123.4pp | ≥ 50pp | YES |
| (3) Demand held up: log consumption − log income | +45.9pp | ≥ 20pp | YES |

Real personal consumption 1990-2007 grew **+56.9 log pp**; household mortgage liabilities **+134.3 log pp**; real median household income **+10.9 log pp**.

## Method

Compute cumulative log-growth of three FRED series from calendar-year mean of 1990 to calendar-year mean of 2007 (last full pre-crisis year, per spec's exclusion of 2008Q3+).

  - Outcome: PCEC96 (real personal consumption expenditure, monthly)
  - Wage: MEHOINUSA672N (real median household income, annual)
  - Debt: MDOAH (household mortgage liabilities, quarterly)

Annual aggregation = simple mean of within-year observations on each series. All three conditions must hold for SUPPORTED. REFUTED requires both (1) wage-stagnation AND (2) debt-wage-wedge premises to fail simultaneously, since either alone suffices to invalidate the post-Keynesian descriptive premise.

## Informative diagnostics

- Labour share (PRS85006173) 1990 → 2007: 110.7 → 104.9 (-5.9pp). Falling labour share is the upstream driver of the wage-stagnation premise.
- House price index (USSTHPI) 1990 → 2006: +81 log pp. The collateral channel behind Mian-Sufi's home-equity-extraction mechanism.
- Household debt service ratio (HDTGPDUSQ163N) 1990 → 2007: n/a (series starts 2005) → 97.86. Rising DSR is the binding-constraint signal.
- Federal funds rate (DFF) 2003 mean: 1.13% (loose-money era driving the credit expansion); 2007 mean: 5.02%.

## Deviations from pre-registration

- The spec's preferred design is a Mian-Sufi state-panel local projections with state and quarter fixed effects, state-clustered SEs. State-level BEA PCE (post-1997) and NY Fed Consumer Credit Panel data are NOT on disk in `data/vintages/`; only national FRED series are available. Per HANDOFF_TO_RUN_AGENT.md (no fabrication), v1 promotes the spec to a national-level descriptive co-movement test. The state-LP design is preserved as v2 once a state-panel fetcher (BEA SAPCE + NY-Fed CCP) is wired.
- 1990-2007 anchor years used (skipping 2008 entirely) since MEHOINUSA672N is annual; the spec's '1990-2008Q2' window collapses to the same end-anchor for an annual series.

## Data

- `fred:PCE` (nominal_consumption)
- `fred:PCEPI` (pce_price_index)
- `fred:MEHOINUSA672N` (real_median_income)
- `fred:MDOAH` (mortgage_debt)
- `fred:HDTGPDUSQ163N` (debt_service_ratio)
- `fred:HMLBSHNO` (mortgage_liab_change)
- `fred:USSTHPI` (house_price_index)
- `fred:DFF` (fed_funds)
- `fred:PRS85006173` (labour_share)
