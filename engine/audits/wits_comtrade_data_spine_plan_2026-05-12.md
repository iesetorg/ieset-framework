# WITS / UN Comtrade Data Spine Plan - Group 2 / Agent B3

Date: 2026-05-12

Scope: inspect existing fetcher conventions and local trade-policy / trade-flow vintages, then define a reproducible WITS + UN Comtrade spine plan without fetching network data.

## Local Findings

- No ready `wits`, `world_bank_wits`, `un_comtrade`, or `comtrade` publisher is registered in `data/fetchers/publishers.yaml`.
- No local vintage directory matching WITS or Comtrade is present under `data/vintages/`.
- Existing trade-adjacent local vintages can support proxy tests, but they are not substitutes for a WITS/Comtrade spine:
  - WDI: `NE.TRD.GNFS.ZS`, `NE.EXP.GNFS.ZS`, `NE.IMP.GNFS.ZS`, `TX.VAL.*`, `TM.VAL.*`, `TM.TAX.MRCH.WM.AR.ZS`.
  - OWID: `trade-as-share-of-gdp`.
  - OECD PMR: `TARIFFS`, `BARRIER_TRADE`.
  - Heritage / Fraser: `trade_freedom`, `freedom_to_trade_internationally`.
  - FAOSTAT: detailed agricultural trade matrix and food-balance import-share vintages.
  - US Census: `trade_in_goods`, currently US-only and not a global Comtrade replacement.
- Existing fetcher contract is stable:
  - fetchers return `FetchResult`;
  - vintages are written by `write_vintage()` to `data/vintages/<publisher>/<series>@<fetch_utc>.parquet`;
  - `scripts/fetch.py` dispatches only publishers with `status: ready` and importable `fetcher_module`;
  - manifests record `publisher`, `series_id`, `source_url`, `methodology_url`, `license`, `fetch_utc`, `rows`, period bounds, SHA256, and extra fields.
- Existing large-source conventions favor staged discovery, explicit row-count controls, local manifest/audit records, and preservation of raw publisher dimensions rather than premature canonical flattening.

## Planning Verdict

The previous draft had the right direction but was too broad for the current repo state. The implementation should start as a metadata/discovery spine, not as a full data pull. Treat WITS tariff policy variables and Comtrade trade-flow outcomes as separate publishers, separate vintages, and separate derived panels. Do not wire any hypothesis runner to this spine until discovery confirms coverage, rate limits, row scale, and schema stability.

## Publisher Plan

### `world_bank_wits`

Purpose: tariffs, TRAINS policy measures, and WITS-derived trade indicators where available.

Initial status: add as `pending` until a metadata smoke probe succeeds in an online pass.

Fetcher shape:

- Module: `data/fetchers/world_bank_wits.py`.
- Public entry point: `fetch(series_id, *, vintage_utc=None, reporters=None, partners=None, products=None, years=None, indicator=None, nomenclature=None, max_rows=None)`.
- Discovery entry point: either `fetch("metadata")` or a script under `scripts/discover_wits_comtrade_support_2026_05_12.py` that does not write data vintages.
- Publisher id should stay `world_bank_wits`; do not overload `world_bank_wdi`.

First supported series ids:

- `tariff_metadata`
- `tariff_hs2_mfn_applied`
- `tariff_hs2_preferential`
- `tariff_hs6_curated_mfn_applied`
- `trains_ntm_metadata`

### `un_comtrade`

Purpose: reporter-partner-product annual goods trade flows and derived mechanism panels.

Initial status: add as `pending` until an authenticated or public metadata smoke probe succeeds in an online pass.

Fetcher shape:

- Module: `data/fetchers/un_comtrade.py`.
- Public entry point: `fetch(series_id, *, vintage_utc=None, reporters=None, partners=None, products=None, years=None, flow=None, classification="HS", frequency="A", max_rows=None)`.
- Do not fetch all reporters, all partners, all HS6 products in one call.
- Preserve Comtrade-native fields before deriving country-year or sector-year panels.

First supported series ids:

- `metadata`
- `annual_hs2_goods_trade`
- `annual_hs4_goods_trade_curated`
- `annual_hs6_product_families`
- `mirror_flow_diagnostics`

