# Swarm 2026-05-22 Worker C - State Capacity Mixed Conditionality

Scope: 50 falsifiable candidate hypotheses for the mixed/contingent schools:
developmentalism, institutionalism, new_keynesian, post_keynesian, mmt, and
empirical_pragmatist, with ordoliberal and classical_liberal contrasts where
the test naturally distinguishes market-complementing state capacity from
state drag. School labels are not data and should never enter a regression;
they only describe which predictions the evidence may later map to after QA.

Runability flags:

- `READY_NOW`: enough local source coverage appears present for a first-pass
  generic or light bespoke run.
- `NEEDS_ALIAS`: source family is present or public, but the local alias,
  constructed treatment, or runner mapping needs work.
- `NEEDS_DATA`: credible test needs an outside policy/event/micro source not
  yet clearly local.

## Candidate Backlog

### Macro / Fiscal Conditionality

1. `capacity_stabilizers_output_loss_threshold_oecd`
   - Claim: In OECD recessions from 1980-2024, larger automatic stabilizers cushion two-year GDP and employment losses only where government effectiveness is above the sample median; where effectiveness is low, the same spending share predicts slower debt repair without a measurable unemployment cushion.
   - Variables: automatic stabilizer/social spending share, unemployment-benefit spending, WGI government effectiveness, recession indicator, GDP drawdown, unemployment change, gross debt change.
   - Likely data sources: OECD SOCX, WDI/IMF WEO, WGI, OECD/ILOSTAT unemployment.
   - Runability: `READY_NOW`.

2. `capacity_fiscal_expansion_slack_inflation_tradeoff`
   - Claim: Discretionary fiscal expansion raises real output with limited inflation when unemployment is above its country-specific 10-year mean, but the output gain shrinks and inflation pass-through rises when unemployment is below that slack threshold.
   - Variables: cyclically adjusted fiscal balance or government consumption impulse, unemployment gap, real GDP growth, CPI inflation, output gap proxies, trade openness.
   - Likely data sources: IMF WEO, WDI, ILOSTAT, OECD PDB for advanced-economy robustness.
   - Runability: `NEEDS_ALIAS`.

3. `capacity_public_investment_execution_private_capital_complement`
   - Claim: Public investment complements private investment and productivity only in high-execution states; in low government-effectiveness states, higher public capital formation predicts weaker private investment shares and no TFP improvement.
   - Variables: public investment share or gross fixed capital formation by government, private investment share, PWT TFP, WGI government effectiveness/control of corruption, initial GDP per capita.
   - Likely data sources: IMF WEO/GFS if available, WDI gross capital formation proxies, PWT, WGI.
   - Runability: `NEEDS_ALIAS`.

4. `capacity_currency_issuer_debt_inflation_external_constraint`
   - Claim: High public debt is not by itself inflationary for monetary sovereigns with mostly local-currency debt and low external constraint, but debt-inflation and yield stress appear when current-account deficits and foreign-currency liabilities are high.
   - Variables: debt/GDP, inflation, long-term yields if available, current-account balance, FX reserves, exchange-rate depreciation, currency-issuer/user classification, external-debt or FX-debt share.
   - Likely data sources: IMF WEO, WDI, BIS exchange rates, IMF IFS/external debt, OECD/ECB for yields.
   - Runability: `NEEDS_DATA`.

5. `capacity_fiscal_rules_investment_protection_vs_austerity_drag`
   - Claim: Fiscal rules improve long-run debt dynamics without growth loss when they protect public investment and allow cyclical escape clauses; strict nominal-deficit rules without investment protection predict lower public investment and weaker five-year GDP-per-hour growth after shocks.
   - Variables: fiscal-rule design, public investment, cyclicality of fiscal balance, GDP/hour growth, debt/GDP, recession episodes.
   - Likely data sources: IMF Fiscal Rules Dataset, IMF WEO/GFS, OECD PDB.
   - Runability: `NEEDS_DATA`.

