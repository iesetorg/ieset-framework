# Resource Developmentalism Treatment Audit - 2026-05-16

Worker lane: Treatment coding. Write scope limited to this audit and the companion CSV inventory.

## Inputs Read

- Plan anchor: `engine/agent_briefs/resource_developmentalism_hardening_swarm_plan_2026-05-16.md`
- Queue freeze: `engine/audits/resource_developmentalism_queue_freeze_2026-05-16.md`
- Builder: `scripts/build_movement_vintages.py`
- Movement YAML source: `movements/*.yaml`
- Treatment vintages: `data/vintages/movements/resource_developmentalism@2026-05-16T084233Z.parquet` and `data/vintages/movements/resource_developmentalism_alignment@2026-05-16T084233Z.parquet`
- Resource-rent vintage used by builder: `data/vintages/world_bank_wdi/NY.GDP.TOTL.RT.ZS@2026-04-30T115056Z.parquet`

## Construction Summary

`resource_developmentalism` is not a hand-coded treatment. The builder first creates dense annual country panels for every movement position. It then takes the canonical `developmentalism` series, clips negative values to zero, and keeps positive values only in resource-rent years.

Resource-rent years are defined as annual WDI total natural-resource rents at or above 5 percent of GDP. If a country-year has no annual rent value, the builder falls back to a country flag: mean WDI total rents over 1970-2020 at or above 5 percent of GDP. Every other country-year is zero-filled.

The dense panel therefore mixes three meanings of zero: no active movement, active non-developmentalist movement, and uncoded/missing movement coverage. That is not a valid market-open resource peer indicator.

## Inventory Coverage

The companion CSV contains 128 movement-country rows. These rows cover all 941 positive country-years in the movement vintage, across 44 countries from 1956 to 2026. Because overlapping umbrella and sub-episode movements can contribute to the same country-year, the row-level treated-observation sum is 1221, larger than the unique positive country-year count.

Within the hypothesis window, the vintage has 772 positive country-years across 41 countries during 1970-2020. In the WGI-constrained result-card window approximation, 1996-2018, it has 345 positive country-years across 28 countries before outcome/control missingness.

## Largest Treated Countries

- KWT: 66 obs, 1961-2026, mean value 0.50
- ARE: 56 obs, 1971-2026, mean value 1.00
- PNG: 52 obs, 1975-2026, mean value 0.50
- IRN: 51 obs, 1976-2026, mean value 1.00
- IDN: 40 obs, 1966-2026, mean value 0.95
- MYS: 40 obs, 1976-2026, mean value 0.95
- NGA: 39 obs, 1976-2023, mean value 0.56
- VEN: 39 obs, 1974-2026, mean value 0.94
- SAU: 38 obs, 1975-2026, mean value 0.88
- ETH: 36 obs, 1991-2026, mean value 0.89
- COD: 33 obs, 1965-1997, mean value 0.50
- RUS: 32 obs, 1991-2026, mean value 0.77

## Largest Movement Windows