## Row Contracts

### Raw Tariff Vintage

Minimum columns:

- `reporter_iso3`
- `partner_iso3` or `partner_group`
- `year`
- `product_code`
- `product_level`
- `classification`
- `classification_revision`
- `indicator_id`
- `tariff_type`
- `value`
- `unit`
- `raw_reporter`
- `raw_partner`
- `raw_product`
- `quality_flags`

`FetchResult.extra` should include query parameters, coverage counts, classification revision, source table/dataflow id, and whether the payload is discovery-only.

### Raw Trade-Flow Vintage

Minimum columns:

- `reporter_iso3`
- `partner_iso3`
- `year`
- `flow`
- `product_code`
- `product_level`
- `classification`
- `classification_revision`
- `trade_value_usd`
- `quantity`
- `quantity_unit`
- `netweight_kg`
- `raw_reporter`
- `raw_partner`
- `raw_product`
- `quality_flags`

Keep re-import / re-export flags if Comtrade exposes them. Preserve missing or aggregate partner rows rather than dropping them silently.

### Canonical Derived Panel

Derived outputs should be separate vintages or generated artifacts, not mixed into raw pulls. Minimum columns:

- `country_iso3`
- `partner_iso3` when bilateral
- `sector_code` or `product_code`
- `year`
- `variable_id`
- `value`
- `unit`
- `source_publishers`
- `source_vintage_paths`
- `source_query_hash`
- `recipe_id`
- `quality_flags`

## Staged Implementation

1. Local-only discovery helper.
   - Scan `publishers.yaml`, `data/vintages/`, hypotheses, and manifests for WITS/Comtrade references.
   - Emit an audit JSON/MD under `engine/audits/`, not a data vintage.
   - This can be implemented and tested without network.

2. Metadata smoke pass.
   - With network available later, probe publisher metadata only: reporter coverage, year bounds, product classifications, tariff indicators, flow types, and rate-limit constraints.
   - Record exact URLs, status codes, response schemas, and failure modes.
   - Keep publishers `pending` unless a tiny data smoke pull writes a valid manifest.

3. Small data smoke vintages.
   - WITS: one reporter, HS2, one short year range, MFN applied tariff.
   - Comtrade: one reporter, one or two partners, HS2, annual imports and exports, one short year range.
   - Use `max_rows` or explicit product/year filters as a hard safety valve.

4. Curated cross-country pull.
   - WITS: HS2 all available reporters, 1990-2024, MFN applied and preferential tariffs where available.
   - Comtrade: annual HS2 or HS4 reporter-partner goods trade for active hypothesis countries.
   - Write one manifest per staged run.

5. Product-family HS6 pull.
   - Restrict to hypothesis-needed families: agriculture/food, textiles/apparel, steel/metals, autos, electronics, energy products, semiconductors/machine tools.
   - Require a row-count estimate before each pull.

6. Derived panel promotion.
   - Promote derived panels only after raw vintage coverage and mirror-flow diagnostics pass.
   - Store recipes separately from raw fetchers so runner logic can audit lineage.

## Derived Variables To Build First

Priority 1:

- `mfn_applied_tariff_simple_avg_hs2`
- `preferential_tariff_simple_avg_hs2`
- `tariff_gap_preferential_minus_mfn`
- `import_value_by_reporter_partner_hs2`
- `export_value_by_reporter_partner_hs2`
- `trade_partner_concentration_hhi`

Priority 2:

- `tariff_weighted_by_import_share`
- `import_penetration_by_sector`
- `revealed_comparative_advantage`
- `export_concentration_hhi`
- `high_tech_export_share_comtrade`
- `energy_import_dependence_comtrade`

Priority 3:

- `bilateral_tariff_exposure`
- `china_import_shock_exposure`
- `sanctions_trade_reorientation`
- `intermediate_imports_productivity_spillover`
- `capital_goods_import_growth`

## Quality Gates