6. `capacity_tax_revenue_public_goods_threshold`
   - Claim: Higher tax revenue supports growth and poverty reduction when tax collection capacity and rule of law are high; above similar revenue shares in low-capacity states, marginal revenue predicts lower private investment and no poverty improvement.
   - Variables: tax revenue/GDP, WGI rule of law/control of corruption, public investment or health/education spending, private investment, poverty headcount, GDP per capita growth.
   - Likely data sources: WDI, WGI, IMF/OECD Revenue Statistics where available.
   - Runability: `READY_NOW`.

7. `capacity_government_consumption_vs_investment_composition`
   - Claim: Government size only drags growth when the marginal increase is government consumption or wage-bill heavy; public investment-heavy expansions in high-capacity states have neutral or positive five-year productivity effects.
   - Variables: government consumption/GDP, public investment proxy, compensation/wage-bill proxy, GDP per capita growth, PWT TFP, WGI government effectiveness.
   - Likely data sources: WDI, IMF WEO/GFS, PWT, WGI.
   - Runability: `NEEDS_ALIAS`.

8. `capacity_zlb_fiscal_monetary_coordination_vs_dominance`
   - Claim: Fiscal-monetary coordination is expansionary without sustained inflation at the zero lower bound when central-bank credibility is high and slack is large; outside slack/ZLB regimes, repeated fiscal accommodation predicts inflation persistence.
   - Variables: policy rate near zero, fiscal impulse, unemployment gap, inflation persistence, central-bank independence proxy, debt/GDP, output growth.
   - Likely data sources: BIS policy rates, IMF WEO, WDI inflation, Garriga/Cukierman CBI data if local or fetched.
   - Runability: `NEEDS_DATA`.

### Industrial Policy

9. `capacity_export_discipline_selective_credit_success`
   - Claim: Selective credit and sector targeting raise export complexity and manufacturing productivity only when subsidies are tied to export-performance discipline; untied import-substitution targeting predicts lower export diversity and weaker productivity.
   - Variables: directed-credit/industrial-policy episodes, export-performance targets, export product concentration/diversity, high-tech exports, manufacturing value added per worker, productivity growth.
   - Likely data sources: WITS, WDI high-tech/manufacturing, UNIDO/STAN/KLEMS, historical policy coding.
   - Runability: `NEEDS_DATA`.

10. `capacity_hightech_exports_government_effectiveness_interaction`
   - Claim: Industrial-policy intensity proxies such as R&D spending or high-tech export targeting predict durable high-tech export shares only above a government-effectiveness threshold; below it, the same policy intensity predicts concentration without upgrading.
   - Variables: R&D spending, high-tech exports share, export concentration HHI, WGI government effectiveness, tertiary enrolment, FDI share.
   - Likely data sources: WDI, WITS/derived export concentration, WGI.
   - Runability: `READY_NOW`.

11. `capacity_tariff_sunset_infant_industry_upgrade`
   - Claim: Infant-industry protection works when tariffs are temporary and followed by export-share gains; persistent tariffs without export discipline predict lower consumption growth and no high-tech export upgrading.
   - Variables: applied tariff rates, tariff-duration spells, export value/variety, high-tech export share, private consumption per capita, GDP growth.
   - Likely data sources: WITS tariff and trade vintages, WDI consumption and high-tech exports.
   - Runability: `READY_NOW`.

12. `capacity_fdi_screening_absorptive_capability`
   - Claim: FDI screening and local-content rules improve domestic value-added upgrading only where human capital and rule of law exceed threshold levels; otherwise they reduce FDI inflows without measurable productivity gains.
   - Variables: FDI inflows, local-content/screening policy episodes, human capital/tertiary enrolment, rule of law, manufacturing value added, TFP growth.
   - Likely data sources: WDI, WGI, PWT, OECD FDI restrictiveness or policy coding.
   - Runability: `NEEDS_DATA`.

13. `capacity_green_industrial_policy_electricity_price_tradeoff`
   - Claim: Green industrial policy complements markets when it lowers renewable costs or deployment without raising industrial electricity prices; where grid integration capacity is weak, higher renewable shares predict manufacturing-share losses through energy-price channels.
   - Variables: renewable capacity/share, industrial electricity prices, manufacturing value-added share, grid reliability/proxy, public support intensity, GDP/hour.
   - Likely data sources: IRENA, Eurostat electricity prices, WDI energy/manufacturing, IEA/ENTSO-E for reliability.
   - Runability: `NEEDS_ALIAS`.

