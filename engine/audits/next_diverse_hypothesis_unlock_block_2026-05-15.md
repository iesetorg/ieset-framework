# Next Diverse Hypothesis Unlock Block - 2026-05-15

## Scope

This pass focused on the next high-leverage block after minimum wage: energy learning curves plus OECD productivity and industrial-structure evidence. The aim was not just to add one more verdict, but to find the next data vein that can support more varied hypothesis families.

## Graduated This Pass

### `solar_lcoe_2010_2024_learning_curve_continuation`

- Status moved from `INCONCLUSIVE_DATA_PENDING` to `partial`.
- Added a dedicated replication because the landed IRENA LCOE workbook is a global technology series, not a country panel.
- Result:
  - 2010-2019 solar PV learning rate per doubling: 38.8%.
  - 2010-2024 learning rate per doubling: 36.8%.
  - Full-period slope retained 93.5% of the pre-2020 slope.
  - Solar LCOE fell from $68.64/MWh in 2019 to $42.62/MWh in 2024.
  - Post-2020 flattening interaction is significant, so the strict preregistration is only partial.

### `onshore_wind_lcoe_2010_2024_learning_curve_continuation`

- New candidate hypothesis, steelman, replication, diagnostics, and result card created.
- Result:
  - 2010-2019 onshore-wind learning rate per doubling: 36.4%.
  - 2010-2024 learning rate per doubling: 41.7%.
  - Full-period slope retained 119.5% of the pre-2020 slope.
  - Onshore-wind LCOE fell from $48.89/MWh in 2019 to $34.06/MWh in 2024.
  - Post-2020 flattening interaction is not significant.
- Verdict: `supported`.

## Infrastructure Repair

- Patched `scripts/run_panel_fe.py` so future generic runs resolve:
  - `irena:lcoe_solar_pv`
  - `irena:lcoe_wind_onshore`
  - `irena:wind_onshore_lcoe`
  - `irena:solar_pv_costs`
- Added `World` -> `GLOBAL` normalization for global technology series.

## Block Triage

| Block | Local state | Verdict potential | Next action |
| --- | --- | --- | --- |
| IRENA solar LCOE | Global cost and capacity present | 1 graduated now | Use as template for renewables follow-through tests |
| IRENA wind LCOE | Global cost and capacity present | 1 new supported result now | Add scoreboard mapping after coverage review |
| China renewables learning | Global LCOE present, country-specific LCOE/manufacturing share absent | Not enough for China-vs-OECD causal claim | Fetch/construct China module production share and country/cohort cost proxies before verdict conversion |
| OECD PDB productivity | Large landed panel: 1.7M+ rows | Already supports a multi-hypothesis vein | Convert strongest existing PDB cards into scoreboard mappings, then generate next 20 productivity hypotheses |
| Nuclear phaseout | OWID/eurostat proxies present; primary reliability/price outcomes incomplete | Not yet rigorous | Need ENTSO-E/IEA reliability, wholesale price, and capacity-factor sources |
| Industrial concentration | OECD PDB/STAN useful but concentration treatment remains weak | Blocked for concentration claim | Need BEA/Compustat/ORBIS or OECD industry concentration proxy before rerun |

## Already Productive OECD PDB Candidates

Existing local OECD PDB result cards show this is the strongest next hypothesis factory:

- `oecd_pdb_gdp_hour_frontier_convergence_1950_2025` - supported.
- `oecd_pdb_small_open_economy_frontier_convergence` - supported.
- `oecd_pdb_capital_deepening_without_tfp_limit` - supported.
- `oecd_pdb_post_2008_productivity_hysteresis_panel` - supported.
- `oecd_pdb_hours_reduction_output_tradeoff_panel` - supported.
- `oecd_pdb_market_reform_productivity_compounder` - refuted_or_weak.
- `oecd_pdb_public_sector_share_productivity_drag` - refuted_or_weak.
- `oecd_pdb_tfp_growth_frontier_persistence_1970_2025` - refuted_or_weak.

## Scoreboard Mapping Completed

Mapped only the OECD PDB results with direct mechanism matches, using new reciprocal position claims where older claims already pointed to another hypothesis:

- `oecd_pdb_capital_deepening_without_tfp_limit`
  - `classical_liberal#179`
  - `empirical_pragmatist#149`
- `oecd_pdb_market_reform_productivity_compounder`
  - `classical_liberal#180`
  - `institutionalism#140`
  - `ordoliberal#159`
  - `chicago_monetarism#137`
- `oecd_pdb_public_sector_share_productivity_drag`
  - `austrian#140`
  - `chicago_monetarism#138`
  - `classical_liberal#181`
  - `ordoliberal#160`
- `oecd_pdb_hours_reduction_output_tradeoff_panel`
  - `social_democratic#149`

Deliberately not mapped in this pass:

- `solar_lcoe_2010_2024_learning_curve_continuation` and `onshore_wind_lcoe_2010_2024_learning_curve_continuation`: these prove global cost-learning trajectories, not the stronger China-causal industrial-policy claims.
- `oecd_pdb_gdp_hour_frontier_convergence_1950_2025` and `oecd_pdb_small_open_economy_frontier_convergence`: useful evidence, but no existing school claim was specific enough without creating broader beta-convergence claims.
- `oecd_pdb_post_2008_productivity_hysteresis_panel` and `oecd_pdb_tfp_growth_frontier_persistence_1970_2025`: informative macro/productivity facts, but not yet mapped to a clear school prediction.

## Recommended Next Batch

1. Build 20 OECD PDB follow-ons around productivity convergence, MFP persistence, capital deepening, average hours, sectoral public-share drag, and post-2008 hysteresis.
2. Add coverage mappings for the solar and wind learning-curve cards after checking which schools have explicit clean-energy cost trajectory claims.
3. Fetch or construct China renewables manufacturing share before trying to score the stronger China industrial-policy claim.
4. Keep nuclear out of scoreboard conversion until real reliability and wholesale-price outcomes land.

## Validation

- `python3 -m py_compile scripts/run_panel_fe.py engine/runs/solar_lcoe_2010_2024_learning_curve_continuation/replication.py engine/runs/onshore_wind_lcoe_2010_2024_learning_curve_continuation/replication.py` passed.
- `python3 scripts/validate_scope_alignment.py` passed with 2442 pass, 0 errors.
- `python3 scripts/validate_link_reciprocity.py --summary` passed with 2452 position-side links, 2452 hypothesis-side coverages, 0 errors, 0 warnings after reciprocal mapping.
- `python3 scripts/validate_specs.py` still fails on pre-existing backlog/schema debt; no new failure was traced to this pass.
