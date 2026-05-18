# Energy/Climate Swarm B2 - 2026-05-18

Worker B lane: climate/energy hypotheses and run artifacts only. Scoreboard,
positions, data fetch manifests, and daily rate-limited backfill artifacts were
not edited.

## Artifacts Produced

1. `engine/runs/green_transition_cost_trajectory_electricity_prices/replication.py`
   - Replaced stale generic panel wrapper with an exact local Eurostat/WDI diagnostic.
2. `engine/runs/green_transition_cost_trajectory_electricity_prices/diagnostics.json`
   - New PARTIAL verdict with pinned metrics.
3. `engine/runs/green_transition_cost_trajectory_electricity_prices/result_card.md`
   - Human-readable local diagnostic result card.
4. `engine/runs/green_transition_cost_trajectory_electricity_prices/manifest.yaml`
   - Exact Eurostat and WDI vintage files plus SHA-256 hashes.
5. `engine/runs/green_transition_cost_trajectory_electricity_prices/BLOCKED.md`
   - Updated blocker: full IEA/OECD-STAN test still blocked; local price diagnostic revived.
6. `engine/runs/eu_green_deal_vs_ets_emissions_mechanism/replication.py`
   - Exact blocker/provenance wrapper for EEA-dependent event study.
7. `engine/runs/eu_green_deal_vs_ets_emissions_mechanism/manifest.yaml`
   - Pins local EEA bootstrap-stub vintages and unblock path.
8. `engine/runs/eu_ets_price_2022_2026_carbon_signal_strength/replication.py`
   - Exact blocker/provenance wrapper for ETS price-signal test.
9. `engine/runs/eu_ets_price_2022_2026_carbon_signal_strength/manifest.yaml`
   - Pins local ETS bootstrap-stub vintage and missing EUA/TTF requirements.
10. `engine/audits/energy_climate_swarm_B2_2026-05-18.md`
   - This audit.

## Verdicts

| hypothesis | verdict | basis |
|---|---:|---|
| `green_transition_cost_trajectory_electricity_prices` | PARTIAL | Eurostat industrial electricity price gap is clear, but WDI real manufacturing VA does not show predicted high-transition output underperformance. |
| `eu_green_deal_vs_ets_emissions_mechanism` | INCONCLUSIVE_DATA_PENDING | Local EEA greenhouse-gas inventory and EU ETS verified-emissions vintages are bootstrap stubs with zero non-null outcomes. |
| `eu_ets_price_2022_2026_carbon_signal_strength` | INCONCLUSIVE_DATA_PENDING | Local EU ETS verified-emissions vintage is a bootstrap stub; EUA and TTF price vintages are absent. |
| `china_renewables_industrial_policy_learning_curve` | unchanged existing INCONCLUSIVE_DATA_PENDING | Existing wrapper/manifest already revive the world-aggregate IRENA learning curve and correctly leave the CHN-vs-OECD mechanism blocked. |

## Key Green-Transition Metrics

- High-transition group: BE, DE, NL.
- Measured-transition group: ES, FR, IT, NO, SE.
- Eurostat industrial price band: `MWH2000-19999`, EUR/kWh including taxes.
- Average high-transition price gap, 2015-2023: 28.7%.
- High-transition price gap in 2023: 49.4%.
- Year-FE high-transition log price coefficient: 0.269, clustered p=0.139.
- Post-2021 high-transition interaction: 0.008, clustered p=0.951.
- WDI real manufacturing VA change, 2019-2023: high-transition +4.7%; measured-transition +2.1%.

## Commands Run

- `python3 - <<'PY' ... py_compile.compile(..., cfile='/private/tmp/...')`
- `python3 engine/runs/green_transition_cost_trajectory_electricity_prices/replication.py`
- `python3 engine/runs/eu_green_deal_vs_ets_emissions_mechanism/replication.py`
- `python3 engine/runs/eu_ets_price_2022_2026_carbon_signal_strength/replication.py`

All three wrappers completed successfully. Parquet reads emitted sandbox CPU-info
warnings from Arrow (`sysctlbyname failed`), but no wrapper failed.

## Blockers

- EEA `greenhouse_gas_inventory` and `eu_ets_verified_emissions` vintages are bootstrap stubs only.
- EUA allowance price and TTF gas price vintages are not present locally.
- Full green-transition price/output claim still needs IEA industrial prices for USA/JPN/KOR and OECD STAN sector output.
- UK post-2020 industrial price coverage is incomplete in the current Eurostat local vintage.

## Churn To Restore / Ignore

Unowned dirty files are present outside this lane and were not edited by B2:

- `web/app/scoreboard/page.tsx`
- `data/manifests/fetch_run_2026-05-17T231721Z.yaml`
- `data/manifests/fetch_run_2026-05-17T231736Z.yaml`
- `engine/audits/daily_rate_limited_data_backfill_2026-05-17T231721Z.*`
- `engine/audits/daily_rate_limited_data_backfill_2026-05-17T231736Z.*`
- Multiple non-energy/non-climate run dirs currently dirty, including consumer-choice, export-complexity, financialisation, household-debt, private-credit, QE, and market-order artifacts.
- `engine/audits/financial_fragility_swarm_C2_2026-05-18.md`