14. `capacity_soe_hard_budget_competition_productivity`
   - Claim: State-owned enterprise presence is not necessarily productivity-damaging when hard-budget constraints and competition are high; high SOE presence with weak competition predicts lower sector productivity and higher fiscal contingent liabilities.
   - Variables: SOE share by sector, product-market competition, sector productivity, subsidies/transfers, fiscal balance, WGI regulatory quality.
   - Likely data sources: OECD PMR/SOE indicators, OECD STAN/PDB, IMF fiscal data, WGI.
   - Runability: `NEEDS_DATA`.

15. `capacity_public_procurement_rnd_diffusion`
   - Claim: Public procurement raises innovation spillovers when procurement transparency is high and contracts are contestable; opaque procurement predicts higher public spending without patenting or productivity gains.
   - Variables: procurement spending/transparency, patent applications, R&D spending, entry rates, productivity growth, corruption control.
   - Likely data sources: World Bank procurement/B-READY, WDI patents/R&D/business entry, WGI control of corruption.
   - Runability: `NEEDS_DATA`.

### State Capacity / Institutional Mechanisms

16. `capacity_government_effectiveness_state_size_nonmonotonic`
   - Claim: Government spending has a nonmonotonic relationship with growth: moderate-to-large spending is compatible with growth in high-effectiveness states, while similarly large spending in low-effectiveness states predicts lower private investment and slower GDP per capita growth.
   - Variables: government expenditure/consumption share, WGI government effectiveness, private investment, GDP per capita growth, trade openness, initial income.
   - Likely data sources: WDI, WGI, PWT.
   - Runability: `READY_NOW`.

17. `capacity_regulatory_quality_business_entry_complement`
   - Claim: Regulation complements markets when regulatory quality is high: higher regulatory quality predicts more business entry and less informality; high procedural burden with low regulatory quality predicts lower entry and weaker employment growth.
   - Variables: WGI regulatory quality, business registrations, permit/procedure burden if available, employment rate, informality proxy, GDP growth.
   - Likely data sources: WGI, WDI business registrations, B-READY/Doing Business, ILOSTAT.
   - Runability: `NEEDS_ALIAS`.

18. `capacity_corruption_public_investment_leakage`
   - Claim: Public investment raises infrastructure and growth outcomes only where corruption control is high; where corruption control is low, higher public investment predicts debt accumulation without road, electricity, or growth gains.
   - Variables: public investment/gross capital formation, WGI control of corruption, road density/electricity access, debt/GDP, GDP per capita growth.
   - Likely data sources: WDI, WGI, IMF WEO/GFS.
   - Runability: `READY_NOW`.

19. `capacity_rule_of_law_financial_depth_productive_allocation`
   - Claim: Financial depth supports productivity and innovation only under strong rule of law; in weak-rule-of-law settings, private credit growth predicts credit booms and asset prices more than TFP or patenting.
   - Variables: private credit/GDP, rule of law, TFP growth, patents, BIS credit gap, BIS house prices, investment share.
   - Likely data sources: WDI/GFDD, WGI, PWT, UN patents, BIS credit/house prices.
   - Runability: `READY_NOW`.

20. `capacity_tax_administration_social_spending_poverty_elasticity`
   - Claim: Social spending reduces poverty more strongly when tax administration and corruption control are high; in weak-capacity states, spending growth has lower poverty elasticity and higher fiscal slippage.
   - Variables: social spending or social-protection coverage, tax revenue/GDP, corruption control, poverty headcount, fiscal balance, Gini.
   - Likely data sources: OECD SOCX for OECD, WDI social-protection/poverty/tax/fiscal variables, WGI.
   - Runability: `READY_NOW`.

21. `capacity_trade_liberalization_institutional_variance`
   - Claim: Tariff reductions increase consumption and export variety in high-rule-of-law and high-human-capital countries, but generate weak or negative medium-run growth in low-capacity countries with shallow finance.
   - Variables: tariff reductions, rule of law, tertiary enrolment/human capital, private credit, consumption per capita, export variety/concentration, GDP growth.
   - Likely data sources: WITS, WDI, WGI, PWT.
   - Runability: `READY_NOW`.

