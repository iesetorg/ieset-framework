# BLOCKED — welfare_architecture_comparative_effectiveness

**Status:** Cannot run with currently-fetched vintages.

## Required data not available

The spec calls for three outcomes; none are fetched at the right granularity:

1. `retirement_income_replacement_rate_median` from OECD Pensions at a Glance (`oecd:DSD_PENSIONS@DF_PENSIONS_REPL_RATE`). The OECD vintages directory contains tax, health, education, prices, income-distribution dataflows but **no Pensions at a Glance dataflow**.
2. `elderly_poverty_rate` (66+ age group from `OECD WISE IDD`). The IDD parquet `OECD.WISE.INE_DSD_WISE_IDD_DF_IDD_1.0` is fetched but the 66+ poverty subseries is a slice that has not been verified runnable from the cached parquet without dataflow-specific decoding.
3. `sovereign_pension_net_liability_projection` is a constructed variable combining IMF `GGXWDG_NGDP` (present) with OECD pension-spending projections to 2050 (not fetched). Without the projection input the outcome cannot be built.

Treatment: `welfare_architecture_category` is a manual categorical coding (per spec) — implementable but not committed to the repo as a coding sheet.

Controls: `gdp_per_capita_ppp` (present), `SP.POP.DPND.OL` (NOT in WDI vintages — only `SP.POP.DPND` total dependency, and even that is missing), `SL.TLF.CACT.FE.ZS` (NOT in WDI vintages).

The spec itself notes: "Data-gated. ... The hypothesis is pre-registered now to lock the comparison logic; first-run execution waits on publisher readiness."

## What would unblock

1. OECD Pensions at a Glance dataflow ingested.
2. OECD pension-spending-projection dataset ingested.
3. WDI dependency-ratio + female LFP added to bootstrap.
4. Manual welfare-architecture coding sheet committed.

## Action

No replication.py written. The three pre-registered outcomes cannot be measured with currently-fetched vintages.
