#!/usr/bin/env python3
"""Generate 20 hypothesis YAMLs + steelman files for Tracks A and B."""
import os

GROWTH_DIR = "./hypotheses/growth"
STEELMAN_DIR = "./hypotheses/steelman"

os.makedirs(GROWTH_DIR, exist_ok=True)
os.makedirs(STEELMAN_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def write_yaml(hid, content):
    path = os.path.join(GROWTH_DIR, f"{hid}.yaml")
    with open(path, "w") as f:
        f.write(content)
    print(f"Wrote YAML: {path}")

def write_steelman(hid, content):
    path = os.path.join(STEELMAN_DIR, f"{hid}.md")
    with open(path, "w") as f:
        f.write(content)
    print(f"Wrote steelman: {path}")

# ---------------------------------------------------------------------------
# Track A: 6–10
# ---------------------------------------------------------------------------

# 6
write_yaml("developmentalist_growth_premium_low_income_only", '''# yaml-language-server: $schema=../../schemas/hypothesis.schema.json
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
  notes: Panel FE with triple interaction (developmentalist × income_group × period). Tests whether the developmentalist premium is significant only in low-income subsamples.
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
''')

write_steelman("developmentalist_growth_premium_low_income_only", '''# Steelman — Developmentalist Growth Premium in Low-Income Countries Only

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
''')

# 7
write_yaml("frontier_real_wage_growth_market_competition_1980_2024", '''# yaml-language-server: $schema=../../schemas/hypothesis.schema.json
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
''')

write_steelman("frontier_real_wage_growth_market_competition_1980_2024", '''# Steelman — Frontier Real Wage Growth and Market Competition (1980–2024)

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
''')

# 8
write_yaml("catch_up_capital_deepening_not_tfp", '''# yaml-language-server: $schema=../../schemas/hypothesis.schema.json
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
''')

write_steelman("catch_up_capital_deepening_not_tfp", '''# Steelman — Catch-Up Driven by Capital Deepening, Not TFP

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
''')

# 9
write_yaml("market_reform_duration_growth_persistence", '''# yaml-language-server: $schema=../../schemas/hypothesis.schema.json
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
''')

write_steelman("market_reform_duration_growth_persistence", '''# Steelman — Market Reform Duration and Growth Persistence

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
''')

# 10
write_yaml("frontier_income_volatility_state_allocation", '''# yaml-language-server: $schema=../../schemas/hypothesis.schema.json
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
''')

write_steelman("frontier_income_volatility_state_allocation", '''# Steelman — Frontier Income Volatility and State-Directed Allocation

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
''')

print("Done Track A 6-10")
