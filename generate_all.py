#!/usr/bin/env python3
import os

GROWTH_DIR = "./hypotheses/growth"
STEELMAN_DIR = "./hypotheses/steelman"

os.makedirs(GROWTH_DIR, exist_ok=True)
os.makedirs(STEELMAN_DIR, exist_ok=True)

def write_yaml(hid, content):
    path = os.path.join(GROWTH_DIR, f"{hid}.yaml")
    if os.path.exists(path):
        print(f"SKIP (exists): {path}")
        return
    with open(path, "w") as f:
        f.write(content)
    print(f"Wrote YAML: {path}")

def write_steelman(hid, content):
    path = os.path.join(STEELMAN_DIR, f"{hid}.md")
    if os.path.exists(path):
        print(f"SKIP (exists): {path}")
        return
    with open(path, "w") as f:
        f.write(content)
    print(f"Wrote steelman: {path}")

# ============================================================
# Track A: 1-10
# ============================================================

# 1
write_yaml("frontier_income_persistence_market_institutions_1960_2024", """# yaml-language-server: $schema=../../schemas/hypothesis.schema.json
hypothesis_id: frontier_income_persistence_market_institutions_1960_2024
version: 1
status: candidate
topic: growth
claim: Countries in the top quartile of market-institution scores in 1960 retain high-income frontier status through 2024 more often than countries with high state-directed-credit intensity but weaker property-rights scores.
evidence_type: associational
sample:
  countries:
    - USA
    - GBR
    - DEU
    - FRA
    - NLD
    - BEL
    - CHE
    - AUT
    - AUS
    - CAN
    - DNK
    - SWE
    - NOR
    - FIN
    - JPN
    - KOR
    - TWN
    - SGP
    - HKG
    - NZL
    - ARG
    - BRA
    - MEX
    - URY
    - CHL
    - PHL
    - THA
    - TUR
    - GRC
    - IND
    - PAK
  period: [1960, 2024]
  temporal_structure: panel
variables:
  outcome:
    - name: frontier_status_dummy
      source: world_bank_wdi:NY.GDP.PCAP.KD
      transformation: indicator_top_25pct_of_oecd_plus_at_t
      notes: High-income frontier status defined as real GDP per capita in top quartile of OECD+high-income Asian distribution in each year.
    - name: real_gdp_per_capita
      source: world_bank_wdi:NY.GDP.PCAP.KD
      transformation: log
  treatment:
    - name: property_rights_score_1960
      source: fraser_efw:legal_system_property_rights
      transformation: level_at_1960
      notes: Fraser legal-system and property-rights sub-index at 1960; available from 1970 earliest, so 1970 used as proxy for 1960 when necessary.
    - name: state_directed_credit_intensity
      source: constructed:credit_to_soe_share
      transformation: level
      notes: Credit allocation to state-owned enterprises or directed credit as share of total domestic credit; constructed from historical central-bank and IMF sources.
  controls:
    - name: initial_gdp_per_capita_1960
      source: maddison:real_gdp_pc
      transformation: log_level_at_1960
    - name: initial_human_capital
      source: owid:mean-years-of-schooling-long-run-1870
      transformation: level_at_1960
    - name: trade_openness
      source: world_bank_wdi:NE.TRD.GNFS.ZS
      transformation: level
    - name: polity_score
      source: polity5:polity2
      transformation: level
estimator:
  template: panel_fe
  fixed_effects: [country, year]
  clustering: country
  notes: Panel FE logit or linear probability model for frontier retention, with property-rights and state-credit intensity as key regressors. Pre-treatment institutional score at 1960 used to mitigate reverse causation.
falsification:
  rule: The hypothesis is refuted if the coefficient on 1960 property-rights score in a frontier-retention regression is not positive and significant at p<0.10, or if countries with high state-directed-credit but weak property rights retain frontier status at rates statistically indistinguishable from or higher than the market-institution group.
  test: panel_fe_frontier_retention_lpm
  threshold:
    property_rights_coef: ">0 and p<0.10"
    state_credit_coef: "<=0 or p>=0.10"
prior_confidence: 0.6
disclosure: Author holds priors favouring market institutions but acknowledges that East Asian developmentalist cases (Korea, Taiwan) succeeded with significant state direction; this may bias downward attribution of success to property rights alone.
steelman: hypotheses/steelman/frontier_income_persistence_market_institutions_1960_2024.md
scope:
  period: [1960, 2024]
  countries:
    - USA
    - GBR
    - DEU
    - FRA
    - NLD
    - BEL
    - CHE
    - AUT
    - AUS
    - CAN
    - DNK
    - SWE
    - NOR
    - FIN
    - JPN
    - KOR
    - TWN
    - SGP
    - HKG
    - NZL
    - ARG
    - BRA
    - MEX
    - URY
    - CHL
    - PHL
    - THA
    - TUR
    - GRC
    - IND
    - PAK
  outcome_dim:
    - gdp_growth
    - institutional_quality
  policy_family:
    - institutional_reform
    - regulation
    - industrial_policy
notes: Fraser EFW legal-system index starts in 1970; 1960 value is interpolated or proxied by earliest available. State-directed credit data requires historical central-bank series not yet in standard fetchers.
""")

write_steelman("frontier_income_persistence_market_institutions_1960_2024", """# Steelman — Frontier Income Persistence and Market Institutions (1960–2024)

## Strongest version of the claim
Countries that established strong market-supporting institutions — particularly secure property rights, impartial contract enforcement, and limited arbitrary state expropriation — before 1960 were more likely to remain in the high-income frontier through 2024 than countries that relied on state-directed credit allocation without comparable institutional foundations. The effect is conditional on initial income and human capital but persists after controlling for geography and trade openness.

## Key evidence the claim would need
1. A robust cross-country panel showing that pre-1960 property-rights proxies predict continued frontier status over six decades, with state-directed-credit intensity adding no independent predictive power.
2. Decomposition showing that the mechanism runs through sustained TFP growth and investment quality rather than transient capital deepening.
3. Case evidence from long-run high-income persistencers (Switzerland, Netherlands, Australia) versus failed developmentalist attempts (Argentina, Uruguay pre-1970s) that initial institutional stock conditioned later policy efficacy.

## Best counterarguments
- **Reverse causation:** High-income countries may have the fiscal and administrative capacity to build good property-rights institutions; the arrow may run from income to institutions rather than the reverse (Acemoglu-Johnson-Robinson vs. Glaeser et al. critique).
- **Survivorship bias:** We observe the countries that retained frontier status; those with strong 1960 institutions that later failed are not in the sample because the institution measure itself is post-hoc constructed.
- **State capacity confound:** East Asian cases with strong state-directed credit also built competent bureaucracies; the relevant dimension may be state capacity rather than market-vs-state orientation.
- **Measurement fragility:** Fraser property-rights indices begin in 1970; 1960 values are back-casted or interpolated, introducing measurement error that may bias coefficients toward zero.

## Boundary conditions
- Claim applies most clearly to the pre-1960 institutional stock; post-1980 institutional reform episodes (e.g., Eastern Europe post-1990) are a different treatment regime.
- Expectation is weaker for resource-rich economies where rents can substitute for institutional quality in sustaining high income temporarily.
- The claim is about persistence, not catch-up: low-income countries with weak institutions may still grow rapidly via capital deepening or commodity booms.

## Relation to existing hypotheses
Tensions with `industrial_policy_developmentalist_states_growth` (East Asian success with state direction) and `developmentalist_growth_premium_low_income_only` (state direction may work at low income). Aligns with `economic_freedom_index_income_correlation` and `rule_of_law_institutional_growth` if those are promoted to pre-registered.
""")

