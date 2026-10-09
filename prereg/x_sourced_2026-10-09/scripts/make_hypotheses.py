"""Generate X-sourced draft hypotheses (IESET schema) + steelman notes. Status: draft. Not in git."""
import json, yaml, pathlib, jsonschema
REPO = pathlib.Path.home()/"IESET"; OUT = pathlib.Path.home()/"IESET-x-build"/"hypotheses"
schema = json.load(open(REPO/"schemas/hypothesis.schema.json"))
DISC = ("Drafted 2026-10-09 by agent from a high-engagement X claim. The headline value quoted in the tweet was seen "
        "before drafting; the falsification threshold was fixed before the analysis script was run and is frozen "
        "in PREREG_LEDGER.json (SHA256 + UTC). Not git-pre-registered (needs user-approved commit).")
CONF = "Author holds no positions related to this claim. Engine house prior is market-liberal; disclosed."
H = []
def h(hid, topic, claim, ev, countries, period, ts, outcomes, est, rule, test, threshold, prior, scope_dims, policy, tweets, direction="?", notes=""):
    H.append(dict(hypothesis_id=hid, version=1, status="draft", topic=topic, claim=claim, claim_direction=direction,
      evidence_type=ev, sample=dict(countries=countries, period=period, temporal_structure=ts),
      variables=dict(outcome=outcomes), estimator=dict(template=est),
      falsification=dict(rule=rule, test=test, threshold=threshold), prior_confidence=prior,
      disclosure=DISC, conflict_disclosure=CONF, steelman=f"hypotheses/steelman/{hid}.md",
      scope=dict(period=period, countries=countries, outcome_dim=scope_dims, policy_family=policy),
      source_provenance={"archive_refs": tweets, "mined_at": "2026-10-09", "mined_by_model": "Grok Bot (X search)"},
      notes=notes or "X-sourced draft; build dir ~/IESET-x-build; runner scripts/run_x_hypotheses.py"))
V=lambda n,s,t="level": dict(name=n, source=s, transformation=t)

h("argentina_core_vs_headline_inflation_2025_2026","monetary",
  "Stripping volatile/regulated items flatters Argentine inflation: over Jan 2025-Aug 2026 INDEC core (nucleo) monthly inflation runs below headline, i.e. 'exclude food and fuel and it looks fine'.",
  "descriptive",["ARG"],[2025,2026],"time_series",
  [V("ipc_headline_mom","indec_ipc:headline","mom_pct"),V("ipc_core_mom","indec_ipc:core","mom_pct"),V("ipc_regulated_mom","indec_ipc:regulated","mom_pct")],
  "descriptive","SUPPORTED if mean(headline-core) >= 0.10pp over 2025-01..2026-08; REFUTED if mean(headline-core) <= 0; PARTIAL otherwise. Secondary (informative): mean(regulated-core).",
  "mean_gap_headline_minus_core","mean(headline_mom - core_mom) >= 0.10",0.4,["inflation"],["monetary_policy"],
  ["https://x.com/MartinDandach/status/2104389560658456823"])
h("argentina_monthly_cpi_25pct_to_under_2pct_2023_2026","monetary",
  "Argentine monthly CPI fell from ~25.5% m/m in Dec 2023 to under 2% m/m by Aug 2026.",
  "descriptive",["ARG"],[2023,2026],"time_series",[V("ipc_headline_mom","indec:148.3_INIVELNAL_DICI_M_26","mom_pct")],
  "descriptive","SUPPORTED if Dec-2023 m/m >= 20 AND latest (Aug-2026) m/m <= 2.5 AND mean of last 12 months <= 3.0; REFUTED if latest m/m > 4; PARTIAL otherwise.",
  "endpoint_thresholds","dec23>=20 & latest<=2.5 & mean12<=3",0.8,["inflation"],["monetary_policy","fiscal_policy"],
  ["https://x.com/Rothmus/status/2104310814370926972"],"-")
