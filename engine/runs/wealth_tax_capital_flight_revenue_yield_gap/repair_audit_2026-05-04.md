# Repair audit - wealth_tax_capital_flight_revenue_yield_gap

Date: 2026-05-04

## Finding

`scripts/run_synth_did.py` reports `FRA not in panel` because the first loadable outcome is not a four-country wealth-tax outcome panel. It is the `wealth_tax_revenue_realised_to_forecast` source chain, but only `ssb:skatteinntekter (NOR)` resolves locally, yielding two NOR observations after the sample filter. The preregistered France leg, `minefi:recettes_fiscales (FRA)`, has no local vintage, so the treated country never appears in the outcome panel.

## Local vintage coverage checked

- `minefi:recettes_fiscales`, `minefi:tax_residency_changes`, and `minefi:ISF/IFI_base`: no `data/vintages/minefi` materialization; publisher is registered as `pending` / fetcher TBD.
- `dian:estadisticas_tributarias` and `dian:patrimonio_declarado`: no `data/vintages/dian` materialization; publisher is registered as `pending` / fetcher TBD.
- `aeat:recaudacion` and `aeat:patrimonio_declarado`: no `data/vintages/aeat` materialization; publisher is registered as `pending` / fetcher TBD.
- `henley_private_clients_millionaire_report` and `icij:offshore_leaks_derivatives`: no local materialized HNW migration/offshore-leaks panel; `icij` is registered as `pending` / fetcher TBD.
- `banrep:GDP (COL)`: no local `banrep` materialization, so the Colombia control source does not fill from the preregistered national source.
- Local broad proxies such as WDI/OWID contain `FRA`, `NOR`, `COL`, and `ESP`, and WID stores France as `FR`, but these are not the preregistered wealth-tax revenue/yield or HNW migration variables needed for this causal-chain test.

## Runner panel state

Filtered sample: 1990-2024, countries `FRA`, `NOR`, `COL`, `ESP`.

- `wealth_tax_revenue_realised_to_forecast`: `NOR` only, 2015-2016, 2 rows.
- `high_net_worth_emigration_count`: no filtered sample rows; the loaded SSB vintage is outside 1990-2024.
- `reported_taxable_wealth_base`: `NOR` only, 1999-2024, 26 rows.
- `wealth_tax_introduction_or_hike_event`: constructed for all four countries, 1990-2024.
- `real_gdp_growth`: `FRA`, `ESP`, `NOR`; `COL` missing from the preregistered `banrep` leg.

## Verdict

No rerun was performed after this audit. A successful rerun would require honest preregistered outcome coverage for France plus at least two donor countries on the same wealth-tax outcome family. The available local WDI/OWID/WID proxies are insufficient for the registered yield-gap/emigration falsification rule.