# 2
write_yaml("catch_up_growth_fades_after_middle_income_threshold", """# yaml-language-server: $schema=../../schemas/hypothesis.schema.json
hypothesis_id: catch_up_growth_fades_after_middle_income_threshold
version: 1
status: candidate
topic: growth
claim: Developmentalist catch-up economies show faster growth before reaching 40 percent of US GDP per capita, but their growth premium shrinks or reverses after crossing that threshold.
evidence_type: causal
sample:
  countries:
    - KOR
    - TWN
    - SGP
    - CHN
    - MYS
    - THA
    - IDN
    - PHL
    - VNM
    - IND
    - BRA
    - MEX
    - CHL
    - ARG
    - TUR
    - POL
    - HUN
    - CZE
  period: [1960, 2024]
  temporal_structure: panel
variables:
  outcome:
    - name: real_gdp_per_capita_growth
      source: world_bank_wdi:NY.GDP.MKTP.KD.ZG
      transformation: level
    - name: real_gdp_per_capita
      source: world_bank_wdi:NY.GDP.PCAP.KD
      transformation: log
  treatment:
    - name: developmentalist_policy_dummy
      source: constructed:binary_indicator
      transformation: binary
      notes: Coded 1 for KOR 1961-1997, TWN 1958-2000, SGP 1965-present, CHN 1978-present, MYS 1971-1996, based on Amsden-Wade-Chang coding.
    - name: middle_income_threshold_dummy
      source: constructed:indicator
      transformation: binary
      notes: Indicator = 1 when country-year real GDP per capita exceeds 40% of US level in same year.
  controls:
    - name: log_initial_gdp_pc
      source: world_bank_wdi:NY.GDP.PCAP.KD
      transformation: log
    - name: human_capital
      source: owid:mean-years-of-schooling-long-run-1870
      transformation: level
    - name: trade_openness
      source: world_bank_wdi:NE.TRD.GNFS.ZS
      transformation: level
    - name: institutional_quality
      source: wgi:RL.EST
      transformation: level
estimator:
  template: panel_fe
  fixed_effects: [country, year]
  clustering: country
  notes: Panel FE with interaction between developmentalist dummy and post-threshold dummy. Tests whether the developmentalist growth premium is larger below the 40% threshold than above it.
falsification:
  rule: The hypothesis is refuted if the interaction coefficient (developmentalist x post-threshold) is not negative and significant at p<0.10, or if the developmentalist growth premium is equal or larger above the threshold than below it.
  test: panel_fe_interaction_threshold
  threshold:
    interaction_coef: "<0 and p<0.10"
    pre_threshold_premium: ">0 and significant"
prior_confidence: 0.55
disclosure: Author is aware of the middle-income trap literature and may overstate the threshold effect; the 40% threshold is arbitrary and should be tested with 30% and 50% robustness.
steelman: hypotheses/steelman/catch_up_growth_fades_after_middle_income_threshold.md
scope:
  period: [1960, 2024]
  countries:
    - KOR
    - TWN
    - SGP
    - CHN
    - MYS
    - THA
    - IDN
    - PHL
    - VNM
    - IND
    - BRA
    - MEX
    - CHL
    - ARG
    - TUR
    - POL
    - HUN
    - CZE
  outcome_dim:
    - gdp_growth
  policy_family:
    - industrial_policy
    - trade_policy
notes: 40% threshold is measured in constant USD from WDI; robustness to PPP-based thresholds and to 30%/50% alternatives is planned.
""")

write_steelman("catch_up_growth_fades_after_middle_income_threshold", """# Steelman — Catch-Up Growth Fades After Middle-Income Threshold

## Strongest version of the claim
Developmentalist policy packages — selective credit, sector targeting, export subsidies, and SOE-led investment — accelerate convergence when an economy is far from the technological frontier, but their marginal efficacy declines once a country reaches about 40% of US GDP per capita. Beyond that point, the binding constraints shift from mobilising capital and labour into modern sectors to sustaining TFP growth through innovation, competitive markets, and institutional adaptation, where state-directed models face greater coordination challenges.

## Key evidence the claim would need
1. A clear structural break in the developmentalist growth premium at or near the 40% threshold, robust to threshold-variation (30-50%).
2. Post-threshold slowdown concentrated in TFP growth rather than capital deepening, consistent with the innovation-boundary story.
3. Cross-country evidence that economies which maintained strong growth above the threshold (e.g., Korea post-1997, Taiwan) had accompanying market-liberalising reforms, while plateau cases (Malaysia, Thailand) did not.

## Best counterarguments
- **Threshold arbitrariness:** The 40% level is not theoretically derived; it may capture a statistical artefact of sample composition rather than a true economic discontinuity.
- **Policy-switch confound:** Countries that slowed after the threshold may have simply maintained the same policies too long rather than the policies inherently losing efficacy; a well-timed policy switch could sustain growth.
- **Measurement noise:** PPP vs market-exchange-rate GDP per capita gives very different threshold crossings; the result may flip with accounting convention.
- **Survivorship in post-threshold sample:** Few countries have reached high income; small-N above the threshold means low statistical power to detect a continuing premium.

## Boundary conditions
- Claim is about the *marginal* efficacy of a given policy package, not an absolute ceiling on growth.
- Expectation is strongest for state-directed catch-up models; market-liberal catch-up may face different threshold dynamics.
- Threshold may vary by sectoral composition (manufacturing-led vs resource-led catch-up).

## Relation to existing hypotheses
Directly tensions with `industrial_policy_developmentalist_states_growth` if that hypothesis finds uniform long-run premium regardless of income level. Aligns with `developmentalist_growth_premium_low_income_only` if the low-income restriction is confirmed.
""")

# 3
write_yaml("frontier_tfp_market_liberal_panel_1970_2024", """# yaml-language-server: $schema=../../schemas/hypothesis.schema.json
hypothesis_id: frontier_tfp_market_liberal_panel_1970_2024
version: 1
status: candidate
topic: growth
claim: Among OECD and high-income Asian economies, long-run TFP growth is higher where product-market regulation and state ownership are lower.
evidence_type: associational
sample:
  countries:
    - USA
    - GBR
    - DEU
    - FRA
    - ITA
    - ESP
    - NLD
    - BEL
    - AUT
    - SWE
    - NOR
    - DNK
    - FIN
    - IRL
    - JPN
    - KOR
    - AUS
    - CAN
    - NZL
    - CHE
    - PRT
    - GRC
    - SGP
    - HKG
    - TWN
  period: [1970, 2024]
  temporal_structure: panel
variables:
  outcome:
    - name: tfp_growth
      source: pwt:rtfpna
      transformation: annual_log_diff
      notes: Penn World Table TFP at constant national prices; annual log difference.
    - name: labour_productivity_growth
      source: oecd_stan:gdp_per_hour_worked
      transformation: annual_log_diff
  treatment:
    - name: product_market_regulation
      source: oecd_pmr:pmr
      transformation: level
      notes: OECD PMR overall indicator; lower is more liberal.
    - name: state_ownership_share
      source: oecd_pmr:state_control
      transformation: level
      notes: OECD PMR state-control sub-component.
  controls:
    - name: log_gdp_per_capita
      source: world_bank_wdi:NY.GDP.PCAP.KD
      transformation: log
    - name: r_d_expenditure_gdp
      source: world_bank_wdi:GB.XPD.RSDV.GD.ZS
      transformation: level
    - name: human_capital
      source: owid:mean-years-of-schooling-long-run-1870
      transformation: level
    - name: trade_openness
      source: world_bank_wdi:NE.TRD.GNFS.ZS
      transformation: level
estimator:
  template: panel_fe
  fixed_effects: [country, year]
  clustering: country
  notes: Panel FE regression of TFP growth on product-market regulation and state-ownership measures. Controls for convergence, innovation effort, human capital, and trade openness.
falsification:
  rule: The hypothesis is refuted if the coefficient on product-market regulation is not negative and significant at p<0.10, or if the coefficient on state-ownership share is not negative and significant at p<0.10, in a panel FE of TFP growth among OECD and high-income Asian economies 1970-2024.
  test: panel_fe_tfp_on_pmr_state_ownership
  threshold:
    pmr_coef: "<0 and p<0.10"
    state_ownership_coef: "<0 and p<0.10"
prior_confidence: 0.6
disclosure: Author is sympathetic to market-liberal arguments but acknowledges that OECD PMR data begins in 1975 and coverage for Asian economies is limited; results may be driven by European variation.
steelman: hypotheses/steelman/frontier_tfp_market_liberal_panel_1970_2024.md
scope:
  period: [1970, 2024]
  countries:
    - USA
    - GBR
    - DEU
    - FRA
    - ITA
    - ESP
    - NLD
    - BEL
    - AUT
    - SWE
    - NOR
    - DNK
    - FIN
    - IRL
    - JPN
    - KOR
    - AUS
    - CAN
    - NZL
    - CHE
    - PRT
    - GRC
    - SGP
    - HKG
    - TWN
  outcome_dim:
    - productivity
    - competition_concentration
  policy_family:
    - competition_policy
    - regulation
    - privatisation_nationalisation
notes: OECD PMR coverage for Korea, Singapore, Hong Kong, Taiwan is sparse before 1998; interpolation or alternative sources (Fraser EFW regulation sub-index) used as robustness.
""")

