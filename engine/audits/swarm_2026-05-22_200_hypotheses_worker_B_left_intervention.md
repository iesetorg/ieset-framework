# Worker B Left / Interventionist Hypothesis Candidates - 2026-05-22

Scope: 50 falsifiable candidates for left/interventionist schools:
`marxian`, `marxist_leninist`, `democratic_socialist`, `market_socialist`,
`social_democratic`, `post_keynesian`, `mmt`, `degrowth`, and
`eco_socialist`.

School labels below are interpretation lenses only. They are not proposed as
treatments, controls, or outcome data. Every candidate uses observable policy,
institutional, or macro variables and can support or refute a school claim
depending on the measured sign, magnitude, and robustness.

Runability flags:

- READY_NOW: plausible first pass with local vintages already present.
- NEEDS_ALIAS: likely local data exist, but exact filters or derived aliases need
  wiring.
- NEEDS_DATA: the key policy variable is not yet available locally.

## Candidates

1. `redistribution_gap_bottom40_real_income_growth_oecd`
   - School lens: `social_democratic`, `democratic_socialist`, `marxian`.
   - Testable claim: Larger tax-and-transfer redistribution gaps predict faster bottom-40 real disposable-income growth over the next three years without a GDP-per-capita growth penalty larger than 0.3 percentage points per year.
   - Measurable variables: treatment = market-income Gini minus disposable-income Gini; outcomes = bottom-40 income share or poverty-rate change, real GDP per capita growth, employment rate; controls = initial GDP per capita, age dependency, trade openness, unemployment.
   - Likely sources: OECD IDD, WDI, OWID/LIS distribution series.
   - Runability: READY_NOW.

2. `social_spending_market_poverty_reduction_elasticity_oecd`
   - School lens: `social_democratic`, `democratic_socialist`.
   - Testable claim: Higher social spending reduces market-income poverty more strongly where benefits are more cash-and-service universal, and the claim is weakened if poverty falls only through accounting transfers with no improvement in employment or material deprivation.
   - Measurable variables: treatment = OECD SOCX social spending by function and universality proxy; outcomes = market poverty, disposable poverty, material deprivation, employment rate; controls = GDP per capita, unemployment, age structure.
   - Likely sources: OECD SOCX, OECD IDD, Eurostat `ilc_mddd11`, WDI.
   - Runability: NEEDS_ALIAS.

3. `progressive_tax_top_income_share_and_growth_oecd`
   - School lens: `social_democratic`, `marxian`, `post_keynesian`.
   - Testable claim: Increases in top marginal income-tax rates lower top-income concentration without reducing medium-run GDP per capita growth or private investment more than matched lower-tax countries.
   - Measurable variables: treatment = top marginal income-tax rate; outcomes = top 1 percent and top 10 percent income shares, GDP per capita growth, gross fixed capital formation; controls = trade openness, initial income, inflation, demographics.
   - Likely sources: OWID top tax and top-income shares, WDI, PWT.
   - Runability: READY_NOW.

4. `public_health_spending_avoidable_mortality_panel`
   - School lens: `social_democratic`, `democratic_socialist`.
   - Testable claim: Higher public health spending reduces amenable mortality, infant mortality, and out-of-pocket burden after income and population-age controls; the claim is refuted if spending growth does not improve outcomes or only raises total cost.
   - Measurable variables: treatment = public health expenditure share of GDP or total health spending; outcomes = amenable mortality, infant mortality, life expectancy, out-of-pocket share; controls = GDP per capita, physicians, hospital beds, old-age dependency.
   - Likely sources: OECD Health, WDI, OWID health series.
   - Runability: READY_NOW.

5. `education_spending_low_income_attainment_mobility_panel`
   - School lens: `social_democratic`, `democratic_socialist`, `marxian`.
   - Testable claim: Higher public education spending predicts higher secondary and tertiary attainment among lower-income cohorts and lower intergenerational earnings persistence; a null or regressive attainment effect would refute the equal-opportunity claim.
   - Measurable variables: treatment = public education expenditure per student or share of GDP; outcomes = secondary completion, tertiary attainment, intergenerational earnings elasticity; controls = GDP per capita, urbanization, fertility, baseline attainment.
   - Likely sources: OECD education finance, WDI education indicators, OWID mobility.
   - Runability: NEEDS_ALIAS.