h("seattle_minimum_wage_restaurant_employment_2025_2026","labour",
  "Seattle's high minimum wage (~$21-22/hr) is costing restaurant jobs: Seattle-metro food-service employment underperforms the US in 2025-2026.",
  "associational",["USA"],[2024,2026],"time_series",
  [V("seattle_msa_food_services_emp","bls:SMU53426607072200001","yoy_pct"),V("us_food_services_emp_nsa","bls:CEU7072200001","yoy_pct")],
  "descriptive","Mean y/y growth Jan-2025..latest. SUPPORTED if Seattle MSA mean y/y <= US mean y/y - 1.0pp AND Seattle mean y/y < 0; REFUTED if Seattle mean y/y >= US mean y/y; PARTIAL otherwise. MSA includes lower-wage suburbs (dilution caveat).",
  "yoy_gap_vs_us","seattle_yoy - us_yoy <= -1.0 & seattle_yoy < 0",0.4,["employment_labour"],["labour_market"],
  ["https://x.com/LeadingReport/status/2106846970304192891","https://x.com/amuse/status/2106036734106685869"],"-")
h("california_fast_food_20_wage_restaurant_employment","labour",
  "California's $20 fast-food minimum wage (Apr 2024) reduced restaurant employment relative to the rest of the US.",
  "associational",["USA"],[2023,2026],"time_series",
  [V("ca_food_services_emp","bls:SMU06000007072200001","index Mar-2024=100"),V("us_food_services_emp_nsa","bls:CEU7072200001","index Mar-2024=100")],
  "descriptive","Compare index (Mar-2024=100, same calendar month to net seasonality) at latest common month. SUPPORTED if CA index <= US index - 1.5; REFUTED if CA index >= US index; PARTIAL otherwise. Food services & drinking places (broader than fast food).",
  "index_gap_vs_us","ca_idx - us_idx <= -1.5",0.5,["employment_labour"],["labour_market"],
  ["https://x.com/LeadingReport/status/2106846970304192891"],"-")
h("us_manufacturing_jobs_change_since_jan_2025","trade",
  "US manufacturing employment has fallen since January 2025 despite tariffs (vs White House claim of manufacturing job gains).",
  "descriptive",["USA"],[2025,2026],"time_series",[V("us_manufacturing_emp","bls:CES3000000001","level, thousands SA")],
  "descriptive","SUPPORTED (jobs down) if CES manufacturing latest - Jan-2025 <= -20k; REFUTED if >= +20k; PARTIAL (flat) otherwise.",
  "level_change","latest - 2025-01 <= -20",0.6,["industrial_capability","employment_labour"],["trade_policy","industrial_policy"],
  ["https://x.com/RMConservative/status/2105347801118855340","https://x.com/RapidResponse47/status/2105782019036754014"],"-")
h("germany_wind_solar_share_lowers_wholesale_price","energy",
  "Higher wind+solar share lowers German day-ahead wholesale prices (merit-order effect), contrary to claims renewables raised German power prices.",
  "associational",["DEU"],[2018,2026],"time_series",
  [V("de_lu_day_ahead_price","smard:price_de_lu","monthly mean EUR/MWh"),V("vre_share_of_load","smard:wind_onshore+wind_offshore+solar / load","share")],
  "panel_fe","OLS price ~ vre_share + year FE + calendar-month FE, HC3. SUPPORTED if beta<0 and p<0.05; REFUTED (renewables raise wholesale price) if beta>0 and p<0.05; INCONCLUSIVE otherwise. Wholesale only; retail levies/network fees out of scope.",
  "ols_fe_beta_sign","beta_vre<0 & p<0.05",0.75,["energy"],["energy_policy"],
  ["https://x.com/dlacalle_IA/status/2106401506521907314"],"-")
h("us_state_wind_solar_share_vs_residential_price_2010_2025","energy",
  "States that expanded wind+solar share most since 2010 saw larger residential electricity price increases ('net zero drives bills').",
  "associational",["USA"],[2010,2025],"cross_section_with_justification",
  [V("d_res_price","eia_v2:electricity/retail-sales RES price","2025 minus 2010, cents/kWh"),V("d_vre_share","eia_v2:electric-power-operational-data SUN+WND / ALL","2025 minus 2010, pp")],
  "descriptive","Long-difference OLS across 50 states+DC: d_price ~ d_vre_share + d_gas_share + price_2010, HC3. SUPPORTED if beta>0 and p<0.05; REFUTED if beta<0 and p<0.05; INCONCLUSIVE otherwise. Excludes AK, HI in robustness.",
  "long_difference_ols","beta_vre>0 & p<0.05",0.35,["energy"],["energy_policy"],
  ["https://x.com/7Kiwi/status/2106351226707132729","https://x.com/TiceRichard/status/2106413483265085464","https://x.com/zatzi/status/2106364678418968683"],"+")