write_steelman("frontier_tfp_market_liberal_panel_1970_2024", """# Steelman — Frontier TFP and Market Liberalisation (1970–2024)

## Strongest version of the claim
Within the OECD and high-income Asian sample, economies that maintained lower product-market regulation and smaller state-ownership footprints achieved systematically higher TFP growth over 1970-2024. The relationship is not driven by a few outlier liberalisers but is visible across the full distribution, holds after controlling for R&D intensity and human capital, and is robust to using alternative TFP measures (PWT, OECD STAN).

## Key evidence the claim would need
1. Negative, statistically significant coefficients on OECD PMR and state-ownership indicators in a panel FE of TFP growth, with magnitude economically meaningful (e.g., a one-SD reduction in PMR associated with +0.2-0.4pp annual TFP growth).
2. Robustness to inclusion of country-specific time trends and to alternative TFP measures.
3. Evidence that the channel runs through firm entry, reallocation, and innovation rather than through compositional shifts alone.

## Best counterarguments
- **Endogeneity:** High-TFP economies may be able to afford deregulation; low-TFP economies may regulate to protect declining sectors. Causation may run from productivity to regulation, not the reverse.
- **Selection on OECD membership:** The sample is already a selected set of high-income economies; variation in PMR within this group may be too narrow to detect large effects.
- **Singapore and Korea exceptions:** Both achieved high TFP growth with significant state involvement; if the regression is driven by European post-1990 deregulation stories, the claim may not generalise to Asian frontier economies.
- **TFP measurement error:** Residual TFP picks up many non-technology factors (capacity utilisation, mark-ups, mismeasurement of intangibles); the correlation may reflect measurement rather than true technology differences.

## Boundary conditions
- Applies to high-income economies near the frontier; low-income economies may benefit from state coordination to overcome coordination failures.
- Short-run TFP fluctuations (recessions, oil shocks) may obscure the long-run relationship; the test requires multi-decade horizons.
- Sectoral composition matters: natural-resource-dependent high-income economies (Norway, Australia) may show different PMR-TFP links than manufacturing-led ones.

## Relation to existing hypotheses
Aligns with `market_reform_duration_growth_persistence` and `economic_freedom_index_income_correlation`. Tensions with `singapore_state_capacity_market_openness_combo` and `korea_post_chaebol_liberalisation_frontier_growth` if state involvement is found complementary rather than substitutable for TFP growth.
""")

# 4
write_yaml("high_income_escape_market_openness_1950_2024", """# yaml-language-server: $schema=../../schemas/hypothesis.schema.json
hypothesis_id: high_income_escape_market_openness_1950_2024
version: 1
status: candidate
topic: growth
claim: Countries escaping middle income into high income are more likely to combine export openness with domestic market competition than export promotion with persistent domestic protection.
evidence_type: associational
sample:
  countries:
    - KOR
    - TWN
    - SGP
    - HKG
    - CHL
    - MYS
    - THA
    - POL
    - HUN
    - CZE
    - EST
    - SVN
    - GRC
    - PRT
    - ESP
    - IRL
    - ISR
    - MEX
    - BRA
    - ARG
    - TUR
    - ZAF
    - COL
    - PER
    - VNM
    - CHN
    - IND
    - IDN
    - PHL
  period: [1950, 2024]
  temporal_structure: panel
variables:
  outcome:
    - name: high_income_escape_dummy
      source: world_bank_wdi:NY.GDP.PCAP.KD
      transformation: indicator_crossing_threshold
      notes: Dummy = 1 in year when country first crosses World Bank high-income threshold (constant 2015 USD, ~$13,845 in 2023) and remains above for 5+ years.
    - name: real_gdp_per_capita_growth
      source: world_bank_wdi:NY.GDP.MKTP.KD.ZG
      transformation: level
  treatment:
    - name: export_openness
      source: world_bank_wdi:NE.TRD.GNFS.ZS
      transformation: level
    - name: domestic_market_competition
      source: oecd_pmr:pmr
      transformation: level
      notes: Lower PMR = more competition; for non-OECD countries, Fraser EFW regulation sub-index used as proxy.
    - name: tariff_protection_avg
      source: world_bank_wits:tariff_average
      transformation: level
  controls:
    - name: log_initial_gdp_pc
      source: maddison:real_gdp_pc
      transformation: log
    - name: institutional_quality
      source: wgi:RL.EST
      transformation: level
    - name: human_capital
      source: owid:mean-years-of-schooling-long-run-1870
      transformation: level
    - name: manufacturing_value_added_share
      source: world_bank_wdi:NV.IND.MANF.ZS
      transformation: level
estimator:
  template: panel_fe
  fixed_effects: [country, year]
  clustering: country
  notes: Panel FE or conditional logit for escaping middle income, with interaction between export openness and domestic competition. Tests whether the combination outperforms export promotion with domestic protection.
falsification:
  rule: The hypothesis is refuted if the interaction between export openness and low domestic protection (or high competition) is not positive and significant at p<0.10 in predicting high-income escape, or if export promotion combined with high domestic protection performs equally well.
  test: panel_fe_interaction_openness_competition
  threshold:
    interaction_coef: ">0 and p<0.10"
prior_confidence: 0.6
disclosure: Author acknowledges that the World Bank income threshold is a moving target and that escapees are a selected sample; the test may be biased toward observed success cases.
steelman: hypotheses/steelman/high_income_escape_market_openness_1950_2024.md
scope:
  period: [1950, 2024]
  countries:
    - KOR
    - TWN
    - SGP
    - HKG
    - CHL
    - MYS
    - THA
    - POL
    - HUN
    - CZE
    - EST
    - SVN
    - GRC
    - PRT
    - ESP
    - IRL
    - ISR
    - MEX
    - BRA
    - ARG
    - TUR
    - ZAF
    - COL
    - PER
    - VNM
    - CHN
    - IND
    - IDN
    - PHL
  outcome_dim:
    - gdp_growth
    - trade_liberalisation
    - competition_concentration
  policy_family:
    - trade_policy
    - competition_policy
    - industrial_policy
notes: WITS tariff data has gaps for many countries before 1990; interpolation and UN Comtrade alternative used. OECD PMR coverage limited before 1998 for emerging economies.
""")