6. `unemployment_benefit_generosity_stabilizer_vs_duration_panel`
   - School lens: `social_democratic`, `post_keynesian`.
   - Testable claim: More generous unemployment benefits reduce household-income losses and recession depth, but the strongest claim is refuted if they materially lengthen unemployment duration after controlling for labor-demand shocks and activation spending.
   - Measurable variables: treatment = unemployment-benefit spending or replacement rate; outcomes = disposable-income loss, unemployment duration, GDP trough-to-recovery time, poverty; controls = output gap, EPL, ALMP spending, sector mix.
   - Likely sources: OECD SOCX, OECD TaxBEN replacement rates, OECD/ILOSTAT unemployment, WDI GDP.
   - Runability: NEEDS_ALIAS.

7. `child_family_benefits_female_lfp_fertility_panel`
   - School lens: `social_democratic`, `democratic_socialist`.
   - Testable claim: Childcare and family-benefit expansions raise female labor-force participation and fertility without lowering maternal employment; refuted if cash-only benefits reduce employment or fail to move fertility.
   - Measurable variables: treatment = family benefits and childcare/service spending; outcomes = female LFP, maternal employment, fertility, child poverty; controls = wages, unemployment, education, housing-cost burden.
   - Likely sources: OECD SOCX, WDI female LFP and fertility, Eurostat labor and poverty tables.
   - Runability: NEEDS_ALIAS.

8. `public_pension_generosity_elderly_poverty_fiscal_tradeoff`
   - School lens: `social_democratic`, `democratic_socialist`, `mmt`.
   - Testable claim: More generous public pensions lower elderly poverty and material deprivation, and the claim is weakened if gains are accompanied by persistent working-age tax wedges, debt-service stress, or lower employment.
   - Measurable variables: treatment = old-age public spending or pension replacement proxy; outcomes = elderly poverty, material deprivation, employment, fiscal balance, interest payments; controls = old-age dependency, GDP per capita, inflation.
   - Likely sources: OECD SOCX, OECD IDD, Eurostat `spr_exp_pens`, WDI fiscal and labor series.
   - Runability: NEEDS_ALIAS.

9. `decommodified_health_oop_spending_mortality_panel`
   - School lens: `democratic_socialist`, `social_democratic`.
   - Testable claim: Lower out-of-pocket health-spending shares predict lower avoidable mortality and less medical impoverishment after total health spending is controlled; refuted if decommodification has no independent outcome gain.
   - Measurable variables: treatment = out-of-pocket share of current health expenditure, public share of health expenditure; outcomes = infant mortality, amenable mortality, life expectancy, poverty headcount; controls = GDP per capita, total health expenditure, physicians.
   - Likely sources: WDI `SH.XPD.OOPC.CH.ZS`, WDI/OWID mortality and health expenditure, OECD amenable mortality.
   - Runability: READY_NOW.

10. `social_housing_share_rent_burden_supply_panel`
    - School lens: `democratic_socialist`, `social_democratic`.
    - Testable claim: Larger non-market social-housing stocks reduce rent overburden and homelessness without depressing total housing completions; refuted if supply falls enough to offset affordability gains.
    - Measurable variables: treatment = social-housing dwellings as share of stock; outcomes = rent-overburden rate, housing completions or permits, homelessness, overcrowding; controls = population growth, interest rates, zoning restrictiveness, income.
    - Likely sources: OECD Affordable Housing Database, Eurostat housing dashboard and permits, national housing statistics.
    - Runability: NEEDS_DATA.

11. `public_electricity_ownership_fossil_share_reduction`
    - School lens: `eco_socialist`, `democratic_socialist`, `market_socialist`.
    - Testable claim: Countries or utilities with larger public electricity ownership reduce fossil generation shares faster and maintain lower retail-price volatility than comparable privately owned systems.
    - Measurable variables: treatment = public ownership share of generation, transmission, or retail utilities; outcomes = fossil share of electricity, renewable share, outage frequency, price volatility; controls = hydro/nuclear endowment, fuel import dependence, GDP per capita.
    - Likely sources: IEA/Ember/OWID electricity mix, Eurostat power prices, national utility ownership datasets.
    - Runability: NEEDS_DATA.

12. `public_bank_credit_countercyclical_investment_panel`
    - School lens: `market_socialist`, `post_keynesian`, `mmt`.
    - Testable claim: Higher public-development-bank lending shares make credit and investment less procyclical during recessions without raising nonperforming loans in expansions.
    - Measurable variables: treatment = public development bank assets or lending share; outcomes = private investment growth, credit growth, NPL ratio, crisis incidence; controls = policy rates, credit gap, GDP growth, capital-account openness.
    - Likely sources: World Bank/IDB public development bank datasets, GFDD, BIS credit, Laeven-Valencia crises, WDI.
    - Runability: NEEDS_DATA.