h("us_southwest_border_encounters_collapse_fy2026","institutional_quality",
  "Southwest-border encounters in FY2026 are down more than 90% versus FY2023 over the same fiscal-year months.",
  "descriptive",["USA"],[2023,2026],"time_series",[V("sw_encounters","uscbp:nationwide_encounters (Southwest Land Border)","sum over common FY months")],
  "descriptive","SUPPORTED if FY26 YTD / FY23 same months <= 0.10; REFUTED if >= 0.50; PARTIAL otherwise.",
  "ratio_same_months","fy26/fy23 <= 0.10",0.8,["demographics_migration"],["institutional_reform"],
  ["https://x.com/WhiteHouse/status/2108219014828949915"],"-")
h("border_closure_raises_low_wage_growth_2025_2026","labour",
  "Cutting immigration raises wages of low-paid native workers: after the 2024-25 border collapse, bottom-quartile wage growth rose relative to top-quartile wage growth.",
  "associational",["USA"],[2023,2026],"time_series",
  [V("wgt_q1_minus_q4","atlanta_fed_wgt:Average Wage Quartile (lowest minus highest)","3mma median y/y, pp")],
  "descriptive","Gap = Q1 - Q4 wage growth. Compare mean gap Feb-2025..latest vs Jan-2023..Jun-2024. SUPPORTED if change >= +0.5pp; REFUTED if change <= -0.5pp; INCONCLUSIVE otherwise. No causal identification (tight-labour-market cycle confound).",
  "gap_change_pre_post","delta_gap >= 0.5",0.35,["wage_stagnation","demographics_migration"],["labour_market"],
  ["https://x.com/VP/status/2104269134741831909","https://x.com/realBrandonGill/status/2103498546498396549"],"+")
h("el_salvador_investment_and_growth_vs_central_america_2019_2025","growth",
  "Despite the security turnaround, El Salvador has the lowest investment rate in Central America and has not out-grown its peers under Bukele.",
  "descriptive",["SLV","GTM","HND","NIC","CRI","PAN","DOM"],[2019,2025],"panel",
  [V("investment_gdp","imf_weo_sdmx:NID_NGDP","mean 2019-2025"),V("real_gdp_growth","imf_weo_sdmx:NGDP_RPCH","mean 2019-2025")],
  "descriptive","SUPPORTED if SLV mean NID_NGDP 2019-2025 ranks lowest of 7 AND SLV mean growth is below peer median; REFUTED if SLV investment rank is in top half (1-3) AND growth above peer median; PARTIAL otherwise.",
  "peer_rank","slv_invest_rank==7 & slv_growth<median",0.55,["gdp_growth","institutional_quality"],["institutional_reform"],
  ["https://x.com/wander_investor/status/2108080210197299275","https://x.com/nayibbukele/status/2104018288057401510"],"-")
h("sweden_1990s_crisis_three_year_contraction_12pct_unemployment","growth",
  "Sweden's early-1990s crisis: GDP contracted three years in a row and unemployment reached ~12%.",
  "descriptive",["SWE"],[1990,1998],"time_series",[V("real_gdp_growth","imf_weo_sdmx:NGDP_RPCH"),V("unemployment","imf_weo_sdmx:LUR")],
  "descriptive","SUPPORTED if NGDP_RPCH < 0 in each of 1991,1992,1993 AND peak LUR 1990-1998 >= 11.0; PARTIAL if exactly one holds; REFUTED if neither.",
  "checklist","3 negative years & peak_LUR>=11",0.6,["financial_crisis","gdp_growth"],["fiscal_policy"],
  ["https://x.com/Handre/status/2103135617815375925"])

OUT.mkdir(parents=True, exist_ok=True)
for d in H:
    jsonschema.validate(d, schema)
    p = OUT/d["topic"]/f'{d["hypothesis_id"]}.yaml'; p.parent.mkdir(exist_ok=True)
    p.write_text("# yaml-language-server: $schema=../../../IESET/schemas/hypothesis.schema.json\n"+yaml.safe_dump(d, sort_keys=False, width=200, allow_unicode=True))
    s = OUT/"steelman"/f'{d["hypothesis_id"]}.md'; s.parent.mkdir(exist_ok=True)
    s.write_text(f"# Steelman: {d['hypothesis_id']}\n\nClaim: {d['claim']}\n\nStrongest opposing case: the test is {d['evidence_type']}, not causal; confounders (cycle, energy-price shocks, compositional change, data revisions, preliminary prints) could produce the same pattern. Falsification: {d['falsification']['rule']}\n")
    print("ok", p)