write_steelman("high_income_escape_market_openness_1950_2024", """# Steelman — High-Income Escape and Market Openness (1950–2024)

## Strongest version of the claim
The historical record of countries that escaped middle-income status into sustained high income shows a systematic pattern: they combined integration into world markets (export openness, low border barriers) with competitive domestic markets (low product-market regulation, low state-ownership, low barriers to firm entry). Countries that promoted exports while maintaining high domestic protection or state-directed allocation were less likely to complete the escape, even when early catch-up growth was rapid.

## Key evidence the claim would need
1. A cross-country panel or event-history model showing that the interaction of export openness and domestic competition significantly predicts crossing the high-income threshold.
2. Case studies where sustained domestic protection correlated with plateau or reversal (e.g., Argentina ISI, Malaysia post-1990) versus cases where liberalisation accompanied escape (Korea post-1997, Chile post-1980s).
3. Sectoral evidence that protected domestic industries eventually became drag sectors while exporting sectors became growth poles.

## Best counterarguments
- **Korea-Taiwan timing:** Both maintained significant domestic protection and state direction well into their high-income transition; the claim may conflate the timing of liberalisation with its necessity.
- **Small-N escape problem:** Very few countries have escaped middle income since 1950; statistical power is low and the result may be dominated by East Asian outliers.
- **Policy-bundle inseparability:** Export promotion and domestic protection were often part of the same package (e.g., Korea's import-substitution-plus-export-push); disentangling them requires fine-grained sectoral data not available in standard panels.
- **Institutional confound:** Countries that liberalised domestically also tended to improve rule of law and state capacity; the competition effect may proxy for broader institutional upgrading.

## Boundary conditions
- Claim is about the *combination* of openness and competition; either alone may be insufficient.
- Less relevant to city-states (Singapore, Hong Kong) where domestic market size is trivial.
- Resource-rich escapees (e.g., Chile copper, Malaysia palm oil) may follow different paths.

## Relation to existing hypotheses
Aligns with `catch_up_growth_fades_after_middle_income_threshold` and `market_reform_duration_growth_persistence`. Tensions with `industrial_policy_developmentalist_states_growth` if the latter treats export promotion and domestic protection as jointly effective.
""")

# 5
write_yaml("long_run_consumption_frontier_market_score_1970_2024", """# yaml-language-server: $schema=../../schemas/hypothesis.schema.json
hypothesis_id: long_run_consumption_frontier_market_score_1970_2024
version: 1
status: candidate
topic: growth
claim: Household consumption per capita converges more strongly to the US frontier in countries with higher long-run economic-freedom scores.
evidence_type: associational
sample:
  countries:
    - USA
    - GBR
    - DEU
    - FRA
    - ITA
    - ESP
    - NLD
    - BEL
    - AUT
    - SWE
    - NOR
    - DNK
    - FIN
    - IRL
    - JPN
    - KOR
    - AUS
    - CAN
    - NZL
    - CHE
    - PRT
    - GRC
    - SGP
    - HKG
    - TWN
    - CHL
    - MEX
    - ARG
    - BRA
    - TUR
    - POL
    - HUN
    - CZE
    - EST
    - ISR
    - ZAF
  period: [1970, 2024]
  temporal_structure: panel
variables:
  outcome:
    - name: household_consumption_per_capita
      source: world_bank_wdi:NE.CON.PRVT.ZS
      transformation: log
      notes: Private consumption share of GDP multiplied by real GDP per capita to approximate consumption per capita; or direct HCE per capita where available.
    - name: consumption_us_frontier_gap
      source: constructed:log_gap_to_us
      transformation: log_ratio_to_us
  treatment:
    - name: economic_freedom_score
      source: fraser_efw:aggregate_score
      transformation: level
    - name: legal_system_property_rights
      source: fraser_efw:legal_system_property_rights
      transformation: level
  controls:
    - name: log_gdp_per_capita
      source: world_bank_wdi:NY.GDP.PCAP.KD
      transformation: log
    - name: trade_openness
      source: world_bank_wdi:NE.TRD.GNFS.ZS
      transformation: level
    - name: government_size
      source: fraser_efw:government_size
      transformation: level
    - name: inflation_rate
      source: world_bank_wdi:FP.CPI.TOTL.ZG
      transformation: level
estimator:
  template: panel_fe
  fixed_effects: [country, year]
  clustering: country
  notes: Panel FE of log consumption-per-capita convergence to US frontier on economic-freedom score and sub-components. Tests whether higher market scores predict faster convergence in living standards.
falsification:
  rule: The hypothesis is refuted if the coefficient on economic-freedom score in a consumption-convergence regression is not positive and significant at p<0.10, or if countries with higher scores show slower or no faster convergence to the US consumption frontier.
  test: panel_fe_consumption_convergence
  threshold:
    efw_coef: ">0 and p<0.10"
prior_confidence: 0.55
disclosure: Author acknowledges that consumption data quality varies across countries and that Fraser EFW scores may conflate market freedom with other institutional features.
steelman: hypotheses/steelman/long_run_consumption_frontier_market_score_1970_2024.md
scope:
  period: [1970, 2024]
  countries:
    - USA
    - GBR
    - DEU
    - FRA
    - ITA
    - ESP
    - NLD
    - BEL
    - AUT
    - SWE
    - NOR
    - DNK
    - FIN
    - IRL
    - JPN
    - KOR
    - AUS
    - CAN
    - NZL
    - CHE
    - PRT
    - GRC
    - SGP
    - HKG
    - TWN
    - CHL
    - MEX
    - ARG
    - BRA
    - TUR
    - POL
    - HUN
    - CZE
    - EST
    - ISR
    - ZAF
  outcome_dim:
    - gdp_growth
    - institutional_quality
  policy_family:
    - institutional_reform
    - trade_policy
    - regulation
notes: Direct household consumption per capita from national accounts is preferred; where unavailable, private-consumption-share x GDP per capita is used as proxy. Fraser EFW starts 1970.
""")

write_steelman("long_run_consumption_frontier_market_score_1970_2024", """# Steelman — Long-Run Consumption Convergence and Market Scores (1970–2024)

## Strongest version of the claim
Household consumption per capita — a more direct welfare metric than GDP — converges toward the US frontier faster in countries that maintain higher economic-freedom scores, particularly in legal-system and property-rights dimensions. The effect is not merely a GDP-level correlation but reflects genuine welfare gains mediated by market access, price efficiency, and reduced rent-seeking.

## Key evidence the claim would need
1. A panel FE showing that economic-freedom scores (Fraser or Heritage) predict faster convergence in consumption per capita to the US level, with legal-system sub-index doing most of the work.
2. Robustness to using actual household-survey consumption (where available) rather than national-accounts imputation.
3. Evidence that the channel runs through lower price distortions and higher variety/quality of goods rather than purely through income redistribution.

## Best counterarguments
- **GDP-to-consumption pass-through:** The correlation may simply reflect GDP-to-consumption pass-through; if market freedom raises GDP, it mechanically raises consumption without a separate welfare channel.
- **Distributional blind spot:** High economic-freedom scores may correlate with higher average consumption but also higher inequality; median or bottom-quintile consumption may not converge.
- **Nordic exception:** Nordic countries combine high living standards with relatively large government size (penalised in Fraser indices); if the regression is driven by government-size sub-components, the welfare conclusion may be misleading.
- **US-centric frontier:** Using the US as the consumption frontier may bias results toward US-style institutional bundles; European social-market models may achieve comparable welfare through different institutional paths.

## Boundary conditions
- Best tested among middle-income and high-income countries where consumption data is more reliable.
- Less relevant to command economies where measured consumption may not capture queuing, rationing, or quality differences.
- Short-run commodity booms can temporarily raise consumption without institutional improvement.

## Relation to existing hypotheses
Aligns with `economic_freedom_index_income_correlation` and `frontier_income_persistence_market_institutions_1960_2024`. Extends them by focusing on consumption welfare rather than production-side GDP.
""")

