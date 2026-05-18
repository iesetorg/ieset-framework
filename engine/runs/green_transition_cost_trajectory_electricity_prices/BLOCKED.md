# BLOCKED — green_transition_cost_trajectory_electricity_prices

**Status:** Full pre-registration still blocked; local Eurostat price diagnostic revived.

## What is now available

- `data/vintages/eurostat/nrg_pc_205@2026-05-12T135519Z.parquet` now provides industrial electricity prices.
- `data/vintages/world_bank_wdi/NV.IND.MANF.KD@2026-04-30T140100Z.parquet` provides real manufacturing value added.
- `replication.py` now runs a narrow exact European diagnostic for DE/BE/NL versus FR/IT/ES/SE/NO.

## Still blocked for the full claim

- IEA industrial electricity price comparators for USA, JPN, and KOR are still absent.
- OECD STAN energy-intensive sector output shares are still absent.
- UK post-2020 industrial price coverage is incomplete in the local Eurostat vintage.
- The local diagnostic does not identify a clean causal transition-policy effect net of COVID and the 2022 gas shock.

## What would unblock

1. Build or populate an IEA industrial electricity price fetcher/manual vintage for non-European comparators.
2. Add OECD STAN sector-level manufacturing output/value-added for chemicals, metals, cement, and paper.
3. Add a pre-registered war/COVID robustness window or instrument if a causal claim is required.

## Action

Use the current result card as a partial local diagnostic only. Do not present it as the full IEA/OECD-STAN price-and-relocation test.