22. `capacity_digital_government_formalization_channel`
   - Claim: Digital public administration complements markets by raising formal business entry and tax compliance where connectivity is high; digitization without broadband penetration or legal credibility does not raise formalization.
   - Variables: e-government/digital ID adoption, internet users/broadband, business registrations, tax revenue/GDP, regulatory quality, employment.
   - Likely data sources: UN E-Government Survey, WDI internet/business/tax variables, WGI.
   - Runability: `NEEDS_DATA`.

### Public Goods / Human Capital

23. `capacity_education_spending_learning_threshold`
   - Claim: Education spending raises human capital and later productivity only where governance quality and teacher/system capacity are high; spending alone is weakly related to outcomes in low-capacity systems.
   - Variables: education spending/GDP, school completion/enrolment, human capital index, GDP/hour or TFP, WGI government effectiveness.
   - Likely data sources: WDI, PWT human capital, OECD PDB for advanced economies, WGI.
   - Runability: `READY_NOW`.

24. `capacity_health_spending_mortality_corruption_interaction`
   - Claim: Public health spending reduces mortality and raises life expectancy when corruption control is high; low corruption-control states show weaker health outcome gains per spending point.
   - Variables: health spending/GDP or per capita, mortality, life expectancy, physician density, out-of-pocket share, corruption control.
   - Likely data sources: WDI health variables, WGI control of corruption.
   - Runability: `READY_NOW`.

25. `capacity_electricity_access_regulatory_quality`
   - Claim: Public electrification complements private-sector growth when regulatory quality is high; in low-regulatory-quality states, electricity access expansions show weaker links to manufacturing value added and business entry.
   - Variables: electricity access/use, regulatory quality, manufacturing share, business registrations, GDP per capita growth.
   - Likely data sources: WDI, WGI.
   - Runability: `READY_NOW`.

26. `capacity_water_sanitation_urbanization_health_dividend`
   - Claim: Urban infrastructure investment lowers mortality and supports urban productivity only when municipal/state capacity is high; rapid urbanization without service delivery predicts worse health and weaker productivity.
   - Variables: urbanization, water/sanitation access, mortality, GDP per worker or GDP/hour, government effectiveness.
   - Likely data sources: WDI, WGI, OECD PDB/PWT.
   - Runability: `NEEDS_ALIAS`.

27. `capacity_rnd_spending_finance_patent_productivity`
   - Claim: R&D spending converts into patenting and productivity only when private finance and regulatory quality are adequate; otherwise R&D intensity is weakly associated with innovation outcomes.
   - Variables: R&D/GDP, patents, private credit/GDP, regulatory quality, TFP, high-tech exports.
   - Likely data sources: WDI, UN patents, GFDD/WDI private credit, WGI, PWT.
   - Runability: `READY_NOW`.

28. `capacity_activation_spending_unemployment_duration`
   - Claim: Active labour-market spending reduces long-term unemployment only where case-management capacity and benefit conditionality are strong; passive benefit generosity without activation predicts longer unemployment duration.
   - Variables: ALMP spending, passive unemployment benefits, sanction/conditionality proxy, government effectiveness, long-term unemployment or unemployment duration, low-education unemployment.
   - Likely data sources: OECD SOCX/ALMP, OECD labour indicators, ILOSTAT, WGI.
   - Runability: `NEEDS_ALIAS`.

### Crisis Response

29. `capacity_gfc_stimulus_speed_output_recovery`
   - Claim: During the 2008-2012 crisis, faster fiscal stimulus in high-capacity states predicted smaller employment losses and faster GDP recovery; in low-capacity/high-debt states, stimulus size had weaker recovery payoff and worse sovereign-risk outcomes.
   - Variables: fiscal impulse, implementation speed, WGI government effectiveness, debt/GDP, GDP recovery, unemployment change, bond spreads where available.
   - Likely data sources: IMF WEO, WDI/ILOSTAT, WGI, OECD/ECB spreads.
   - Runability: `NEEDS_ALIAS`.