13. `soe_share_manufacturing_productivity_tradeoff_panel`
    - School lens: `marxist_leninist`, `market_socialist`, `democratic_socialist`.
    - Testable claim: Higher state-owned-enterprise shares in strategic manufacturing raise investment and output stability but may lower TFP; the strong planning claim is supported only if productivity and stability both improve.
    - Measurable variables: treatment = SOE employment, asset, or value-added share by industry; outcomes = manufacturing value added, labor productivity, TFP, volatility, export upgrading; controls = capital intensity, trade openness, education, infrastructure.
    - Likely sources: OECD STAN, UNIDO INDSTAT, Chinese/National SOE accounts, WDI, PWT.
    - Runability: NEEDS_DATA.

14. `public_rail_investment_carbon_and_access_panel`
    - School lens: `eco_socialist`, `democratic_socialist`.
    - Testable claim: Public rail investment increases passenger rail use and lowers transport emissions per capita without worsening commute access for low-income regions.
    - Measurable variables: treatment = public rail capital spending or route-kilometers per capita; outcomes = passenger-km, transport CO2, car modal share, regional employment access; controls = urbanization, fuel prices, density, GDP per capita.
    - Likely sources: WDI rail passenger-km, ITF/OECD transport, Eurostat regional transport, OWID emissions.
    - Runability: NEEDS_DATA.

15. `resource_nationalization_revenue_social_outcomes_output_tradeoff`
    - School lens: `marxist_leninist`, `market_socialist`, `eco_socialist`.
    - Testable claim: Resource nationalization raises public revenue and social spending enough to improve health and education outcomes, while the claim is refuted if output, investment, or revenues fall relative to private or mixed regimes.
    - Measurable variables: treatment = nationalization episode or state equity share; outcomes = resource output, rents captured by government, health and education spending, mortality, enrollment; controls = commodity prices, reserves, conflict risk, governance.
    - Likely sources: resource nationalization event datasets, WDI resource rents and social indicators, IMF government finance, EIA/OPEC/USGS production data.
    - Runability: NEEDS_DATA.

16. `public_broadband_investment_digital_access_productivity`
    - School lens: `democratic_socialist`, `market_socialist`.
    - Testable claim: Public or municipal broadband investment increases household internet access and local productivity more in low-density or low-income areas than private-only rollout.
    - Measurable variables: treatment = municipal/public broadband coverage or subsidy intensity; outcomes = broadband adoption, internet use, firm productivity, employment, price per Mbps; controls = density, income, education, terrain.
    - Likely sources: FCC/Eurostat/OECD broadband, WDI internet use, national municipal network datasets.
    - Runability: NEEDS_DATA.

17. `cooperative_employment_wage_share_resilience_panel`
    - School lens: `market_socialist`, `democratic_socialist`, `marxian`.
    - Testable claim: Regions with larger cooperative employment shares have higher labor shares and smaller employment losses during downturns without lower productivity growth.
    - Measurable variables: treatment = cooperative employment or value-added share; outcomes = labor share, employment change in recessions, productivity, wage dispersion; controls = sector mix, union density, firm size, regional income.
    - Likely sources: CIRIEC/Euricse/CICOPA cooperative data, OECD regional accounts, OWID labor share, Eurostat labor data.
    - Runability: NEEDS_DATA.

18. `public_procurement_green_industry_learning_curve`
    - School lens: `eco_socialist`, `marxist_leninist`, `post_keynesian`.
    - Testable claim: Green public procurement and state-backed demand accelerate cost declines in solar, wind, batteries, or heat pumps beyond what cumulative global deployment alone predicts.
    - Measurable variables: treatment = public procurement volumes or contract-for-difference awards; outcomes = unit cost, domestic capacity, patents, export share; controls = cumulative deployment, input prices, exchange rates, R&D.
    - Likely sources: IRENA LCOE and capacity, WIPO patents, WITS exports, national procurement and auction datasets.
    - Runability: NEEDS_DATA.