print("Done Track A 1-5")

# 6
write_yaml("developmentalist_growth_premium_low_income_only", """# yaml-language-server: $schema=../../schemas/hypothesis.schema.json
hypothesis_id: developmentalist_growth_premium_low_income_only
version: 1
status: candidate
topic: growth
claim: The growth advantage of developmentalist policy packages is concentrated among low-income countries and disappears in upper-middle-income or high-income samples.
evidence_type: causal
sample:
  countries:
    - KOR
    - TWN
    - SGP
    - CHN
    - VNM
    - IDN
    - PHL
    - IND
    - BGD
    - ETH
    - KEN
    - GHA
    - NGA
    - EGY
    - MAR
    - BRA
    - MEX
    - ARG
    - CHL
    - MYS
    - THA
    - ZAF
    - TUR
    - POL
    - HUN
  period: [1960, 2024]
  temporal_structure: panel
variables:
  outcome:
    - name: real_gdp_per_capita_growth
      source: world_bank_wdi:NY.GDP.MKTP.KD.ZG
      transformation: level
    - name: real_gdp_per_capita
      source: world_bank_wdi:NY.GDP.PCAP.KD
      transformation: log
  treatment:
    - name: developmentalist_policy_dummy
      source: constructed:binary_indicator
      transformation: binary
      notes: Coded 1 for selected East Asian and other developmentalist episodes per Amsden-Wade-Chang literature.
    - name: income_group_dummy
      source: constructed:world_bank_income_group
      transformation: categorical
      notes: Low-income, lower-middle, upper-middle, high-income classification from World Bank.
  controls:
    - name: log_initial_gdp_pc
      source: world_bank_wdi:NY.GDP.PCAP.KD
      transformation: log
    - name: human_capital
      source: owid:mean-years-of-schooling-long-run-1870
      transformation: level
    - name: institutional_quality
      source: wgi:RL.EST
      transformation: level
    - name: trade_openness
      source: world_bank_wdi:NE.TRD.GNFS.ZS
      transformation: level
estimator:
  template: panel_fe
  fixed_effects: [country, year]
  clustering: country
  notes: Panel FE with triple interaction (developmentalist x income_group x period). Tests whether the developmentalist premium is significant only in low-income subsamples.
falsification:
  rule: The hypothesis is refuted if the developmentalist growth premium is positive and significant at p<0.10 in the upper-middle-income or high-income subsamples, or if the premium does not differ significantly across income groups.
  test: panel_fe_subsample_interaction
  threshold:
    low_income_premium: ">0 and p<0.10"
    high_income_premium: "<=0 or p>=0.10"
prior_confidence: 0.55
disclosure: Author is aware that income-group classification is endogenous to growth itself and that the developmentalist coding is contested for borderline cases like Malaysia and Thailand.
steelman: hypotheses/steelman/developmentalist_growth_premium_low_income_only.md
scope:
  period: [1960, 2024]
  countries:
    - KOR
    - TWN
    - SGP
    - CHN
    - VNM
    - IDN
    - PHL
    - IND
    - BGD
    - ETH
    - KEN
    - GHA
    - NGA
    - EGY
    - MAR
    - BRA
    - MEX
    - ARG
    - CHL
    - MYS
    - THA
    - ZAF
    - TUR
    - POL
    - HUN
  outcome_dim:
    - gdp_growth
  policy_family:
    - industrial_policy
    - trade_policy
notes: World Bank income-group classifications change over time; use annual classification rather than fixed initial group. Developmentalist coding requires hand-curation.
""")

write_steelman("developmentalist_growth_premium_low_income_only", """# Steelman — Developmentalist Growth Premium in Low-Income Countries Only

## Strongest version of the claim
State-directed developmentalist policies — selective credit, sector targeting, export subsidies, and SOE-led investment — produce a measurable growth premium relative to comparable control countries, but this premium is confined to low-income settings where market failures are severe, capital markets are shallow, and technological catch-up is primarily about adopting existing methods. Once countries reach upper-middle-income status, the same policy package no longer adds value and may become a drag by protecting incumbents and distorting resource allocation.

## Key evidence the claim would need
1. A clear positive coefficient on the developmentalist dummy in low-income subsamples that attenuates to zero or flips negative in upper-middle-income and high-income subsamples.
2. Mechanism evidence that the low-income premium operates through capital deepening and labour reallocation, while the absence of premium at higher incomes reflects weaker TFP and innovation channels.
3. Case evidence that policy reform episodes (Korea 1997, China WTO accession) coincided with income-level transitions and sustained growth only after modifying the developmentalist package.

## Best counterarguments
- **Income-group endogeneity:** Countries that grow fast exit the low-income group quickly; the observed concentration may be a mechanical composition effect rather than a true income-level moderation.
- **Policy heterogeneity:** Developmentalist policies in low-income Ethiopia are not the same as developmentalist policies in high-income Korea; treating them as a single dummy conflates different treatments.
- **State-capacity threshold:** The premium may disappear not because of income level per se but because state capacity requirements rise with technological complexity; high-income countries with strong state capacity (Singapore) may still benefit.
- **Small-N at high income:** Very few countries have reached high income with a developmentalist history, so statistical power to detect a continuing premium is low.

## Boundary conditions
- Expectation is strongest for manufacturing-led catch-up; resource-led or service-led development may show different income-level dynamics.
- The claim is about the *average* marginal effect, not an absolute impossibility of developmentalist success at high income.
- Time horizon matters: short-run crisis-recovery episodes may benefit from state direction regardless of income level.

## Relation to existing hypotheses
Directly tensions with `industrial_policy_developmentalist_states_growth` if the latter finds a uniform long-run premium. Aligns with `catch_up_growth_fades_after_middle_income_threshold` and `high_income_escape_market_openness_1950_2024`.
""")

