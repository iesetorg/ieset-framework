# Next Big Unlocks Database Audit

Date: 2026-05-19

## Executive Read

The database is no longer bottlenecked by obvious ready-but-unrun hypotheses.
Across the spec-complete corpus, every hypothesis already has a run directory.
The next unlock is therefore not "run the ready queue"; it is:

1. Convert the small verified decisive unmapped pool into scoreboard claims.
2. Backfill evidence packets for already-mapped decisive results so the public
   scoreboard is easier to verify.
3. Repair high-value partial/inconclusive results whose data gaps are clustered
   around a few publishers and aliases.

## Corpus Inventory

| item | count |
| --- | ---: |
| hypothesis specs audited by runnability script | 1,612 |
| run directories | 1,621 |
| diagnostics files | 1,621 |
| evidence packets | 371 |
| scoreboard position claims | 2,510 |

## Verdict Inventory

Across run diagnostics:

| verdict bucket | count |
| --- | ---: |
| partial | 822 |
| supported | 472 |
| refuted | 169 |
| inconclusive | 139 |
| other | 11 |
| missing | 8 |

Evidence types:

| evidence type | count |
| --- | ---: |
| associational | 870 |
| descriptive | 484 |
| causal | 159 |
| canonical multi-metric | 99 |
| unknown/no spec | 9 |

## Runnability

The runnability audit found:

| flag | count |
| --- | ---: |
| READY | 1,474 |
| NEEDS_DATA | 137 |
| NEEDS_TEMPLATE | 1 |
| LEGACY_SCHEMA | 0 |
| HAS_RUN | 1,612 |

Key implication: there are 0 ready-but-not-run candidates. The work is in
conversion, repair, and data expansion.

## Biggest Unlock 1: Evidence-Packet Backfill

This is the largest credibility unlock.

There are 209 mapped decisive results that already affect or can affect the
scoreboard but still have weak public provenance:

| weak provenance grade | mapped decisive count |
| --- | ---: |
| missing evidence packet | 190 |
| no input vintages recorded | 15 |
| packet with no grade | 4 |

High-leverage examples with many scoreboard links:

| hypothesis | verdict | evidence | covers | why it matters |
| --- | --- | --- | ---: | --- |
| `bukele_fiscal_trajectory_tax_cuts_imf_2019_2024` | refuted | causal | 17 | many-school fiscal/authoritarian-growth mapping |
| `eu_chemical_reach_regulation_firm_exit_effect` | supported | causal | 17 | regulation/compliance-cost evidence |
| `industrial_policy_developmentalist_states_growth` | supported | causal | 17 | central developmentalism benchmark |
| `lula_bolsa_familia_poverty_reduction_decomposition_2003_2010` | refuted | causal | 17 | welfare/poverty decomposition |
| `nordic_outcome_persistence_decomposition_v3` | refuted | causal | 17 | Nordic model interpretation |
| `strong_union_labour_law_youth_unemployment_south_europe` | refuted | causal | 17 | labour-market institutions |
| `labour_market_flexibility_unemployment_duration` | refuted | associational | 17 | labour-flexibility scoreboard cluster |
| `cuba_socialist_economy_stagnation_1960_2023` | supported | canonical | 17 | socialist case-study benchmark |
| `great_leap_forward_famine_output_collapse_1959_1961` | supported | canonical | 17 | Marxist-Leninist canonical validation |
| `north_south_korea_development_divergence_1953_present` | supported | canonical | 17 | system-divergence anchor |

Recommended next action: run an evidence-packet backfill wave on the top 30
mapped decisive results by `covers_claims` and evidence weight. This probably
does not change q-net much, but it massively upgrades verifiability.

## Biggest Unlock 2: Verified Decisive Unmapped Pool

There are 361 decisive results with no current school mapping. Most are low
provenance, broad/duplicate, or not really school-level claims yet.

Safe verified subset:

| pool | count | potential q if 2 links each |
| --- | ---: | ---: |
| all decisive unmapped | 361 | 224.5 |
| verified/partial-provenance safe unmapped | 12 | 11.0 |
| verified/partial-provenance safe non-broad | 12 | 11.0 |