19. `union_density_labor_share_inequality_growth_panel`
    - School lens: `marxian`, `social_democratic`, `post_keynesian`.
    - Testable claim: Higher union density raises labor share and lowers disposable-income inequality without reducing medium-run GDP per hour growth once sector composition is controlled.
    - Measurable variables: treatment = union density; outcomes = labor share, Gini, wage dispersion, GDP per hour growth; controls = trade exposure, unemployment, education, manufacturing share, EPL.
    - Likely sources: OECD TUD, OWID labor share and Gini, OECD PDB, WDI.
    - Runability: NEEDS_ALIAS.

20. `bargaining_coverage_low_wage_poverty_employment_panel`
    - School lens: `social_democratic`, `democratic_socialist`.
    - Testable claim: Higher collective-bargaining coverage lowers in-work poverty and low-wage incidence with no youth-employment penalty in coordinated systems, but is refuted if coverage mainly prices out young or low-skill workers.
    - Measurable variables: treatment = bargaining coverage and coordination proxy; outcomes = in-work poverty, low-wage share, youth employment, low-education unemployment; controls = minimum-wage bite, EPL, productivity, unemployment.
    - Likely sources: OECD CBC/TUD, OECD earnings, OECD low-education unemployment, Eurostat `ilc_iw01`.
    - Runability: NEEDS_ALIAS.

21. `codetermination_wage_share_productivity_investment_panel`
    - School lens: `democratic_socialist`, `market_socialist`.
    - Testable claim: Stronger worker board representation raises wage share and long-term investment without lowering TFP growth or firm survival.
    - Measurable variables: treatment = codetermination law strength or thresholds; outcomes = labor share, capex, TFP, wage dispersion, firm exits; controls = industry, firm size, export exposure, union density.
    - Likely sources: codetermination law datasets, OECD/Compustat/Orbis firm data, OECD PDB, EU KLEMS.
    - Runability: NEEDS_DATA.

22. `minimum_wage_bite_low_pay_poverty_employment_panel`
    - School lens: `social_democratic`, `democratic_socialist`, `marxian`.
    - Testable claim: Moderate minimum-wage bite increases low-end wages and reduces working poverty with employment effects near zero; refuted if high-bite settings show significant low-skill job losses.
    - Measurable variables: treatment = minimum wage to median or low-tail wage ratio; outcomes = low-wage share, working poverty, teen or low-education employment, hours; controls = unemployment, sector mix, inflation, productivity.
    - Likely sources: OECD MWUSD, derived minimum-wage bite panels, BLS/QCEW for US states, OECD low-education unemployment.
    - Runability: READY_NOW.

23. `epl_security_youth_unemployment_dualism_panel`
    - School lens: `social_democratic`, `democratic_socialist`.
    - Testable claim: Employment protection improves job security and tenure without creating youth/temporary-contract dualism only when active labor policy and growth are strong.
    - Measurable variables: treatment = EPL regular and temporary-contract indexes; outcomes = youth unemployment, low-education unemployment, temporary employment share, job tenure; controls = GDP growth, ALMP, bargaining coverage.
    - Likely sources: OECD EPL, OECD/ILOSTAT unemployment, Eurostat temporary-contract labor data.
    - Runability: READY_NOW.

24. `strike_activity_real_wage_followthrough_inflation_panel`
    - School lens: `marxian`, `post_keynesian`, `social_democratic`.
    - Testable claim: Higher strike activity predicts real-wage catch-up and labor-share gains without persistent inflation acceleration after productivity and slack are controlled.
    - Measurable variables: treatment = strike days per worker or strike incidence; outcomes = real wage growth, labor share, CPI inflation, unemployment; controls = productivity, output gap, import prices, union density.
    - Likely sources: ILO strike statistics, OECD earnings, OWID labor share, WDI inflation.
    - Runability: NEEDS_DATA.

25. `labor_share_demand_growth_wage_led_panel`
    - School lens: `marxian`, `post_keynesian`.
    - Testable claim: In demand-constrained high-income economies, rising labor share predicts stronger consumption and GDP growth, while profit-share gains predict weaker domestic demand.
    - Measurable variables: treatment = labor share of GDP; outcomes = household consumption growth, GDP growth, private investment, current account; controls = interest rates, trade openness, unemployment, credit growth.
    - Likely sources: OWID labor share, WDI national accounts, BIS credit, OECD PDB.
    - Runability: READY_NOW.