# 7
write_yaml("frontier_real_wage_growth_market_competition_1980_2024", """# yaml-language-server: $schema=../../schemas/hypothesis.schema.json
hypothesis_id: frontier_real_wage_growth_market_competition_1980_2024
version: 1
status: candidate
topic: growth
claim: Real wage growth at the frontier is stronger in countries with more competitive product markets and lower barriers to firm entry.
evidence_type: associational
sample:
  countries:
    - USA
    - GBR
    - DEU
    - FRA
    - ITA
    - ESP
    - NLD
    - BEL
    - AUT
    - SWE
    - NOR
    - DNK
    - FIN
    - IRL
    - JPN
    - KOR
    - AUS
    - CAN
    - NZL
    - CHE
    - PRT
    - SGP
    - HKG
    - TWN
  period: [1980, 2024]
  temporal_structure: panel
variables:
  outcome:
    - name: real_wage_growth
      source: ilo:avg_wage_real
      transformation: annual_log_diff
      notes: ILOSTAT real average wage growth where available; OECD Earnings database as alternative for OECD members.
    - name: median_real_wage_growth
      source: oecd:median_wages
      transformation: annual_log_diff
      notes: OECD median real wage growth for subset of countries with comparable data.
  treatment:
    - name: product_market_regulation
      source: oecd_pmr:pmr
      transformation: level
      notes: Lower PMR = more competitive product markets.
    - name: barriers_to_entry
      source: oecd_pmr:barriers_to_entry
      transformation: level
      notes: OECD PMR barriers-to-entrepreneurship sub-component.
  controls:
    - name: labour_productivity_growth
      source: oecd_stan:gdp_per_hour_worked
      transformation: annual_log_diff
    - name: unemployment_rate
      source: world_bank_wdi:SL.UEM.TOTL.ZS
      transformation: level
    - name: trade_openness
      source: world_bank_wdi:NE.TRD.GNFS.ZS
      transformation: level
    - name: union_density
      source: oecd:union_density
      transformation: level
estimator:
  template: panel_fe
  fixed_effects: [country, year]
  clustering: country
  notes: Panel FE of real wage growth on product-market competition and barriers to entry, controlling for productivity growth and labour-market institutions.
falsification:
  rule: The hypothesis is refuted if the coefficient on product-market regulation is not negative and significant at p<0.10, or if the coefficient on barriers to entry is not negative and significant at p<0.10, in predicting real wage growth among frontier economies.
  test: panel_fe_real_wage_on_competition
  threshold:
    pmr_coef: "<0 and p<0.10"
    barriers_entry_coef: "<0 and p<0.10"
prior_confidence: 0.6
disclosure: Author acknowledges that real wage data is patchy outside OECD and that the productivity-wage link may dominate the competition channel.
steelman: hypotheses/steelman/frontier_real_wage_growth_market_competition_1980_2024.md
scope:
  period: [1980, 2024]
  countries:
    - USA
    - GBR
    - DEU
    - FRA
    - ITA
    - ESP
    - NLD
    - BEL
    - AUT
    - SWE
    - NOR
    - DNK
    - FIN
    - IRL
    - JPN
    - KOR
    - AUS
    - CAN
    - NZL
    - CHE
    - PRT
    - SGP
    - HKG
    - TWN
  outcome_dim:
    - employment_labour
    - productivity
    - competition_concentration
  policy_family:
    - competition_policy
    - regulation
notes: ILOSTAT real wage coverage is sparse for Singapore, Hong Kong, Taiwan before 2000; OECD alternative used where available. PMR data begins 1998 for most countries.
""")

write_steelman("frontier_real_wage_growth_market_competition_1980_2024", """# Steelman — Frontier Real Wage Growth and Market Competition (1980–2024)

## Strongest version of the claim
In high-income frontier economies, stronger real wage growth over 1980-2024 is systematically associated with lower product-market regulation and lower barriers to firm entry. The channel runs through increased labour demand from new entrants, reduced monopsony power in concentrated sectors, and faster productivity diffusion, rather than solely through aggregate productivity growth.

## Key evidence the claim would need
1. Negative, significant coefficients on OECD PMR and barriers-to-entry indicators in a panel FE of real wage growth, after controlling for labour productivity growth.
2. Evidence that the competition-wage link is stronger in sectors with traditionally high concentration (retail, professional services, telecoms).
3. Robustness to using median wages rather than mean wages, to ensure the result is not driven by top-earner compensation in liberalised financial sectors.

## Best counterarguments
- **Productivity pass-through dominates:** Real wages may track labour productivity regardless of competition; if competition raises productivity, the channel is indirect and the claim about competition per se is overstated.
- **US anomaly:** The US has relatively competitive product markets but stagnant median wages 1980-2020; the correlation may be driven by European deregulation episodes (UK, Scandinavia) rather than a general law.
- **Labour-market institutions dominate:** Union density, minimum wages, and collective bargaining coverage may explain more wage variation than product-market competition; controlling for them may absorb the competition effect.
- **Endogeneity:** Countries with strong wage growth may be politically able to deregulate; causation may run from wages to reform appetite.

## Boundary conditions
- Best tested among OECD and high-income Asian economies with reliable wage data.
- Sectoral composition matters: manufacturing-led economies may show different competition-wage links than service-led ones.
- Short-run adjustment costs from deregulation (job losses in protected sectors) may obscure long-run wage gains.

## Relation to existing hypotheses
Aligns with `frontier_tfp_market_liberal_panel_1970_2024` and `productivity_compensation_decoupling_post_1973`. Tensions with `us_1945_1973_labour_compact_productivity_wage_link` if the latter attributes wage growth primarily to bargaining institutions rather than market competition.
""")

# 8
write_yaml("catch_up_capital_deepening_not_tfp", """# yaml-language-server: $schema=../../schemas/hypothesis.schema.json
hypothesis_id: catch_up_capital_deepening_not_tfp
version: 1
status: candidate
topic: growth
claim: Developmentalist catch-up gains are explained more by capital deepening and labour reallocation than by sustained TFP acceleration.
evidence_type: causal
sample:
  countries:
    - KOR
    - TWN
    - SGP
    - CHN
    - VNM
    - IDN
    - MYS
    - THA
    - PHL
    - IND
    - BGD
    - BRA
    - MEX
    - CHL
    - ARG
    - TUR
    - ZAF
  period: [1960, 2024]
  temporal_structure: panel
variables:
  outcome:
    - name: real_gdp_per_capita_growth
      source: world_bank_wdi:NY.GDP.MKTP.KD.ZG
      transformation: level
  decomposition_channels:
    - name: capital_deepening_contribution
      source: pwt:rnna
      transformation: growth_contribution_per_worker
      notes: Growth of capital stock per worker, weighted by capital share, from Penn World Table.
    - name: labour_reallocation_contribution
      source: constructed:sectoral_shift
      transformation: growth_contribution
      notes: Structural change contribution estimated from sectoral employment and value-added shifts (McMillan-Rodrik method).
    - name: tfp_growth
      source: pwt:rtfpna
      transformation: annual_log_diff
  treatment:
    - name: developmentalist_policy_dummy
      source: constructed:binary_indicator
      transformation: binary
  controls:
    - name: log_initial_gdp_pc
      source: world_bank_wdi:NY.GDP.PCAP.KD
      transformation: log
    - name: human_capital
      source: owid:mean-years-of-schooling-long-run-1870
      transformation: level
    - name: trade_openness
      source: world_bank_wdi:NE.TRD.GNFS.ZS
      transformation: level
estimator:
  template: panel_fe_decomposition
  fixed_effects: [country, year]
  clustering: country
  notes: Growth-decomposition panel FE that estimates the contribution of capital deepening, labour reallocation, and TFP to the developmentalist growth premium. Tests whether the premium is driven by factor accumulation rather than TFP.
falsification:
  rule: The hypothesis is refuted if the developmentalist dummy has a larger and significant coefficient on TFP growth than on capital-deepening or labour-reallocation contributions, or if TFP explains more than 50% of the developmentalist premium in a standard growth accounting decomposition.
  test: panel_fe_decomposition_developmentalist
  threshold:
    capital_coef_larger: true
    tfp_share_of_premium: "<0.50"
prior_confidence: 0.55
disclosure: Author acknowledges that growth-accounting decompositions are sensitive to capital-share assumptions and that PWT TFP is a residual subject to measurement error.
steelman: hypotheses/steelman/catch_up_capital_deepening_not_tfp.md
scope:
  period: [1960, 2024]
  countries:
    - KOR
    - TWN
    - SGP
    - CHN
    - VNM
    - IDN
    - MYS
    - THA
    - PHL
    - IND
    - BGD
    - BRA
    - MEX
    - CHL
    - ARG
    - TUR
    - ZAF
  outcome_dim:
    - gdp_growth
    - productivity
  policy_family:
    - industrial_policy
    - fiscal_policy
notes: PWT capital stock data has known limitations for China and some emerging economies; robustness to alternative capital series (IMF IFS, national accounts) is planned. Labour reallocation requires sectoral employment data from ILO or national sources.
""")