- KWT kuwait_oil_welfare_state_1961_present: 66 obs, 1961-2026, alignment 0.5, risks: partial developmentalism alignment; 16/66 treated years use resource-country fallback; long umbrella window; resource doctrine explicit
- ARE uae_emirate_state_capitalism_1971_present: 56 obs, 1971-2026, alignment 1, risks: 9/56 treated years use resource-country fallback; long umbrella window; resource doctrine explicit
- PNG papua_new_guinea_independence_resource_state_1975_present: 52 obs, 1975-2026, alignment 0.5, risks: partial developmentalism alignment; 5/52 treated years use resource-country fallback; long umbrella window; resource doctrine explicit
- IRN iran_revolution_islamic_economy_1979_present: 48 obs, 1979-2026, alignment 0.5, risks: partial developmentalism alignment; 7/48 treated years use resource-country fallback; long umbrella window; resource doctrine explicit
- COD zaire_mobutu_mpr_1965_1997: 33 obs, 1965-1997, alignment 0.5, risks: partial developmentalism alignment; 5/33 treated years use resource-country fallback; long umbrella window; resource doctrine explicit
- IDN indonesia_suharto_new_order_1965_1998: 30 obs, 1966-1969;1973-1998, alignment 1, risks: 4/30 treated years use resource-country fallback; long umbrella window; resource doctrine explicit
- SYR syria_baath_assad_statist_regime_1963_2000: 30 obs, 1963-1969;1974-1985;1988-1997;2000, alignment 0.5, risks: partial developmentalism alignment; 7/30 treated years use resource-country fallback; long umbrella window; resource link mainly WDI-threshold driven
- VNM vietnam_doi_moi_1986: 30 obs, 1989-1997;1999-2014;2022-2026, alignment 1, risks: 5/30 treated years use resource-country fallback; long umbrella window; resource link mainly WDI-threshold driven
- ETH ethiopia_eprdf_developmental_state_1991_2018: 28 obs, 1991-2018, alignment 1, risks: long umbrella window; resource link mainly WDI-threshold driven
- KAZ kazakhstan_nazarbayev_resource_state_1991_2019: 28 obs, 1991-1997;1999-2019, alignment 0.5, risks: partial developmentalism alignment; long umbrella window; resource doctrine explicit
- TUN tunisia_bourguiba_state_modernisation_1956_1987: 28 obs, 1956-1969;1974-1987, alignment 1, risks: 14/28 treated years use resource-country fallback; long umbrella window; resource link mainly WDI-threshold driven
- VEN venezuela_chavismo_bolivarian_1999_present: 28 obs, 1999-2026, alignment 1, risks: mechanical/derived alignment; 12/28 treated years use resource-country fallback; long umbrella window; resource doctrine explicit
- MMR mmr_burmese_way_to_socialism_1962: 27 obs, 1962-1988, alignment 0.5, risks: partial developmentalism alignment; 8/27 treated years use resource-country fallback; long umbrella window; resource link mainly WDI-threshold driven
- RWA rwanda_post_genocide_reconstruction_1994_2020: 24 obs, 1994-2017, alignment 1, risks: long umbrella window; resource link mainly WDI-threshold driven
- MYS malaysia_mahathir_bumiputera_development_1981_2003: 23 obs, 1981-2003, alignment 1, risks: resource link mainly WDI-threshold driven

## Risk Counts

- Mechanical or derived developmentalism labels touch 209 of 941 positive country-years (22.2%).
- Partial developmentalism labels touch 514 positive country-years (54.6%).
- Long umbrella movements of 25 or more active years touch 550 positive country-years (58.4%).
- Resource-country fallback, used where annual rent values are missing but 1970-2020 country mean rents exceed 5 percent of GDP, accounts for 198 positive country-years (21.0%).
- Movement doctrines with explicit resource/rent/oil/mineral wording touch 562 positive country-years (59.7%); WDI-threshold-only resource linkage touches 412 (43.8%).

## High-Risk Inclusion Audit

- CHN: 28 unique treated country-years. Main rows: deng_xiaoping_reforms_1978 (1978-1992;2005-2008;2010-2011, 1); china_hu_era_2002_2012 (2005-2008;2010-2011, 1); china_wto_accession_2001 (2005-2008;2010-2011, 1); china_xi_era_2012_present (2022-2026, 1). Flags: umbrella timing, resource link not always doctrinal.
- ETH: 36 unique treated country-years. Main rows: ethiopia_eprdf_developmental_state_1991_2018 (1991-2018, 1); ethiopia_abiy_prosperity_2018_present (2018-2026, 0.5); ethiopia_meles_late_era_2005_2012 (2005-2012, 1); ethiopia_hailemariam_eprdf_2012_2018 (2012-2018, 1). Flags: umbrella timing, resource link not always doctrinal.
- RWA: 27 unique treated country-years. Main rows: rwanda_post_genocide_reconstruction_1994_2020 (1994-2017, 1); rwanda_kagame_fourth_term_2024_present (2024-2026, 1). Flags: umbrella timing, resource link not always doctrinal.
- PNG: 52 unique treated country-years. Main rows: papua_new_guinea_independence_resource_state_1975_present (1975-2026, 0.5). Flags: umbrella timing.
- ARE: 56 unique treated country-years. Main rows: uae_emirate_state_capitalism_1971_present (1971-2026, 1); uae_zayed_consolidation_1976_1990 (1976-1990, 1); uae_zayed_oil_price_collapse_response_1985_1995 (1985-1995, 0.5); uae_khalifa_early_era_2004_2014 (2004-2014, 1). Flags: umbrella timing, mechanical labels.
- SAU: 38 unique treated country-years. Main rows: saudi_abdullah_late_era_2005_2015 (2005-2015, 0.5); saudi_vision_2030_2016_present (2016-2026, 1); saudi_abdullah_de_facto_crown_prince_1995_2005 (1996-2005, 1); saudi_mbs_cp_era_2017_present (2017-2026, 1). Flags: mechanical labels, resource link not always doctrinal.
- KWT: 66 unique treated country-years. Main rows: kuwait_oil_welfare_state_1961_present (1961-2026, 0.5). Flags: umbrella timing.
- IRN: 51 unique treated country-years. Main rows: iran_revolution_islamic_economy_1979_present (1979-2026, 0.5); iran_khomeini_revolutionary_consolidation_1979_1989 (1979-1989, 1); iran_rafsanjani_pragmatist_1989_1997 (1989-1997, 1); iran_khatami_reformist_1997_2005 (1997-2005, 0.5). Flags: umbrella timing, mechanical labels, resource link not always doctrinal.
- VEN: 39 unique treated country-years. Main rows: venezuela_chavismo_bolivarian_1999_present (1999-2026, 1); venezuela_perez_first_term_1974_1979 (1974-1979, 1); venezuela_herrera_copei_1979_1984 (1979-1984, 0.5). Flags: umbrella timing, mechanical labels.
- NGA: 39 unique treated country-years. Main rows: nigeria_obasanjo_pdp_civilian_1999_2007 (1999-2007, 0.5); nigeria_babangida_military_1985_1993 (1986-1993, 0.5); nigeria_buhari_apc_civilian_2015_2023 (2017-2023, 0.5); nigeria_abacha_military_1993_1998 (1993-1998, 0.5). Flags: mechanical labels, resource link not always doctrinal.
- DZA: 17 unique treated country-years. Main rows: algeria_fln_socialist_developmental_state_1962_1978 (1962-1978, 1). Flags: resource link not always doctrinal.
- AGO: 17 unique treated country-years. Main rows: angola_mpla_socialist_oil_state_1975_1991 (1975-1991, 0.5). Flags: none.
- IRQ: 12 unique treated country-years. Main rows: iraq_baath_oil_statism_1968_1979 (1968-1979, 1). Flags: none.
- SYR: 30 unique treated country-years. Main rows: syria_baath_assad_statist_regime_1963_2000 (1963-1969;1974-1985;1988-1997;2000, 0.5). Flags: umbrella timing, resource link not always doctrinal.
- COD: 33 unique treated country-years. Main rows: zaire_mobutu_mpr_1965_1997 (1965-1997, 0.5). Flags: umbrella timing.