26. `shorter_hours_productivity_employment_wellbeing_panel`
    - School lens: `degrowth`, `democratic_socialist`, `post_keynesian`.
    - Testable claim: Reductions in annual hours worked raise hourly productivity and wellbeing without lowering employment rates when implemented in high-productivity economies.
    - Measurable variables: treatment = annual hours worked per worker; outcomes = GDP per hour, employment rate, Cantril life satisfaction, real GDP per capita; controls = initial productivity, sector mix, unemployment, union density.
    - Likely sources: OECD PDB, OWID happiness, WDI employment and GDP.
    - Runability: READY_NOW.

27. `public_investment_green_capacity_crowding_in_panel`
    - School lens: `post_keynesian`, `eco_socialist`, `mmt`.
    - Testable claim: Public investment crowds in renewable capacity and private investment during slack periods, but is refuted if higher public investment systematically displaces private capital without capacity gains.
    - Measurable variables: treatment = public gross fixed capital formation or green public investment; outcomes = renewable installed capacity, private investment share, GDP growth, employment; controls = interest rates, fiscal balance, energy demand, GDP per capita.
    - Likely sources: IMF public investment, WDI investment, IRENA capacity, Eurostat government capital expenditure.
    - Runability: NEEDS_ALIAS.

28. `industrial_policy_hightech_exports_patents_panel`
    - School lens: `marxist_leninist`, `market_socialist`, `post_keynesian`.
    - Testable claim: Mission-oriented industrial policy raises high-tech export shares and resident patenting after five to ten years, with support only if gains exceed general R&D and education trends.
    - Measurable variables: treatment = targeted industrial-policy subsidy, public R&D, or strategic-sector support; outcomes = high-tech exports, resident patents, manufacturing value added, productivity; controls = education, exchange rates, trade openness, baseline complexity.
    - Likely sources: WDI R&D and high-tech exports, WIPO/OECD patents, WITS, industrial-policy datasets.
    - Runability: NEEDS_ALIAS.

29. `directed_credit_manufacturing_upgrade_financial_risk_panel`
    - School lens: `marxist_leninist`, `market_socialist`, `post_keynesian`.
    - Testable claim: Directed credit to manufacturing increases upgrading and export complexity, but the claim is refuted if credit allocation raises NPLs and crisis risk without productivity gains.
    - Measurable variables: treatment = directed or policy-bank credit to priority sectors; outcomes = manufacturing productivity, high-tech exports, NPL ratio, credit gap, banking-crisis indicator; controls = exchange rate, global demand, governance, capital controls.
    - Likely sources: national credit-allocation data, BIS, GFDD, WITS, WDI, Laeven-Valencia.
    - Runability: NEEDS_DATA.

30. `capital_controls_crisis_volatility_growth_panel`
    - School lens: `post_keynesian`, `mmt`, `market_socialist`.
    - Testable claim: More restrictive capital-account regimes reduce crisis incidence and exchange-rate volatility without lowering long-run investment or GDP growth in emerging markets.
    - Measurable variables: treatment = Chinn-Ito capital-account openness index; outcomes = banking/currency crises, exchange-rate volatility, investment share, GDP per capita growth; controls = reserves, current account, inflation, commodity terms of trade.
    - Likely sources: Chinn-Ito, Laeven-Valencia, BIS EER, WDI, IMF.
    - Runability: READY_NOW.

31. `rent_control_supply_affordability_tradeoff_panel`
    - School lens: `democratic_socialist`, `social_democratic`.
    - Testable claim: Rent-control expansions lower rent burden for incumbent tenants without reducing new supply or mobility; the strong claim is refuted if permits, completions, or vacancy rates fall persistently.
    - Measurable variables: treatment = rent-control stringency or expansion events; outcomes = rent burden, permits, completions, mobility, homelessness; controls = population growth, income, interest rates, zoning constraints.
    - Likely sources: national rent-control law panels, Eurostat housing costs and construction permits, OECD housing dashboard.
    - Runability: NEEDS_DATA.

32. `food_price_controls_inflation_nutrition_supply_panel`
    - School lens: `marxist_leninist`, `democratic_socialist`.
    - Testable claim: Food price controls reduce food inflation and food insecurity without reducing domestic food supply; refuted if shortages or production declines dominate.
    - Measurable variables: treatment = food price-control episodes or administered-price coverage; outcomes = food CPI, food production index, undernourishment, import dependence, queue or shortage proxies; controls = harvest shocks, exchange rate, global food prices.
    - Likely sources: IMF price-control datasets, FAOSTAT, WDI food production, national CPI, World Food Programme.
    - Runability: NEEDS_DATA.