30. `capacity_pandemic_job_retention_targeting`
   - Claim: Covid job-retention and wage-subsidy schemes preserved employment with less inflation/fiscal leakage where targeting and administrative capacity were high; broad untargeted transfers produced weaker employment preservation per fiscal point.
   - Variables: job-retention uptake/spending, transfer spending, administrative capacity, employment loss/rebound, inflation, debt change.
   - Likely data sources: OECD Covid policy trackers, IMF fiscal monitor, ILOSTAT, WDI, WGI.
   - Runability: `NEEDS_DATA`.

31. `capacity_energy_shock_transfers_vs_price_controls`
   - Claim: Energy-shock relief works better as targeted transfers or temporary tax smoothing in high-capacity states; administered price controls/subsidies predict shortages, fiscal slippage, or lower investment where pass-through is suppressed for long periods.
   - Variables: energy-price shock, targeted transfers, fuel/energy subsidies or price controls, household electricity prices, fiscal balance, energy consumption/investment, inflation.
   - Likely data sources: Eurostat electricity prices, IMF/OECD fossil-fuel support, WDI energy, IMF WEO.
   - Runability: `NEEDS_ALIAS`.

32. `capacity_disaster_reconstruction_public_investment_multiplier`
   - Claim: Post-disaster reconstruction spending restores output faster when procurement and corruption-control measures are strong; similar spending in weak-capacity states predicts higher debt with slower infrastructure recovery.
   - Variables: disaster severity, public reconstruction spending, procurement/corruption controls, road/electricity restoration, GDP recovery, debt.
   - Likely data sources: EM-DAT, WDI, WGI, IMF disaster/fiscal databases.
   - Runability: `NEEDS_DATA`.

33. `capacity_imf_program_ownership_social_spending_tradeoff`
   - Claim: IMF programs stabilize inflation and external balances with less poverty and growth damage when domestic ownership and social-spending floors are credible; programs without these features show larger output and social costs.
   - Variables: IMF program episodes, prior fiscal/external stress, social spending floors, inflation, current account, GDP growth, poverty/unemployment.
   - Likely data sources: IMF MONA/program data, IMF WEO, WDI poverty/unemployment, WGI.
   - Runability: `NEEDS_DATA`.

34. `capacity_capital_controls_temporary_crisis_stabilizer`
   - Claim: Temporary capital controls during acute currency crises reduce reserve loss and output collapse when paired with credible exit and macro adjustment; persistent controls outside crisis windows predict lower investment and financial depth.
   - Variables: capital-control episodes/intensity, reserves, exchange-rate depreciation, investment share, private credit, GDP growth, crisis indicator.
   - Likely data sources: IMF AREAER/Chinn-Ito, WDI, BIS exchange rates, IMF WEO.
   - Runability: `NEEDS_DATA`.

35. `capacity_food_price_shock_safety_nets_vs_export_bans`
   - Claim: Food-price shocks are better absorbed by targeted safety nets and buffer-stock release in administratively capable states; export bans and broad price controls increase domestic volatility or reduce producer incentives over the following seasons.
   - Variables: food price index, safety-net spending/coverage, export-ban episodes, agricultural output, domestic food inflation, poverty.
   - Likely data sources: FAOSTAT, WDI agriculture/poverty, IMF commodity prices, WITS trade restrictions if coded.
   - Runability: `NEEDS_DATA`.

### Financial Stability

36. `capacity_macroprudential_credit_gap_buffer`
   - Claim: Credit gaps predict weaker future output and house-price reversals, but the effect is muted where countercyclical capital buffers and macroprudential tools tighten before the peak.
   - Variables: BIS credit gap, countercyclical buffer/macroprudential index, real house prices, GDP growth, unemployment, bank credit growth.
   - Likely data sources: BIS credit gap/house prices, IMF iMaPP macroprudential database, WDI/ILOSTAT.
   - Runability: `NEEDS_DATA`.

