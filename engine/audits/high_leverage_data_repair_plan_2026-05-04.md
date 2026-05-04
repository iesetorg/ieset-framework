# High-Leverage Data Repair Plan

Generated: 2026-05-04

Purpose: keep the path to 200 tested hypotheses per school methodological. This file records the highest-impact remaining linked blockers after the replication-wrapper backfill, OWID/IRENA source repairs, and minimum-wage integrity gates.

## Current Queue Shape

- Public hidden hypotheses: 191.
- School-linked hidden hypotheses: 54.
- School-linked hidden claims blocked: 157.
- Tested range at target-200 audit: 122-147.
- Largest repair reason: `needs_successful_rerun`.
- Scoreboard movement from this wave: intentionally none, except one weak/proxy-prone minimum-wage path was neutralized back to inconclusive.

## Top Data Bundles

### Intergenerational Mobility Cross-Country

- Linked claims blocked: 17.
- Current state: one true mobility outcome now fetched: `owid:intergenerational-earnings-elasticity`.
- Binding missing series:
  - `oecd:OECD.EDU.IMEP_DSD_EAG_FIN_DF_FIN_RESOURCES_1.0`
  - `oecd:OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0`
- Non-binding robustness gap:
  - `owid:share-of-children-in-the-bottom-quintile-who-make-it-to-the-top-quintile`
- Integrity note: direct OECD SDMX calls from this environment are currently Cloudflare-challenged/403. Do not substitute WDI GDP, poverty, or Gini for mobility or institutional-channel data.
- Next action: obtain the OECD Education-at-a-Glance subnational spending dispersion and OECD Affordable Housing income-segregation vintages, then implement the bespoke partial-R2 plus leave-one-out regression branch.

### Minimum-Wage State/Subnational Cluster

- Linked claims blocked: 17 for `minimum_wage_above_median_employment_teen_effects`; 9 for `minimum_wage_disemployment_at_high_bite_ratios`; 1 for `federal_minimum_wage_employment_meta`.
- Current state: integrity gates now reject national FRED and single-state exemplar proxies. Official USDOL state minimum-wage history is now fetched as `usdol:state_minimum_wage_history` (2,106 jurisdiction-year rows, 1968-2024).
- Required source bundle:
  - `bls:LAU_state_teen_employment_population_ratio_panel`
  - `usdol:state_minimum_wage_history` (landed)
  - `bls:OEWS_state_p10_hourly_wage_panel`
  - `bls:OES_state_median_hourly_wage_panel`
  - `bls:QCEW_state_total_employment_panel`
  - `bls:QCEW_county_NAICS722_employment_panel`
  - `derived:minimum_wage_bite_ratio_subnational_panel`
- Integrity note: the runner must preserve `unit_id` or state/county keys. Collapsing to `USA, year` would destroy the design.
- Next action: add USDOL publisher registration plus BLS LAU/OEWS/QCEW panel builders, then rerun only after state/unit counts and binding-change diagnostics pass.

### Nuclear Phaseout Grid Reliability

- Linked claims blocked: 17.
- Current state: treatment-side nuclear/renewables capacity/share data now load; primary outcomes remain data-gated.
- Missing primary outcomes:
  - IEA industrial electricity prices.
  - ENTSO-E day-ahead wholesale price volatility.
  - LOLE/adequacy metrics.
  - Fossil backup capacity factor.
- Integrity note: Eurostat `nrg_pc_205` is useful as an audit/cross-check but currently cannot satisfy the preregistered cohort/period by itself.
- Next action: manual-drop IEA industrial prices, implement ENTSO-E fetcher behind `ENTSOE_API_KEY`, then rerun bespoke replication.

### Wealth Tax Capital Flight Revenue Yield Gap

- Linked claims blocked: 17.
- Current state: run remains `INCONCLUSIVE_DATA_PENDING` because France is not in the panel.
- Required source bundle:
  - France ISF/IFI realized revenue and official forecasts.
  - Norway 2022 wealth-tax hike realized revenue and emigration/outflow measures.
  - Colombia 2022-2023 patrimonio tax revenue/forecast.
  - Spain grandes fortunas realized/forecast panel.
- Integrity note: do not score with only Norway or single-country revenue data; the preregistered chain is a multi-case realized-vs-forecast and mobility/outflow design.
- Next action: build a hand-curated public-finance panel with source URLs and forecast-vintage metadata.

### China Renewables Industrial Policy Learning Curve

- Linked claims blocked: 7.
- Current state: IRENA capacity data are present; LCOE outcomes are missing.
- Missing primary outcomes:
  - `irena:lcoe_solar_pv`
  - `irena:lcoe_wind_onshore`
- Integrity note: official IRENA snippets confirm the existence of LCOE data and report-level facts, but snippets are not a vintage. Use the official `Download data` workbook/manual drop or a first-class parser.
- Next action: obtain the official IRENA Renewable Power Generation Costs data companion, fetch LCOE vintages, then add a dedicated learning-curve replication rather than relying on generic descriptive summaries.

### Taiwan TSMC Industrial Policy

- Linked claims blocked: 7.
- Current state: missing semiconductor-industry outcome data.
- Required source bundle:
  - TSMC/global foundry share, preferably Gartner/TrendForce/IC Insights with permissible citation or manual vintage.
  - Taiwan semiconductor value-added/export capability series.
- Integrity note: avoid scoring on broad high-tech exports alone; the claim is semiconductor/foundry dominance.

### Fossil Subsidy Persistence

- Linked claims blocked: 4.
- Current state: missing subsidy and reserve-ownership outcomes.
- Required source bundle:
  - `imf:imf_energy_subsidies`
  - `iea:fossil_subsidies_estimate`
  - `academic:rystad_global_reserves_ownership`
- Integrity note: consumer fuel-price proxies are not enough to test persistence of subsidy regimes or private reserve ownership.

### Austerity And ZLB Multipliers

- Linked claims blocked: 3 plus several single-school blockers.
- Current state: bespoke diagnostics correctly refuse OLS-only identification.
- Required source bundle:
  - April-2010 WEO forecast vintage / Blanchard-Leigh instrument data.
  - Quarterly OECD national accounts panel.
  - Ramey-Zubairy or Guajardo-Leigh-Pescatori narrative fiscal shock series.
- Integrity note: OLS signs are explicitly biased by reverse causality in this design; keep neutral until IV/LP-IV data land.

## Operational Order

1. Fetch/manual-drop source bundles that unlock 17-claim blockers without changing specs: intergenerational OECD channels, minimum-wage subnational panels, nuclear IEA/ENTSO-E, wealth-tax realized-vs-forecast panel.
2. Add data loaders/fetchers that preserve the estimand unit: state/county `unit_id`, forecast vintage, cohort, or technology.
3. Only then implement or run bespoke replications that match the preregistered falsification rule.
4. Refresh `plan_public_visibility_repair_queue.py`, `plan_school_tested_equalization.py`, and `audit_scoreboard_outcomes.py` after each batch.