33. `fiscal_expansion_slack_unemployment_recovery_panel`
    - School lens: `post_keynesian`, `mmt`, `social_democratic`.
    - Testable claim: Fiscal expansions during high-slack years reduce unemployment and accelerate GDP recovery more than expansions near capacity, with no persistent inflation overshoot unless supply constraints bind.
    - Measurable variables: treatment = change in government consumption or cyclically adjusted balance proxy interacted with slack; outcomes = unemployment, GDP growth, inflation; controls = monetary policy, external demand, debt, energy prices.
    - Likely sources: WDI fiscal and macro series, IMF WEO/GFS, OECD national accounts.
    - Runability: READY_NOW.

34. `austerity_after_recession_hysteresis_panel`
    - School lens: `post_keynesian`, `social_democratic`, `mmt`.
    - Testable claim: Fiscal consolidation within three years after recessions lowers employment and potential-output paths relative to countries that delay consolidation until recovery.
    - Measurable variables: treatment = post-recession change in fiscal balance, government consumption, or expenditure share; outcomes = employment rate, GDP per capita level, unemployment hysteresis, investment; controls = debt, crisis severity, trade shock, monetary stance.
    - Likely sources: WDI fiscal and labor series, IMF fiscal monitor, OECD PDB, Laeven-Valencia.
    - Runability: READY_NOW.

35. `sovereign_currency_debt_inflation_threshold_panel`
    - School lens: `mmt`, `post_keynesian`.
    - Testable claim: For monetary sovereigns with floating exchange rates and debt in domestic currency, high public-debt ratios do not predict inflation or default absent real-resource or external-balance stress.
    - Measurable variables: treatment = public debt to GDP interacted with currency sovereignty and external-debt share; outcomes = CPI inflation, sovereign stress/default, interest burden, exchange-rate depreciation; controls = output gap, current account, import prices, reserves.
    - Likely sources: WDI/IMF debt and inflation, Reinhart-Rogoff or BoC default data, IMF AREAER exchange-rate regimes, external-debt currency composition.
    - Runability: NEEDS_ALIAS.

36. `central_bank_asset_purchases_yields_inflation_panel`
    - School lens: `mmt`, `post_keynesian`.
    - Testable claim: Large central-bank government-bond purchases lower long yields without producing proportional CPI inflation when unemployment is above pre-crisis levels.
    - Measurable variables: treatment = central-bank sovereign asset purchases or balance-sheet expansion; outcomes = 10-year yield, CPI inflation, unemployment, exchange rate; controls = fiscal deficit, policy rate, commodity prices, inflation expectations.
    - Likely sources: FRED, ECB, BOJ, BOE, BIS policy rates, WDI inflation and unemployment.
    - Runability: NEEDS_ALIAS.

37. `job_guarantee_almp_unemployment_floor_panel`
    - School lens: `mmt`, `democratic_socialist`, `social_democratic`.
    - Testable claim: Public employment or activation-heavy labor-market programs lower long-term unemployment and poverty more than passive transfers at similar fiscal cost.
    - Measurable variables: treatment = public employment program intensity or ALMP spending share; outcomes = long-term unemployment, poverty, labor-force participation, inflation; controls = recession depth, benefit generosity, EPL, demographics.
    - Likely sources: OECD SOCX/ALMP, ILOSTAT unemployment duration, WDI labor series, national public-employment program data.
    - Runability: NEEDS_ALIAS.

38. `automatic_stabilizers_recession_depth_recovery_panel`
    - School lens: `social_democratic`, `post_keynesian`.
    - Testable claim: Larger automatic stabilizers reduce peak-to-trough GDP losses and poverty spikes during recessions, but may trade off against recovery speed if labor-market reentry is weak.
    - Measurable variables: treatment = social spending response to unemployment, tax-transfer redistribution gap, replacement-rate proxy; outcomes = recession depth, poverty change, unemployment persistence, recovery time; controls = shock type, monetary stance, openness, debt.
    - Likely sources: OECD SOCX, OECD IDD, WDI GDP/unemployment/poverty, Eurostat poverty.
    - Runability: NEEDS_ALIAS.

39. `deficits_private_saving_sectoral_balance_panel`
    - School lens: `mmt`, `post_keynesian`.
    - Testable claim: Government deficits are associated with higher private-sector net saving, especially when current-account balances are stable; the claim is refuted if private saving does not co-move after accounting identities and valuation changes are handled.
    - Measurable variables: treatment = fiscal balance to GDP; outcomes = derived private-sector balance, household saving, investment, current account; controls = GDP growth, credit cycle, inflation, capital-account openness.
    - Likely sources: WDI fiscal balance and current account, OECD national accounts, IMF sectoral accounts.
    - Runability: NEEDS_ALIAS.