37. `capacity_bank_capital_buffers_credit_cycle_cost`
   - Claim: Higher pre-crisis bank capital buffers reduce crisis output losses without permanently lowering credit growth in high-supervision states; in weak-supervision states, nominal capital ratios do not prevent credit busts.
   - Variables: bank capital ratios, supervisory quality, credit growth, banking-crisis episodes, GDP drawdown, recovery speed.
   - Likely data sources: GFDD, World Bank/IMF banking supervision surveys, Laeven-Valencia crisis data, BIS credit, WDI.
   - Runability: `NEEDS_ALIAS`.

38. `capacity_financial_liberalization_supervision_interaction`
   - Claim: Financial liberalization increases private investment and innovation only when supervision and rule of law are strong; liberalization under weak supervision predicts credit booms and later crisis probability.
   - Variables: financial openness/liberalization episodes, supervisory capacity/rule of law, private credit, investment, patenting, banking crises.
   - Likely data sources: Chinn-Ito/Abiad financial reform indexes, WGI, WDI/GFDD, Laeven-Valencia, UN patents.
   - Runability: `NEEDS_DATA`.

39. `capacity_housing_supply_credit_boom_amplifier`
   - Claim: Credit booms turn into damaging house-price cycles primarily where housing supply and permitting capacity are constrained; elastic-supply markets show smaller price booms and smaller post-boom employment losses.
   - Variables: credit gap, real house prices, building permits/housing completions, land-use restrictiveness, unemployment change, construction employment.
   - Likely data sources: BIS credit/house prices, Eurostat/OECD housing permits, WDI construction where available, national housing datasets.
   - Runability: `NEEDS_ALIAS`.

40. `capacity_deposit_insurance_supervision_moral_hazard`
   - Claim: Deposit insurance reduces bank-run risk without raising crisis probability when supervision is strong; broad guarantees in weak-supervision regimes predict faster credit growth and higher crisis incidence.
   - Variables: deposit insurance coverage, supervisory quality, private credit growth, banking-crisis indicator, bank Z-score/nonperforming loans.
   - Likely data sources: World Bank deposit insurance database, GFDD, Laeven-Valencia, WGI.
   - Runability: `NEEDS_DATA`.

41. `capacity_capital_market_depth_innovation_vs_volatility`
   - Claim: Capital-market depth raises patenting and high-growth entry when rule of law and disclosure quality are high; in weak-institution settings, market depth predicts volatility and crisis exposure more than innovation.
   - Variables: stock-market capitalization/turnover, rule of law, patents, business entry, GDP volatility, crisis episodes.
   - Likely data sources: GFDD, WGI, UN patents, WDI business entry, IMF/WDI GDP.
   - Runability: `READY_NOW`.

### Social Insurance / Welfare Architecture

42. `capacity_unemployment_benefits_activation_threshold`
   - Claim: More generous unemployment benefits do not lower employment when activation spending and case-management capacity are high; without activation, generosity predicts longer unemployment duration and lower employment rates.
   - Variables: unemployment-benefit spending/replacement proxy, ALMP spending, government effectiveness, unemployment duration/long-term unemployment, employment rate.
   - Likely data sources: OECD SOCX, OECD labour/ALMP, WGI, ILOSTAT.
   - Runability: `NEEDS_ALIAS`.

43. `capacity_health_insurance_labour_market_complement`
   - Claim: Universal or broad health coverage improves health outcomes without reducing employment when financed through broad-based taxes or social insurance and managed by high-capacity institutions; payroll-heavy financing with weak administration predicts employment drag.
   - Variables: health coverage/spending, financing mix/payroll tax proxy, employment rate, life expectancy/mortality, government effectiveness.
   - Likely data sources: WDI health and employment, OECD health/social spending, WGI.
   - Runability: `NEEDS_ALIAS`.

44. `capacity_forced_saving_vs_payg_informality`
   - Claim: Forced-saving pension architectures improve national saving and reduce old-age poverty when labour informality is low and capital markets are deep; in high-informality settings they leave coverage gaps and do not outperform PAYG/transfer systems.
   - Variables: pension architecture, saving rate, pension coverage, old-age poverty, informality proxy, capital-market depth, fiscal debt.
   - Likely data sources: OECD pensions/SOCX, WDI saving and labour, GFDD, LIS/WID or national poverty data.
   - Runability: `NEEDS_DATA`.

