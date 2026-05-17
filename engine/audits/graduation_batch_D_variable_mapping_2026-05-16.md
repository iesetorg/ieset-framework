# Graduation Batch D Variable Mapping Repair - 2026-05-16

Scope: 19 current treatment/variable mapping candidates. I used the current
`engine/runs/*/diagnostics.json` artifacts, the candidate YAML specs, and the
source/vintage resolution helpers in `scripts/run_panel_fe.py`. No hypothesis
YAML, runner, or run artifact was edited.

## Runner Mapping Notes

`scripts/run_panel_fe.py` now resolves source tokens through:

- `data/fetchers/publishers.yaml` publisher aliases.
- `SERIES_ALIAS_BY_PUBLISHER`, including `oecd:EPL_OV`, `oecd:DSD_PDB`,
  `oecd:OutputGap`, `oecd_pmr:pmr_composite`, and several Fraser/BIS aliases.
- `SOURCE_BRIDGES`, including stale OECD PDB URNs to `oecd:DSD_PDB`.
- `latest_vintage()`, which supports exact, nested, and fuzzy local parquet
  lookup.
- `construct_variable_from_text()`, which can build simple country/year binary
  indicators and weighted sums only when component source tokens are loadable.

Important limitation: `load_variable()` skips `constructed`, `derived`, `manual`,
and `academic` source publishers. Local `data/vintages/derived/*.parquet` files
therefore need either a specific bridge in `construct_variable_from_text()` or a
careful loader change before a YAML can point at them.

## Headline

Ready-to-patch now: 3 low-risk candidates.

Estimated graduation yield if the ready subset is patched and rerun: 2-3 real
verdicts. A fourth is plausible if the Malaysia treatment proxy is explicitly
approved as a design decision, but I do not count it as ready because it changes
the treatment from an index to a country-event proxy.

Most of Batch D is true missing data, not source-token drift. The major blockers
are antitrust enforcement/WIPO data, BIT stocks, WITS tariff histories,
firm/sector concentration panels, SOE and state-credit shares, occupational
licensing indexes, and subnational or HS-code treatment units that the generic
country-year runners cannot represent.

## Ready To Patch

| Candidate | Current blocker | Minimal repair | Patch later | Rerun command | Expected result |
| --- | --- | --- | --- | --- | --- |
| `minimum_wage_youth_unemployment_tradeoff` | Treatment uses vague `constructed:` statutory-minimum-wage text; local minimum-wage bite vintages exist under `data/vintages/derived/`. `oecd:EPL_OV` is now aliasable to an existing OECD EPL vintage. | Add a narrow bridge from the statutory-minimum-wage/median-earnings constructed phrase to `derived:minimum_wage_bite_ratio_subnational_panel` or permit that specific derived vintage to load. Leave WDI/ILOSTAT outcomes as-is; do not require the missing youth-share control for primary identification. | `scripts/run_panel_fe.py` | `python3 scripts/run_panel_fe.py minimum_wage_youth_unemployment_tradeoff --force` | Medium-high; likely graduates unless overlap/listwise deletion collapses after the treatment loads. |
| `startup_density_frontier_prosperity` | OECD high-growth-firm and VC treatments absent, but the YAML note already allows a WDI business-density proxy and `world_bank_wdi:IC.BUS.NREG` is local. | Add a YAML fallback for `startup_density` to `world_bank_wdi:IC.BUS.NREG`; leave VC and industrial-policy spending as secondary/missing. `oecd_pmr:pmr_composite` already resolves to local `oecd_pmr:PMR`. | `hypotheses/regulatory/startup_density_frontier_prosperity.yaml` | `python3 scripts/run_panel_fe.py startup_density_frontier_prosperity --force` | Medium; should at least leave preflight and produce a verdict if country/year overlap is sufficient. |
| `fiat_expansion_erodes_currency_purchasing_power_long_run` | Panel FE requires a treatment, but this is a descriptive long-run index claim. Outcomes mostly have local fallbacks: BIS EER, BIS/Shiller real estate, FRED PPI, IMF PCPS. | Convert estimator template from `panel_fe` to `descriptive`, and add/bridge `imf:primary_commodity_prices` to `imf_pcps:PALLFNF` for the commodity-basket fallback. | `hypotheses/monetary/fiat_expansion_erodes_currency_purchasing_power_long_run.yaml` and optionally `scripts/run_panel_fe.py` for the IMF PCPS bridge | `python3 scripts/run_descriptive.py fiat_expansion_erodes_currency_purchasing_power_long_run --force` | Medium; likely graduates as a descriptive verdict, but the generic descriptive runner summarizes first country versus donor median, so inspect result-card semantics before scoreboard use. |

## Needs Design Decision, Not Just Mapping