40. `policy_rate_hikes_labor_share_distribution_panel`
    - School lens: `post_keynesian`, `marxian`.
    - Testable claim: Monetary tightening reduces labor share and wage growth more than profit income during disinflation episodes, implying a distributional cost channel.
    - Measurable variables: treatment = policy-rate increase or real-rate shock; outcomes = labor share, real wage growth, unemployment, inflation, profit share proxy; controls = import prices, credit gap, fiscal stance, output gap.
    - Likely sources: BIS central-bank policy rates, OECD earnings, OWID labor share, WDI inflation/unemployment.
    - Runability: READY_NOW.

41. `public_green_spending_renewables_co2_intensity_panel`
    - School lens: `eco_socialist`, `post_keynesian`, `mmt`.
    - Testable claim: Public green spending lowers CO2 intensity and raises renewable capacity faster than carbon-price-only strategies at similar income levels.
    - Measurable variables: treatment = public climate spending or green-investment share; outcomes = CO2 intensity, renewable capacity, fossil electricity share, electricity prices; controls = carbon price, fossil endowment, GDP per capita, energy demand.
    - Likely sources: OECD/IMF climate spending, IRENA capacity, OWID emissions and electricity mix, Eurostat power prices.
    - Runability: NEEDS_DATA.

42. `fossil_subsidy_phaseout_emissions_poverty_tradeoff_panel`
    - School lens: `eco_socialist`, `degrowth`, `social_democratic`.
    - Testable claim: Fossil-fuel subsidy reductions lower emissions intensity only when paired with household compensation; otherwise they raise poverty or energy stress enough to weaken the just-transition claim.
    - Measurable variables: treatment = fossil-fuel consumption subsidy share and phaseout episodes; outcomes = CO2 intensity, fossil-energy use, poverty, household energy burden, inflation; controls = oil prices, income, exchange rates, social spending.
    - Likely sources: OWID fossil subsidies, WDI/OWID emissions and poverty, Eurostat energy prices, IMF subsidy data.
    - Runability: READY_NOW.

43. `renewable_capacity_employment_transition_panel`
    - School lens: `eco_socialist`, `social_democratic`.
    - Testable claim: Renewable-capacity growth increases net employment or prevents industrial-employment loss in regions with transition policy, while the claim is refuted if capacity growth coincides with persistent employment losses.
    - Measurable variables: treatment = solar/wind/renewable installed capacity per capita; outcomes = total employment, industrial employment, unemployment, manufacturing value added; controls = GDP growth, energy prices, trade exposure, fossil-sector employment.
    - Likely sources: IRENA capacity, WDI/ILOSTAT employment, Eurostat regional labor, WDI manufacturing value added.
    - Runability: READY_NOW.

44. `material_footprint_wellbeing_decoupling_high_income_panel`
    - School lens: `degrowth`, `eco_socialist`.
    - Testable claim: In high-income countries, material footprint per capita can fall while life expectancy and life satisfaction are maintained or improved; refuted if footprint reductions systematically require welfare losses outside recession years.
    - Measurable variables: treatment = material footprint per capita change; outcomes = life expectancy, Cantril ladder, unemployment, poverty, GDP per capita; controls = recession indicator, energy prices, inequality, public spending.
    - Likely sources: OWID material footprint, OWID happiness/life expectancy, WDI unemployment and poverty, PWT.
    - Runability: READY_NOW.

45. `degrowth_recession_basic_needs_protection_panel`
    - School lens: `degrowth`, `eco_socialist`, `democratic_socialist`.
    - Testable claim: Output or energy-use contractions do not have to reduce basic-needs outcomes when health, education, and food-security institutions are protected; refuted if contractions reliably worsen mortality, schooling, or poverty even under high public provision.
    - Measurable variables: treatment = GDP per capita or energy-use contraction episodes; moderator = public health/education/social spending; outcomes = infant mortality, life expectancy, school enrollment, poverty, food production; controls = conflict, sanctions, commodity prices, initial income.
    - Likely sources: WDI GDP/energy/social indicators, OWID health, FAOSTAT/WDI food production, UCDP conflict.
    - Runability: READY_NOW.