45. `capacity_childcare_spending_female_lfp_housing_cost`
   - Claim: Public childcare and family benefits raise female labour-force participation and fertility only when housing costs and childcare supply constraints are not binding; high transfers without supply expansion have weaker fertility/LFP effects.
   - Variables: family/childcare spending, childcare coverage, housing cost/rent burden, female LFP, fertility, employment rate.
   - Likely data sources: OECD SOCX/family database, WDI female LFP/fertility, OECD/Eurostat housing indicators.
   - Runability: `NEEDS_ALIAS`.

46. `capacity_in_work_benefits_cliff_employment`
   - Claim: In-work benefits increase low-income employment when phaseout cliffs are smooth and administration is simple; sharp cliffs or complex means tests predict lower hours growth and weaker reemployment.
   - Variables: in-work benefit generosity, effective marginal tax rates/benefit cliffs, low-wage employment, hours worked, reemployment duration.
   - Likely data sources: OECD TaxBEN, OECD Benefits and Wages, ILOSTAT, national labour microdata for robustness.
   - Runability: `NEEDS_ALIAS`.

### Infrastructure / Market Complementarity

47. `capacity_transport_infrastructure_market_access_productivity`
   - Claim: Transport infrastructure raises regional productivity and employment where procurement quality and maintenance capacity are high; low-capacity buildouts show weaker productivity gains and higher debt per road-km improvement.
   - Variables: road/rail density or investment, procurement/corruption quality, regional or national productivity, employment, debt.
   - Likely data sources: WDI roads, WGI, OECD regional data or national transport datasets, IMF WEO.
   - Runability: `NEEDS_ALIAS`.

48. `capacity_broadband_competition_productivity_diffusion`
   - Claim: Broadband infrastructure improves business entry, productivity, and export services when telecom competition and regulatory quality are high; monopoly rollout without competition shows weaker diffusion benefits.
   - Variables: broadband/internet penetration, telecom competition/regulatory quality, business registrations, service exports, productivity growth.
   - Likely data sources: WDI internet/service exports/business entry, ITU telecom indicators, WGI regulatory quality.
   - Runability: `NEEDS_ALIAS`.

49. `capacity_grid_flexibility_renewables_price_volatility`
   - Claim: Renewable capacity lowers electricity cost trajectories when grid flexibility/storage/interconnection capacity is high; without flexibility, renewable growth predicts higher industrial price volatility and manufacturing pressure.
   - Variables: renewable capacity/share, storage/interconnection/dispatchable capacity proxy, industrial electricity prices, price volatility, manufacturing value added.
   - Likely data sources: IRENA, Eurostat electricity prices, WDI electricity/manufacturing, ENTSO-E/IEA grid data.
   - Runability: `NEEDS_DATA`.

50. `capacity_social_housing_supply_vs_rent_control`
   - Claim: Public or nonprofit housing supply can reduce rent pressure without the supply losses associated with binding rent controls, but only where permitting and procurement capacity expand net units; price controls without supply expansion reduce availability.
   - Variables: social-housing stock/additions, rent-control episodes, building permits/completions, rents, vacancy, household formation, mobility.
   - Likely data sources: OECD affordable housing database, Eurostat permits/rents, national housing data, WDI construction proxies.
   - Runability: `NEEDS_DATA`.

## Strongest Immediate Run Candidates

Best first-pass candidates because the current local data spine likely supports
the interaction design without major new acquisition:

- `capacity_stabilizers_output_loss_threshold_oecd`
- `capacity_tax_revenue_public_goods_threshold`
- `capacity_government_effectiveness_state_size_nonmonotonic`
- `capacity_corruption_public_investment_leakage`
- `capacity_rule_of_law_financial_depth_productive_allocation`
- `capacity_trade_liberalization_institutional_variance`
- `capacity_education_spending_learning_threshold`
- `capacity_health_spending_mortality_corruption_interaction`
- `capacity_electricity_access_regulatory_quality`
- `capacity_rnd_spending_finance_patent_productivity`
- `capacity_tariff_sunset_infant_industry_upgrade`
- `capacity_hightech_exports_government_effectiveness_interaction`