write_steelman("catch_up_capital_deepening_not_tfp", """# Steelman — Catch-Up Driven by Capital Deepening, Not TFP

## Strongest version of the claim
The rapid convergence observed in developmentalist catch-up economies (East Asia, selected others) is primarily attributable to high rates of physical and human capital accumulation and to labour reallocation from low-productivity agriculture to industry, rather than to sustained total factor productivity growth. The state-directed credit and investment programmes succeeded in mobilising savings and directing them into targeted sectors, but did not generate autonomous technological progress at the frontier.

## Key evidence the claim would need
1. A standard growth-accounting decomposition showing that capital deepening and structural change together explain more than 60% of the growth premium in developmentalist episodes.
2. TFP growth in developmentalist episodes that is not statistically different from or only modestly above comparable control countries after controlling for capital deepening.
3. Sectoral evidence that the fastest-growing sectors were capital-intensive (steel, chemicals, shipbuilding, semiconductors fabrication) rather than R&D-intensive software or frontier innovation.

## Best counterarguments
- **TFP measurement error:** Residual TFP understates true technological progress when capital quality improves (e.g., semiconductor fabrication equipment) or when human capital is mismeasured.
- **China outlier:** China's TFP growth post-1978 and especially post-WTO was substantial; if China drives the developmentalist average, the capital-deepening story may be overstated.
- **Endogenous TFP:** Capital deepening may itself raise TFP through learning-by-doing and scale effects; separating them is conceptually difficult and mechanically sensitive to functional form.
- **Korea-Taiwan innovation transition:** Both transitioned from capital-deepening catch-up to R&D-intensive innovation in the 2000s; a long-run average may miss the phase shift.

## Boundary conditions
- Claim applies most clearly to the catch-up phase (low-to-middle income); frontier economies by definition cannot rely on capital deepening alone.
- Sectoral composition matters: manufacturing-led catch-up is more capital-deepening intensive than services-led growth.
- Time period matters: post-2000, some developmentalist economies (Korea, Taiwan) show significant TFP-driven growth.

## Relation to existing hypotheses
Tensions with `industrial_policy_developmentalist_states_growth` if the latter treats the premium as uniform and technology-driven. Aligns with `developmentalist_growth_premium_low_income_only` and `catch_up_growth_fades_after_middle_income_threshold` if the fade reflects capital-deepening limits.
""")

print("Done Track A 6-8")

# 9
write_yaml("market_reform_duration_growth_persistence", """# yaml-language-server: $schema=../../schemas/hypothesis.schema.json
hypothesis_id: market_reform_duration_growth_persistence
version: 1
status: candidate
topic: growth
claim: Market-oriented reform episodes that persist for at least 20 years generate more durable GDP-per-capita gains than state-led industrial-policy episodes of similar initial intensity.
evidence_type: causal
sample:
  countries:
    - CHL
    - GBR
    - NZL
    - AUS
    - USA
    - CAN
    - DEU
    - FRA
    - ESP
    - NLD
    - SWE
    - DNK
    - FIN
    - IRL
    - EST
    - POL
    - HUN
    - CZE
    - SVN
    - LVA
    - LTU
    - KOR
    - TWN
    - SGP
    - HKG
    - MYS
    - THA
    - IDN
    - PHL
    - CHN
    - VNM
    - IND
    - BRA
    - MEX
    - ARG
    - ZAF
    - TUR
    - COL
    - PER
    - EGY
    - MAR
    - KEN
    - GHA
    - NGA
  period: [1960, 2024]
  temporal_structure: panel
variables:
  outcome:
    - name: real_gdp_per_capita
      source: world_bank_wdi:NY.GDP.PCAP.KD
      transformation: log
    - name: real_gdp_per_capita_growth
      source: world_bank_wdi:NY.GDP.MKTP.KD.ZG
      transformation: level
  treatment:
    - name: market_reform_episode_dummy
      source: constructed:binary_indicator
      transformation: binary
      notes: Coded 1 during identified market-oriented reform episodes lasting >=20 years (e.g., Chile post-1985, UK post-1979, Estonia post-1991, China post-1978 treated as mixed).
    - name: state_led_industrial_policy_episode_dummy
      source: constructed:binary_indicator
      transformation: binary
      notes: Coded 1 during identified state-led industrial-policy episodes of similar initial intensity (e.g., Korea HCI 1973-1997, Brazil ISI 1950-1980, India pre-1991).
  controls:
    - name: log_initial_gdp_pc
      source: world_bank_wdi:NY.GDP.PCAP.KD
      transformation: log
    - name: human_capital
      source: owid:mean-years-of-schooling-long-run-1870
      transformation: level
    - name: institutional_quality
      source: wgi:RL.EST
      transformation: level
    - name: trade_openness
      source: world_bank_wdi:NE.TRD.GNFS.ZS
      transformation: level
estimator:
  template: panel_fe
  fixed_effects: [country, year]
  clustering: country
  notes: Panel FE comparing cumulative GDP-per-capita gains from market-reform episodes >=20 years vs state-led industrial-policy episodes of similar initial intensity. Synthetic control or synth-DiD as robustness for selected cases.
falsification:
  rule: The hypothesis is refuted if the cumulative GDP-per-capita gain from state-led industrial-policy episodes is greater than or equal to that from market-reform episodes of similar duration and initial intensity, or if the difference is not positive and significant at p<0.10.
  test: panel_fe_episode_comparison
  threshold:
    reform_gain_minus_state_gain: ">0 and p<0.10"
prior_confidence: 0.55
disclosure: Author acknowledges that episode identification is judgemental and that initial intensity is hard to calibrate across different policy regimes; results may be sensitive to episode selection.
steelman: hypotheses/steelman/market_reform_duration_growth_persistence.md
scope:
  period: [1960, 2024]
  countries:
    - CHL
    - GBR
    - NZL
    - AUS
    - USA
    - CAN
    - DEU
    - FRA
    - ESP
    - NLD
    - SWE
    - DNK
    - FIN
    - IRL
    - EST
    - POL
    - HUN
    - CZE
    - SVN
    - LVA
    - LTU
    - KOR
    - TWN
    - SGP
    - HKG
    - MYS
    - THA
    - IDN
    - PHL
    - CHN
    - VNM
    - IND
    - BRA
    - MEX
    - ARG
    - ZAF
    - TUR
    - COL
    - PER
    - EGY
    - MAR
    - KEN
    - GHA
    - NGA
  outcome_dim:
    - gdp_growth
    - institutional_quality
  policy_family:
    - institutional_reform
    - industrial_policy
    - trade_policy
notes: Episode coding requires hand-curation from economic-history sources. China 1978-present is coded as mixed (market opening plus heavy state direction) and excluded from primary comparison but included as robustness.
""")