46. `working_time_reduction_energy_use_per_capita_panel`
    - School lens: `degrowth`, `democratic_socialist`.
    - Testable claim: Lower annual hours worked reduce energy use and emissions per capita without proportionate reductions in life satisfaction or employment.
    - Measurable variables: treatment = annual hours worked or statutory working-time reductions; outcomes = energy use per capita, CO2 per capita, employment rate, life satisfaction, GDP per capita; controls = productivity, energy mix, income, unemployment.
    - Likely sources: OECD PDB hours, WDI energy, OWID emissions and happiness, ILOSTAT employment.
    - Runability: READY_NOW.

47. `protected_land_food_security_emissions_panel`
    - School lens: `eco_socialist`, `degrowth`.
    - Testable claim: Expanding protected land lowers land-use emissions or forest loss without reducing food production per capita in countries with adequate yield growth.
    - Measurable variables: treatment = protected land share; outcomes = forest share, food production index, agricultural value added, undernourishment proxy, CO2 intensity; controls = rainfall, rural population, fertilizer use proxy, GDP per capita.
    - Likely sources: WDI protected land, forest and food production series, FAOSTAT, OWID emissions.
    - Runability: READY_NOW.

48. `urban_public_transit_carbon_and_access_panel`
    - School lens: `eco_socialist`, `democratic_socialist`.
    - Testable claim: Public transit expansion lowers per-capita transport emissions and improves job access for lower-income neighborhoods, rather than simply shifting riders from walking or cycling.
    - Measurable variables: treatment = transit service-km, station access, or public transit capital spending; outcomes = transport CO2, commute time, car modal share, employment access; controls = density, fuel prices, income, urban form.
    - Likely sources: ITF/OECD transport, Eurostat urban audit, GTFS-derived transit access, national transport emissions.
    - Runability: NEEDS_DATA.

49. `financialization_labor_share_investment_panel`
    - School lens: `marxian`, `post_keynesian`, `social_democratic`.
    - Testable claim: Higher private-credit depth and financial-sector value-added shares predict lower labor shares and weaker real investment after credit booms, supporting financialization critiques if robust.
    - Measurable variables: treatment = private credit to GDP, credit gap, finance value-added share; outcomes = labor share, gross fixed capital formation, productivity growth, wage growth; controls = policy rates, GDP growth, trade openness, crisis indicators.
    - Likely sources: BIS credit and credit gap, GFDD/WDI private credit, Eurostat sectoral accounts, OWID labor share, WDI investment.
    - Runability: READY_NOW.

50. `macroprudential_credit_controls_house_price_stability_panel`
    - School lens: `post_keynesian`, `market_socialist`, `social_democratic`.
    - Testable claim: Binding macroprudential credit controls reduce house-price booms and later bust unemployment without shifting risk into unregulated credit.
    - Measurable variables: treatment = LTV/DTI limits, countercyclical capital buffers, or credit-growth caps; outcomes = real house prices, household credit growth, unemployment after busts, nonbank credit share; controls = interest rates, income growth, housing supply, capital inflows.
    - Likely sources: IMF iMaPP macroprudential database, BIS house prices and credit, WDI unemployment, national nonbank-credit data.
    - Runability: NEEDS_DATA.

## Best Immediate Run Candidates

Best first-pass candidates because their core treatment and outcome data are
already local or nearly local:

- `redistribution_gap_bottom40_real_income_growth_oecd`
- `progressive_tax_top_income_share_and_growth_oecd`
- `public_health_spending_avoidable_mortality_panel`
- `decommodified_health_oop_spending_mortality_panel`
- `minimum_wage_bite_low_pay_poverty_employment_panel`
- `epl_security_youth_unemployment_dualism_panel`
- `labor_share_demand_growth_wage_led_panel`
- `shorter_hours_productivity_employment_wellbeing_panel`
- `capital_controls_crisis_volatility_growth_panel`
- `fiscal_expansion_slack_unemployment_recovery_panel`
- `austerity_after_recession_hysteresis_panel`
- `policy_rate_hikes_labor_share_distribution_panel`
- `fossil_subsidy_phaseout_emissions_poverty_tradeoff_panel`
- `renewable_capacity_employment_transition_panel`
- `material_footprint_wellbeing_decoupling_high_income_panel`
- `degrowth_recession_basic_needs_protection_panel`
- `working_time_reduction_energy_use_per_capita_panel`
- `financialization_labor_share_investment_panel`
