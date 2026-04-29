# BLOCKED — green_transition_cost_trajectory_electricity_prices

**Status:** Cannot run with currently-fetched vintages.

## Required data not available

Primary outcome: `log_industrial_electricity_price`, sourced from constructed IEA + Eurostat NRG_PC_205 (industrial electricity prices). The IEA fetcher is not present (no `data/vintages/iea/` content with industrial price series), and Eurostat NRG_PC_205 is not in the fetched Eurostat series list (only `nrg_bal_s` energy balance is fetched).

Secondary outcome: `NV.IND.MANF.CD` (manufacturing value-added) — not present in WDI vintages (only `NV.IND.TOTL.KD` industrial total).

Tertiary outcome: OECD STAN energy-intensive sector output share — no OECD STAN parquet in `data/vintages/oecd/`.

The spec notes "v1 pre-registers; v1.1 runs when IEA + Eurostat energy-price series are added to baseline_pull.yaml and bootstrap." That has not happened yet.

## What would unblock

1. Fetch Eurostat NRG_PC_205 industrial electricity price series.
2. Build IEA industrial electricity price specialist fetcher.
3. Add `NV.IND.MANF.CD` to WDI bootstrap pull.

## Action

No replication.py written. The price-channel outcome cannot be measured with currently-fetched vintages.