write_steelman("market_reform_duration_growth_persistence", """# Steelman — Market Reform Duration and Growth Persistence

## Strongest version of the claim
Market-oriented reform episodes — characterised by trade opening, product-market deregulation, privatisation, and fiscal consolidation — that are sustained for at least two decades produce larger and more durable cumulative gains in real GDP per capita than state-led industrial-policy episodes of comparable initial ambition and resource mobilisation. The durability reflects lower rent-seeking accumulation, better reallocation dynamics, and stronger institutional self-reinforcement.

## Key evidence the claim would need
1. A matched comparison of long-run reform episodes showing that market-reform episodes yield higher cumulative GDP-per-capita growth after 20 years than state-led episodes, matched on initial GDP, human capital, and institutional quality.
2. Evidence that the market-reform advantage grows over time (cumulates) rather than fading, consistent with institutional reinforcement.
3. Mechanism evidence that state-led episodes are more prone to reversal, crisis, or protectionist entrenchment after the initial high-growth phase.

## Best counterarguments
- **Episode heterogeneity:** Market-reform episodes vary enormously (UK Thatcher vs. Chile Pinochet vs. Estonia post-Soviet); state-led episodes also vary (Korea HCI vs. Brazil ISI vs. India pre-1991). Averaging across such different bundles may obscure that specific policies matter more than the market-vs-state label.
- **Selection bias:** Countries that can sustain market reforms for 20 years may already have stronger institutions, making the comparison unfair to state-led cases that often arise in weaker-institution settings.
- **China counterexample:** China's mixed model has persisted for 40+ years with very large cumulative gains; if coded as state-led, it challenges the claim.
- **Crisis confound:** Many market-reform episodes (Chile, UK, Estonia) followed severe crises that created reform windows; the post-crisis recovery may explain part of the gain.

## Boundary conditions
- Claim is about episodes of similar *initial* intensity; comparing modest market tweaks to ambitious five-year plans is not the test.
- Durability requires at least 20 years; shorter reform windows are excluded.
- Resource-rich economies may experience different dynamics due to rent-capture incentives.

## Relation to existing hypotheses
Aligns with `liberalisation_episodes_growth_trajectory` and `high_income_escape_market_openness_1950_2024`. Tensions with `industrial_policy_developmentalist_states_growth` and `korea_post_chaebol_liberalisation_frontier_growth` if the latter finds state-led episodes equally or more durable.
""")

# 10
write_yaml("frontier_income_volatility_state_allocation", """# yaml-language-server: $schema=../../schemas/hypothesis.schema.json
hypothesis_id: frontier_income_volatility_state_allocation
version: 1
status: candidate
topic: growth
claim: High state-directed allocation is associated with larger boom-bust cycles after middle-income status, even when early catch-up growth is strong.
evidence_type: associational
sample:
  countries:
    - KOR
    - TWN
    - SGP
    - HKG
    - CHN
    - MYS
    - THA
    - IDN
    - PHL
    - VNM
    - IND
    - BRA
    - MEX
    - ARG
    - CHL
    - TUR
    - ZAF
    - POL
    - HUN
    - CZE
    - EST
    - RUS
    - UKR
    - BLR
    - KAZ
  period: [1960, 2024]
  temporal_structure: panel
variables:
  outcome:
    - name: gdp_per_capita_volatility
      source: world_bank_wdi:NY.GDP.MKTP.KD.ZG
      transformation: rolling_sd_5yr
      notes: 5-year rolling standard deviation of real GDP growth.
    - name: crisis_dummy
      source: constructed:binary_indicator
      transformation: binary
      notes: Banking-currency-sovereign crisis indicator from Laeven-Valencia or similar catalogue.
  treatment:
    - name: state_directed_allocation_index
      source: constructed:composite_index
      transformation: level
      notes: Composite of SOE share of output, directed credit share, and state investment share; constructed from historical sources and OECD data where available.
    - name: middle_income_dummy
      source: constructed:indicator
      transformation: binary
      notes: Indicator = 1 when country is above lower-middle-income threshold.
  controls:
    - name: log_gdp_per_capita
      source: world_bank_wdi:NY.GDP.PCAP.KD
      transformation: log
    - name: trade_openness
      source: world_bank_wdi:NE.TRD.GNFS.ZS
      transformation: level
    - name: financial_depth
      source: world_bank_wdi:GFDD.DI.14
      transformation: level
      notes: Private credit to GDP ratio.
    - name: institutional_quality
      source: wgi:RL.EST
      transformation: level
estimator:
  template: panel_fe
  fixed_effects: [country, year]
  clustering: country
  notes: Panel FE of output volatility on state-directed allocation, interacted with middle-income status. Tests whether state allocation amplifies volatility post-catch-up.
falsification:
  rule: The hypothesis is refuted if the interaction between state-directed allocation and middle-income dummy is not positive and significant at p<0.10 in predicting output volatility or crisis frequency, or if high state allocation is associated with lower volatility after middle income.
  test: panel_fe_volatility_interaction
  threshold:
    interaction_coef: ">0 and p<0.10"
prior_confidence: 0.55
disclosure: Author acknowledges that crisis identification and state-allocation measurement are both contested and that commodity dependence may confound the volatility-state-allocation link.
steelman: hypotheses/steelman/frontier_income_volatility_state_allocation.md
scope:
  period: [1960, 2024]
  countries:
    - KOR
    - TWN
    - SGP
    - HKG
    - CHN
    - MYS
    - THA
    - IDN
    - PHL
    - VNM
    - IND
    - BRA
    - MEX
    - ARG
    - CHL
    - TUR
    - ZAF
    - POL
    - HUN
    - CZE
    - EST
    - RUS
    - UKR
    - BLR
    - KAZ
  outcome_dim:
    - gdp_growth
    - financial_crisis
    - institutional_quality
  policy_family:
    - industrial_policy
    - fiscal_policy
    - regulation
notes: State-directed allocation composite requires hand-assembly from multiple sources (OECD, national central banks, academic datasets). Post-Soviet states added for variation in state allocation.
""")

write_steelman("frontier_income_volatility_state_allocation", """# Steelman — Frontier Income Volatility and State-Directed Allocation

## Strongest version of the claim
Economies that rely heavily on state-directed resource allocation — through state-owned enterprises, directed credit, and sector-specific subsidies — experience larger output volatility and more severe boom-bust cycles after reaching middle-income status, even when their early catch-up phase shows strong growth. The mechanism is misallocation during booms, politically driven over-investment in favoured sectors, and abrupt correction when external conditions or subsidy capacity tightens.

## Key evidence the claim would need
1. A positive interaction between state-directed allocation and middle-income status in predicting output volatility or crisis incidence.
2. Case evidence of boom-bust episodes in state-directed middle-income economies (Malaysia 1997, Thailand 1997, Argentina recurring crises, Russia 1998, Kazakhstan 2008).
3. Sectoral evidence that volatility is concentrated in state-supported sectors (construction, heavy industry, finance) rather than in tradable or competitive sectors.

## Best counterarguments
- **Crisis type heterogeneity:** Currency and banking crises in middle-income economies may reflect capital-account openness and short-term debt more than state allocation; attributing volatility to state direction may misidentify the causal channel.
- **Korea-Taiwan exceptions:** Both had significant state direction and experienced crises (1997 for Korea) but also rapid recovery; the claim about systematic larger boom-bust may be overstated if recovery is part of the story.
- **Commodity confound:** Many state-directed economies are also commodity-dependent; commodity price cycles drive volatility independently of domestic policy.
- **Small-N crisis episodes:** The number of severe boom-bust cycles in the sample is small; statistical inference is fragile.

## Boundary conditions
- Claim is about *middle-income and above*; low-income state-directed economies may not have the financial depth to generate large cycles.
- Applies most clearly to economies with significant domestic credit markets; cash-constrained low-income economies experience different volatility patterns.
- Post-crisis recovery dynamics are not part of the claim; the hypothesis focuses on cycle amplitude, not recovery speed.

## Relation to existing hypotheses
Aligns with `catch_up_growth_fades_after_middle_income_threshold` and `malaysia_developmentalist_plateau_1990_2024`. Tensions with `industrial_policy_developmentalist_states_growth` if the latter treats state direction as uniformly beneficial without accounting for volatility costs.
""")

print("Done Track A 9-10")