| Candidate | Current blocker | Minimal repair | Patch later | Rerun command | Why not ready |
| --- | --- | --- | --- | --- | --- |
| `malaysia_developmentalist_plateau_1990_2024` | GLC/Bumiputera constructed treatments absent. `oecd_pmr:pmr` loads but is not the Malaysia-specific national-champion treatment and has weak sample coverage. | If approved, replace the primary treatment with an explicit `constructed: indicator = 1 for MYS from 1990 onward` proxy and fix the commodity export control from `TX.VAL.MMTL.ZS.WT` to local WDI `TX.VAL.MMTL.ZS.UN`. | `hypotheses/growth/malaysia_developmentalist_plateau_1990_2024.yaml` | `python3 scripts/run_panel_fe.py malaysia_developmentalist_plateau_1990_2024 --force` | This would test a Malaysia post-1990 event proxy, not a measured GLC/Bumiputera protection index. |
| `industrial_concentration_labour_share_link` | Local OECD PDB now resolves, but the real CR4/HHI treatments are `derived:bea_compustat_industry_cr4` and `derived:bea_compustat_industry_hhi`, which are absent. | Move `intangible_investment_share` out of treatment into controls if rerunning later; fetch/build actual CR4/HHI before claiming the concentration estimand. | `hypotheses/labour/industrial_concentration_labour_share_link.yaml` after concentration data exists | `python3 scripts/run_panel_fe.py industrial_concentration_labour_share_link --force` | PDB is an already-existing vintage, but using it as treatment would grade the wrong estimand. |
| `zlb_state_dependent_multiplier_pk_framing` | Some local aliases exist for GDP, rates, output gap, CAPB, and expectations. The actual treatment still needs government-consumption shocks, narrative shocks, and an LP-IV/state interaction. | Add `oecd:NAQ_government_consumption` bridge to local OECD national-accounts government consumption only as a partial repair; do not rerun as a clean graduation without narrative shocks and an LP-IV runner/design. | `scripts/run_panel_fe.py` for the source bridge; likely a new LP-IV runner or bespoke replication later | `python3 scripts/run_panel_fe.py zlb_state_dependent_multiplier_pk_framing --force` for preflight only | Existing local vintages reduce one gap, but the core treatment and estimator are still missing. |

## True Missing Data Or Unit Support