## Coding Risks

1. Unknowns are currently controls. The dense movement panel writes uncoded/no-active-alignment years as zero, so the generic FE model treats unknown or unreviewed country-years as untreated peers.
2. The resource filter is too mechanical. WDI total rents at or above 5 percent can classify China, Ethiopia, Rwanda, Tunisia, Syria, Myanmar, Vietnam, and Cote d'Ivoire as resource-developmentalist even when the movement doctrine is not resource-funded.
3. The country-level rent fallback is large enough to matter. It contributes 198 unique positive country-years, often pre-1970 or post-2021, and extends ongoing movements to 2026 despite annual rent data ending in 2021.
4. Long umbrella movements dominate. Kuwait 1961-present, UAE 1971-present, PNG 1975-present, Iran 1979-present, Zaire/COD 1965-1997, Syria 1963-2000, Vietnam Doi Moi, Ethiopia EPRDF, and Venezuela Chavismo are broad regime windows rather than policy episodes.
5. Overlapping umbrella and episode movements are clipped after summing. This hides whether a country-year is treated because of one carefully coded episode or several duplicated regime descriptors.
6. More than 20 percent of positive country-years are touched by mechanical/derived developmentalism labels, and more than half by partial developmentalism labels. This triggers the lane stop rule unless those labels are reviewed before modeling.
7. The current treatment does not distinguish `resource_statist_socialist`, `resource_developmentalist`, `market_open_resource_peer`, `rule_bound_resource_manager`, `resource_nationalisation_shock`, `mixed`, and `uncoded`. Norway, Botswana-like rule-bound managers, Gulf rentier diversification states, socialist oil states, and market-open resource peers should not share one scalar treatment.

## Recommended Recoding Before Estimation

- Add an explicit treatment subtype field rather than deriving resource developmentalism solely from `developmentalism` plus WDI rents.
- Split long regimes into dated resource-policy episodes where possible: nationalisations, sovereign-wealth-rule adoption, industrial-plan waves, subsidy/credit booms, and liberalisation episodes.
- Preserve an `uncoded` state in the movement vintage and exclude or separately model it; do not zero-fill it into the control group.
- Require doctrinal or policy evidence of resource-funded state direction for the main treatment. Keep WDI-rent-only cases as candidate exposure, not final treatment.
- Use market-open and rule-bound resource managers as explicit comparison categories, not as the residual zero category.

## Bottom Line

The current vintage is useful as a screening proxy, but it is too noisy for the hardened claim. It should not be treated as scoreboard-safe until the treatment is manually subtyped, unknowns are separated from controls, and long umbrella windows are replaced or supplemented by episode timing.