- No full-universe Comtrade HS6 pull before row-count estimates and local storage checks.
- No tariff variable should be silently joined to trade-flow outcomes without year, reporter, partner, product, and classification lineage.
- No WDI/OWID/Heritage/Fraser proxy should be renamed as WITS or Comtrade evidence.
- Every raw vintage must preserve native product classification and revision.
- Every derived panel must record recipe id, source vintage path(s), query parameters or hash, and quality flags.
- Mirror-flow diagnostics must flag reporter/partner disagreement, missing partner coverage, aggregate partner rows, and unit/value implausibility.
- Nomenclature breaks must be explicit; HS revision concordance should be a separate transformation step.
- Hypothesis manifests should prefer `world_bank_wits:` for policy-treatment variables and `un_comtrade:` for trade-flow outcomes once these publishers graduate.

## First 30 Hypotheses Unlocked

Tariff liberalisation:

1. `wits_mfn_tariff_liberalisation_growth_panel_1990_2024`
2. `wits_weighted_tariff_cut_import_growth_panel`
3. `wits_tariff_cut_productivity_compounder_panel`
4. `wits_unilateral_tariff_cut_consumption_welfare_proxy`
5. `wits_tariff_dispersion_resource_misallocation_panel`
6. `wits_trade_tax_dependence_fiscal_capacity_tradeoff`
7. `wits_bound_vs_applied_tariff_credibility_investment`
8. `wits_preferential_tariff_access_export_growth_panel`
9. `wits_tariff_reversal_inflation_pass_through_panel`
10. `wits_tariff_liberalisation_low_income_convergence_panel`

Import competition:

11. `comtrade_import_penetration_manufacturing_productivity_panel`
12. `comtrade_china_import_shock_sectoral_employment_panel`
13. `comtrade_import_competition_consumer_price_disinflation`
14. `comtrade_import_competition_firm_exit_reallocation`
15. `comtrade_import_exposure_regional_unemployment_panel`
16. `comtrade_import_substitution_growth_drag_panel`
17. `comtrade_intermediate_imports_productivity_spillover`
18. `comtrade_capital_goods_imports_tfp_growth_panel`
19. `comtrade_energy_import_dependence_inflation_volatility`
20. `comtrade_food_import_dependence_food_security_risk`

Export discipline and diversification:

21. `comtrade_export_concentration_growth_volatility_panel`
22. `comtrade_export_diversification_income_convergence_panel`
23. `comtrade_hightech_export_share_frontier_growth_panel`
24. `comtrade_rca_upgrading_developmentalist_success_panel`
25. `comtrade_export_discipline_import_substitution_comparison`
26. `comtrade_trade_partner_diversification_resilience_panel`
27. `comtrade_global_value_chain_entry_growth_panel`
28. `comtrade_sanctions_trade_reorientation_growth_cost`
29. `comtrade_resource_export_dependence_governance_trap`
30. `comtrade_export_complexity_private_investment_panel`

## Next Local-Only Step

Create `scripts/discover_wits_comtrade_support_2026_05_12.py` in a later implementation pass. It should not fetch network data by default. It should report:

- whether WITS/Comtrade publishers are registered;
- local vintages and manifests matching WITS/Comtrade/trade/tariff keywords;
- hypotheses already referencing WITS, Comtrade, tariff, RCA, import exposure, export concentration, or HS products;
- existing proxy vintages that can validate future derived panels;
- recommended first smoke queries and row-count limits.

Suggested verification command once created:

```bash
python3 scripts/discover_wits_comtrade_support_2026_05_12.py --ref-limit 20
```

## Online Commands For A Future Pass

These are placeholders, not commands run in this audit:

```bash
python3 scripts/fetch.py world_bank_wits tariff_hs2_mfn_applied --countries CHL --start 2000 --end 2005
python3 scripts/fetch.py un_comtrade annual_hs2_goods_trade --countries CHL --start 2000 --end 2005
```

The actual CLI may need extra `--partners`, `--products`, `--flow`, or fetcher-specific flags; add those only after the fetcher contract is implemented.

## Handoff Summary

This spine is high leverage, but it should graduate in three gates: local discovery, metadata smoke, then tiny data smoke. Until then, continue using current WDI/OWID/OECD PMR/Heritage/Fraser/FAOSTAT/US Census vintages as clearly labelled proxies or validation sources, not as WITS/Comtrade evidence.