| Candidate | Current blocker | Minimal repair | Patch later | Rerun command | Status |
| --- | --- | --- | --- | --- | --- |
| `bilateral_investment_treaty_fdi_panel` | Outcomes/controls load, but cumulative BIT count/log BIT-stock treatments are absent. | Add UNCTAD IIA Navigator country-year BIT stock vintage, then point both treatments at that vintage. | `hypotheses/trade/bilateral_investment_treaty_fdi_panel.yaml` after data acquisition | `python3 scripts/run_panel_fe.py bilateral_investment_treaty_fdi_panel --force` | True missing data. |
| `colonial_institutions_post_independence_growth` | AJR settler-vs-extractive institutional coding absent. | Add a manual country coding sidecar or publisher-backed colonial-institution vintage; then map treatment to it. | `hypotheses/growth/colonial_institutions_post_independence_growth.yaml` after manual data exists | `python3 scripts/run_panel_fe.py colonial_institutions_post_independence_growth --force` | True missing manual coding. |
| `competition_policy_enforcement_innovation` | PWT and controls load, but antitrust enforcement, merger cases, cartel fines, WIPO citations, and patent-quality components are absent. | Fetch/build antitrust enforcement and patent-quality vintages; only then wire weighted-sum treatment. | `hypotheses/regulatory/competition_policy_enforcement_innovation.yaml` plus future data fetcher files | `python3 scripts/run_panel_fe.py competition_policy_enforcement_innovation --force` | True missing data. |
| `demo_migration_inflows_wages_skill_split` | UN DESA migrant stock and OECD earnings load, but high-skill migrant share from OECD DIOC is absent. | Fetch/bridge OECD DIOC high-skill migrant-share vintage; do not collapse to total migrant share because the falsification rule is skill-split. | `hypotheses/labour/demo_migration_inflows_wages_skill_split.yaml` after OECD DIOC data exists | `python3 scripts/run_panel_fe.py demo_migration_inflows_wages_skill_split --force` | True missing data for the discriminating treatment. |
| `free_community_college_enrolment_completion` | ACS education sources load as USA-level rows, but the treatment is TN/OR state-cohort; generic country-year construction cannot represent state units. | Build IPEDS/ACS state-year outcomes and state-cohort treatment, or add subnational unit support to the DiD runner. | `scripts/run_did_callaway_santanna.py` and `hypotheses/fiscal/free_community_college_enrolment_completion.yaml` after state panel exists | `python3 scripts/run_did_callaway_santanna.py free_community_college_enrolment_completion --force` | True subnational unit/data gap. |
| `industrial_policy_without_exit_discipline_failure` | Episode codings for with/without exit discipline are absent. | Add manual industrial-policy episode coding with sunset/export-performance flags. | `hypotheses/growth/industrial_policy_without_exit_discipline_failure.yaml` after manual sidecar exists | `python3 scripts/run_panel_fe.py industrial_policy_without_exit_discipline_failure --force` | True missing manual coding. |
| `national_champions_long_run_productivity_drag` | PWT and trade controls load, but sector CR3, state-aid intensity, sector VA share, and OECD STAN R&D are absent or not mapped. | Build country-sector concentration/state-aid panel; local STAN is not enough without champion/concentration coding. | `hypotheses/growth/national_champions_long_run_productivity_drag.yaml` after sector data exists | `python3 scripts/run_panel_fe.py national_champions_long_run_productivity_drag --force` | True missing sector data. |
| `occupational_licensing_productivity_drag` | Some BLS/FRED state-ish proxies load, but the Carpenter-Knepper licensing index is absent and `derived:` is skipped by the loader. | Add licensing-index vintage and either a precise derived-loader bridge or publisher mapping; also verify state-unit handling before grading. | `scripts/run_panel_fe.py` and `hypotheses/distribution/occupational_licensing_productivity_drag.yaml` after index exists | `python3 scripts/run_panel_fe.py occupational_licensing_productivity_drag --force` | True missing index plus subnational unit risk. |
| `state_credit_allocation_zombie_firm_persistence` | PWT/WGI/WDI controls load; zombie-firm share and state-owned/development-bank credit share are absent. | Fetch/build zombie firm and state-credit-share panels. BIS credit aggregates are not the same treatment. | `hypotheses/growth/state_credit_allocation_zombie_firm_persistence.yaml` after data exists | `python3 scripts/run_panel_fe.py state_credit_allocation_zombie_firm_persistence --force` | True missing firm/credit data. |
| `state_owned_enterprise_share_growth_plateau` | PWT/Maddison/WDI controls load; SOE employment/value-added share is absent. | Add SOE share vintage, ideally country-year and source-documented. | `hypotheses/growth/state_owned_enterprise_share_growth_plateau.yaml` after SOE data exists | `python3 scripts/run_panel_fe.py state_owned_enterprise_share_growth_plateau --force` | True missing SOE data. |
| `tariff_protection_duration_growth_drag` | WDI outcomes/controls load; WITS tariff level and cumulative duration are absent. Local `wits:export_product_hhi_wits` is product concentration, not tariff protection. | Fetch weighted mean applied tariff, then derive cumulative years above 15 percent. OECD PMR `TARIFFS` can be a robustness proxy, not the primary WITS treatment. | `hypotheses/trade/tariff_protection_duration_growth_drag.yaml` after WITS tariff data exists | `python3 scripts/run_panel_fe.py tariff_protection_duration_growth_drag --force` | True missing tariff data. |
| `trump_tariff_manufacturing_reshoring_effect` | WDI/BLS/Census/FRED country-time data load, but treatment is tariffed HS-code by time; generic DiD currently has no HS-code unit. Import price index is also absent. | Build HS-code/product-year tariff treatment and outcome panel, then add unit support or a bespoke tariff DiD replication. | `scripts/run_did_callaway_santanna.py` or a run-local replication plus `hypotheses/trade/trump_tariff_manufacturing_reshoring_effect.yaml` | `python3 scripts/run_did_callaway_santanna.py trump_tariff_manufacturing_reshoring_effect --force` | True HS-unit/data gap. |
| `welfare_transfer_stockton_seed_guaranteed_income_2019` | BLS LFP proxy loads, but this is an individual-level SEED RCT claim. OECD health-stat alias does not provide the anxiety outcome. | Use published SEED micro/summary treatment-control data or make this a descriptive/manual replication; do not use national BLS LFP as treatment. | `hypotheses/welfare_architecture/welfare_transfer_stockton_seed_guaranteed_income_2019.yaml` or a bespoke run-local replication after SEED data exists | `python3 scripts/run_local_projections.py welfare_transfer_stockton_seed_guaranteed_income_2019 --force` | True missing micro/RCT data. |

## Patch Order

1. Patch the 3 ready candidates first: minimum wage, startup density, fiat descriptive.
2. If a design owner approves a Malaysia post-1990 proxy, patch it as a separate, explicitly documented treatment-proxy conversion.
3. Do not rerun `industrial_concentration_labour_share_link` just because OECD PDB now resolves; it needs CR4/HHI first.
4. Push the remaining candidates to data-pack lanes: BIT/UNCTAD, WITS tariffs, WIPO/antitrust, sector concentration/state aid, SOE/state credit/zombie firms, occupational licensing, and subnational/HS-unit panels.