Best immediate scoreboard candidates:

| hypothesis | verdict | evidence | grade | recommendation |
| --- | --- | --- | --- | --- |
| `abct_credit_boom_predicts_capital_misallocation_oecd` | supported | associational | reproducible_hash_verified | Map carefully to Austrian credit-cycle claims; likely one of the cleanest next links. |
| `austrian_monetary_expansion_asset_bubble_not_cpi_panel` | refuted | associational | reproducible_hash_verified | Direct Austrian asset-inflation prediction refutation; useful because it prevents one-sided pro-market drift. |
| `korea_post_chaebol_liberalisation_frontier_growth` | refuted | associational | partial_provenance | Map narrowly; likely refutes market-liberal post-chaebol liberalisation claim and can support developmentalist caveat. |
| `uae_freezone_institutional_quality_wgi_1996_2024` | supported | canonical | partial_provenance | Good institutional/free-zone case; useful for institutionalism, ordoliberalism, developmentalism, and classical liberalism if wording stays narrow. |
| `cuba_health_outcomes_vs_latam_peers` | supported | associational | partial_provenance | Real socialist-health positive evidence; should be mapped if we want the scoreboard to look honest and not merely adversarial. |
| `trade_lib_egypt_fta_cascade` | supported | descriptive | reproducible_hash_verified | Conditional trade-state-capacity result; map only after wording the instability caveat. |
| `trade_lib_colombia_us_fta_2012` | supported | descriptive | reproducible_hash_verified | Useful as a "pre-existing access limits FTA marginal effect" claim, not a simple pro-trade win. |
| `trade_lib_south_africa_sadc_trade` | supported | descriptive | reproducible_hash_verified | Useful as a regional-trade/no-aggregate-openness claim; not a broad free-trade score. |

Hold for now:

- `financial_fed_dot_plot_realised_path_2012_2024`
- `financial_fed_reverse_repo_facility_usage_2021_2024`

Both are verified but mostly operational central-bank facts, not strong school
predictions.

## Biggest Unlock 3: Partial Verdict Interpretation Queue

There are 620 partial unmapped results. Only 14 are currently safe-ish from a
provenance and duplicate-control standpoint.

Best partials to review next:

| hypothesis | evidence | grade | why it matters |
| --- | --- | --- | --- |
| `capital_gains_tax_cut_investment_response_panel` | associational | reproducible_hash_verified | Direct fiscal/tax policy lever; could graduate with split-out investment vs business-entry claims. |
| `trade_lib_china_wto_2001_manufacturing_export_surge` | causal | reproducible_hash_verified | Major trade/development case; needs synthetic-control interpretation guardrails. |
| `trade_lib_evfta_vietnam_eu_2020` | causal | reproducible_hash_verified | Newer trade-policy case; may be too short-window but valuable. |
| `austrian_savings_rate_investment_quality_link` | associational | reproducible_hash_verified | Direct Austrian mechanism; likely weak/partial, but important for balance. |
| `liberal_free_trade_partner_growth_panel_1990_2020` | associational | reproducible_hash_verified | Broad trade-growth claim; needs careful direction and effect-size review. |
| `property_rights_median_income_growth_1980_2024` | associational | reproducible_hash_verified | Institutional/property-rights mechanism, currently inconclusive direction. |

Recommended next action: do a partial-interpretation pass, not a direct mapping
pass. Split each into precise subclaims where the run actually supports or fails
one component.

## Biggest Unlock 4: Data Source Bridges

The 137 `NEEDS_DATA` specs are concentrated enough that data engineering will
unlock whole clusters.

Top missing data/publisher clusters:

| source family | blocked specs/mentions | likely unlock |
| --- | ---: | --- |
| OECD aliases and SDMX series | 33 specs; 111 run-missing mentions | fiscal, output-gap, labour, PMR, productivity, housing |
| BOJ / ECB / FRED monetary bridge | BOJ 17, ECB 12, FRED 7 specs | ZLB, Japan debt, fiscal multipliers, monetary history |
| Ilzetzki-Reinhart-Rogoff exchange-rate/fiscal data | 10 specs, 5 solo unlocks | gold standard, hyperinflation, Bretton Woods, central bank independence |
| trade stack: WITS + Comtrade + UNCTAD | 24 combined specs | trade liberalisation, FDI, industrial upgrading |
| WIPO / innovation data | 8 specs | patent, innovation, industrial-policy frontier claims |
| IEA / IRENA / energy stack | IEA 6, IRENA 5 specs | nuclear, renewables, Energiewende, China renewables |

Best first data bridge:

1. OECD alias bridge: `OutputGap`, `OECD.SDD.NAD`, `underlying_primary_balance`,
   `NAQ_GDP`, `NAQ_government_consumption`, `harmonised_unemployment`.
2. BOJ/ECB/FRED monetary bridge: unlocks Japan/ZLB/fiscal multiplier cluster.
3. Trade stack: WITS + UNCTAD + Comtrade for trade-development claims.

## Biggest Unlock 5: High-Value Repairs

There are 158 non-verdict or repair results. Many are not quick wins because
they depend on manual/constructed microdata, but the following are high-value if
we want diverse policy coverage:

| hypothesis | blocker shape | reason to prioritise |
| --- | --- | --- |
| `truss_2022_currency_user_ldi_collateral_mechanism` | many BOE/ICE/ECB inputs | fiscal credibility/currency-user case |
| `eu_ets_price_2022_2026_carbon_signal_strength` | ETS/ENTSO/E/OECD STAN | climate/industrial policy |
| `monetarist_fed_2008_great_recession_avoidable_with_constant_m_growth` | FRED macro series wiring | direct monetarist stress test |
| `second_generation_education_outcomes_by_origin` | PISA/microdata | immigration and integration policy |
| `decentralized_property_rights_agricultural_productivity` | FAO/PRINDEX/V-Dem | land/property-rights policy |
| `hayek_decentralised_governance_swiss_cantonal_growth` | Swiss FSO | decentralisation/federalism |
| `licensing_burden_income_mobility` | academic/BLS state data | regulation and mobility |
| `cbam_2026_implementation_carbon_leakage_test` | Comtrade/CBAM/Eurostat | trade-climate frontier |
| `ira_2022_clean_energy_investment_decomposition` | manual clean-energy capex + BLS/IRENA | industrial policy/green subsidy |
| `classical_zoning_relaxation_housing_supply_response_us_metros` | permits/rent/event coding | housing supply policy |

## Recommended Next Three Waves

### Wave 1: Scoreboard Conversion, Small And Clean

Map 5-7 verified direct candidates:

- `abct_credit_boom_predicts_capital_misallocation_oecd`
- `austrian_monetary_expansion_asset_bubble_not_cpi_panel`
- `korea_post_chaebol_liberalisation_frontier_growth`
- `uae_freezone_institutional_quality_wgi_1996_2024`
- `cuba_health_outcomes_vs_latam_peers`
- one conditional trade case after claim wording: Egypt, Colombia, or South Africa

Expected movement: modest q-net movement but high epistemic value because it adds
both pro-market and anti-market findings.

### Wave 2: Public Verification Backfill

Backfill evidence packets for the top 30 mapped decisive weak-provenance results.

Expected movement: little q-net movement, but large credibility movement. This is
the best "policy tool trust" lever.

### Wave 3: Data Bridge Sprint

Build or repair the OECD/BOJ/IRR/trade-stack bridges:

- OECD aliases and SDMX fetch mappings first.
- BOJ/ECB/FRED monetary bridge second.
- WITS/Comtrade/UNCTAD trade-development stack third.

Expected movement: unlocks the next 30-60 repairable or sharpenable hypotheses,
especially fiscal, monetary, trade, and energy clusters.

## Bottom Line

The next honest big lever is not another blind run swarm. The system has runs.
What it needs now is:

- a clean verified mapping wave,
- a proof/provenance wave,
- then a data bridge wave.

That is how we move from lots of verdicts to a policy-grade evidence engine.
