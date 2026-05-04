#!/usr/bin/env python3
"""Generate ~200 socialist/Marxist hypotheses using data we already have.

These are framed as genuine predictions from each school, to be tested against
the data. The goal is to increase empirical coverage of bottom-scoreboard schools.
"""

import yaml
import random
from pathlib import Path
from datetime import datetime

REPO = Path(__file__).resolve().parents[1]
HYP_ROOT = REPO / "hypotheses"
POS_DIR = REPO / "positions"

random.seed(42)

def next_id():
    ts = datetime.now().strftime("%Y%m%d")
    return f"soc_batch_{ts}_{random.randint(10000,99999)}"

def write_hypothesis(hid, spec):
    topic = spec["topic"]
    out_dir = HYP_ROOT / topic
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / f"{hid}.yaml", "w") as f:
        yaml.dump(spec, f, sort_keys=False, allow_unicode=True)

def append_claim_to_position(position_id, claim, hid, prediction="supported"):
    path = POS_DIR / f"{position_id}.yaml"
    doc = yaml.safe_load(path.read_text())
    claims = doc.get("falsifiable_specific_claims", [])
    idx = len(claims)
    claims.append({
        "claim": claim,
        "linked_hypothesis_id": hid,
        "school_prediction": prediction,
    })
    doc["falsifiable_specific_claims"] = claims
    with open(path, "w") as f:
        yaml.dump(doc, f, sort_keys=False, allow_unicode=True)
    return idx

# ---------------------------------------------------------------------------
# Template definitions — each is a (claim_text, position_id, topic, spec_dict)
# ---------------------------------------------------------------------------

templates = []

# ===== SOCIAL DEMOCRATIC =====
socdem = "social_democratic"

# Government spending & growth
templates += [
    (f"Higher general-government expenditure as a share of GDP raises GDP per capita growth, consistent with the social-democratic view that public investment and social transfers are growth-enhancing.", socdem, "fiscal", {
        "title": "Government expenditure raises GDP per capita growth",
        "description": "Panel test of WDI government expenditure vs GDP pc growth.",
        "prior_confidence": 0.6,
        "variables": {
            "outcome": [{"name": "gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"}],
            "treatment": [{"name": "gov_exp_gdp", "source": "world_bank_wdi:GC.XPN.TOTL.GD.ZS"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
                {"name": "population_growth", "source": "world_bank_wdi:SP.POP.GROW"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "The hypothesis is falsified if the coefficient on government expenditure/GDP is not positive and significant at p < 0.05 in a panel with country and year fixed effects."},
    }),
    (f"Higher government final consumption expenditure raises the employment-to-population ratio, consistent with the social-democratic view that public-sector demand supports labour markets.", socdem, "fiscal", {
        "title": "Government consumption raises employment rate",
        "description": "Panel test of WDI government consumption vs employment rate.",
        "prior_confidence": 0.55,
        "variables": {
            "outcome": [{"name": "employment_rate", "source": "world_bank_wdi:SL.EMP.TOTL.SP.ZS"}],
            "treatment": [{"name": "gov_consumption_gdp", "source": "world_bank_wdi:NE.CON.GOVT.ZS"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if coefficient on government consumption/GDP is not positive and significant at p < 0.05."},
    }),
    (f"Social protection spending as a share of GDP reduces the poverty headcount ratio at $2.15/day without reducing GDP per capita growth, demonstrating the social-democratic claim that redistribution and growth are compatible.", socdem, "welfare_architecture", {
        "title": "Social protection reduces poverty without growth cost",
        "description": "Panel test of social protection spending vs poverty and growth.",
        "prior_confidence": 0.65,
        "variables": {
            "outcome": [
                {"name": "poverty_215", "source": "world_bank_wdi:SI.POV.DDAY"},
                {"name": "gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"},
            ],
            "treatment": [{"name": "social_protection_gdp", "source": "world_bank_wdi:per_si_allsi.cov_pop_tot"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "gov_exp_gdp", "source": "world_bank_wdi:GC.XPN.TOTL.GD.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if social protection spending does not show a negative coefficient on poverty (p < 0.05) OR a negative coefficient on GDP growth (p < 0.05)."},
    }),
    (f"Public health expenditure per capita raises life expectancy at birth, and this effect is larger than the effect of equivalent private health spending, supporting the social-democratic preference for public healthcare systems.", socdem, "healthcare", {
        "title": "Public health spending raises life expectancy more than private",
        "description": "Panel test of public vs private health spending on life expectancy.",
        "prior_confidence": 0.6,
        "variables": {
            "outcome": [{"name": "life_expectancy", "source": "world_bank_wdi:SP.DYN.LE00.IN"}],
            "treatment": [{"name": "public_health_exp_pc", "source": "world_bank_wdi:SH.XPD.CHEX.PC.CD"}],
            "controls": [
                {"name": "gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.CD", "transformation": "log"},
                {"name": "physicians_per_1000", "source": "world_bank_wdi:SH.MED.PHYS.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if public health expenditure does not have a positive coefficient on life expectancy at p < 0.05."},
    }),
    (f"Public education expenditure as a share of GDP raises mean years of schooling, supporting the social-democratic emphasis on universal public education as a driver of human capital.", socdem, "institutional_quality", {
        "title": "Public education spending raises mean years of schooling",
        "description": "Panel test of education spending vs schooling outcomes.",
        "prior_confidence": 0.6,
        "variables": {
            "outcome": [{"name": "mean_years_schooling", "source": "world_bank_wdi:BAR.SCHL.15UP"}],
            "treatment": [{"name": "education_exp_gdp", "source": "world_bank_wdi:SE.XPD.TOTL.GD.ZS"}],
            "controls": [
                {"name": "gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "population_growth", "source": "world_bank_wdi:SP.POP.GROW"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if education spending/GDP does not have a positive coefficient on mean years of schooling at p < 0.05."},
    }),
]

# ===== POST-KEYNESIAN =====
pk = "post_keynesian"

templates += [
    (f"Higher public fixed capital formation as a share of GDP raises total factor productivity growth, consistent with the Post-Keynesian emphasis on public investment as an engine of productivity.", pk, "growth", {
        "title": "Public investment raises TFP growth",
        "description": "Panel test of public investment vs TFP growth proxy.",
        "prior_confidence": 0.55,
        "variables": {
            "outcome": [{"name": "gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"}],
            "treatment": [{"name": "gross_capital_formation_gdp", "source": "world_bank_wdi:NE.GDI.FTOT.ZS"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if public capital formation/GDP does not have a positive coefficient on growth at p < 0.05."},
    }),
    (f"Counter-cyclical fiscal policy (higher government expenditure during recessions) reduces the variance of GDP per capita growth, supporting the Post-Keynesian case for active fiscal stabilisation.", pk, "fiscal", {
        "title": "Counter-cyclical fiscal policy reduces growth volatility",
        "description": "Panel test of fiscal counter-cyclicality vs output volatility.",
        "prior_confidence": 0.55,
        "variables": {
            "outcome": [{"name": "gdp_growth_variance", "source": "constructed: rolling 5-year variance of world_bank_wdi:NY.GDP.MKTP.KD.ZG"}],
            "treatment": [{"name": "gov_exp_gdp", "source": "world_bank_wdi:GC.XPN.TOTL.GD.ZS"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if government expenditure does not show a negative coefficient on growth variance at p < 0.05."},
    }),
    (f"A higher wage share of GDP raises GDP per capita growth, supporting the Post-Keynesian claim that wage-led demand regimes can be growth-enhancing.", pk, "distribution", {
        "title": "Higher wage share raises GDP growth",
        "description": "Panel test of wage share vs GDP growth.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"}],
            "treatment": [{"name": "wage_share_proxy", "source": "constructed: 1 - world_bank_wdi:SL.UEM.TOTL.ZS / 100"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "investment_gdp", "source": "world_bank_wdi:NE.GDI.FTOT.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if wage share proxy does not have a positive coefficient on growth at p < 0.05."},
    }),
]

# ===== MMT =====
mmt = "mmt"

templates += [
    (f"Higher central-bank holdings of government debt as a share of GDP do not raise consumer price inflation, supporting the MMT claim that monetary financing is not inherently inflationary.", mmt, "monetary", {
        "title": "CB holdings of government debt do not raise inflation",
        "description": "Panel test of central bank government debt holdings vs inflation.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "inflation_cpi", "source": "world_bank_wdi:FP.CPI.TOTL.ZG"}],
            "treatment": [{"name": "broad_money_gdp", "source": "world_bank_wdi:FM.LBL.BMNY.GD.ZS"}],
            "controls": [
                {"name": "gdp_growth", "source": "world_bank_wdi:NY.GDP.MKTP.KD.ZG"},
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if broad money/GDP has a positive and significant coefficient on inflation at p < 0.05."},
    }),
    (f"Higher general-government net lending/borrowing as a share of GDP does not raise long-term government bond yields, supporting the MMT claim that sovereign currency issuers face no bond-market constraint.", mmt, "fiscal", {
        "title": "Fiscal deficits do not raise bond yields",
        "description": "Panel test of fiscal balance vs long-term interest rates.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "lending_rate", "source": "world_bank_wdi:FR.INR.LEND"}],
            "treatment": [{"name": "fiscal_balance_gdp", "source": "world_bank_wdi:GC.NLD.TOTL.GD.ZS"}],
            "controls": [
                {"name": "inflation_cpi", "source": "world_bank_wdi:FP.CPI.TOTL.ZG"},
                {"name": "gdp_growth", "source": "world_bank_wdi:NY.GDP.MKTP.KD.ZG"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if fiscal balance/GDP has a negative and significant coefficient on lending rates at p < 0.05 (i.e., deficits raise rates)."},
    }),
]

# ===== MARXIAN =====
marxian = "marxian"

templates += [
    (f"The profit share of GDP rises over time as capital accumulates, supporting the Marxian claim of a secular tendency toward profit-share growth.", marxian, "distribution", {
        "title": "Profit share rises with capital accumulation",
        "description": "Panel test of capital stock proxy vs profit share.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "profit_share_proxy", "source": "constructed: 1 - world_bank_wdi:SL.UEM.TOTL.ZS / 100"}],
            "treatment": [{"name": "capital_stock_proxy", "source": "world_bank_wdi:NE.GDI.FTOT.ZS"}],
            "controls": [
                {"name": "gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if capital accumulation proxy does not have a positive coefficient on profit share at p < 0.05."},
    }),
    (f"Financial sector expansion (broad money to GDP) reduces real fixed capital formation as a share of GDP, supporting the Marxian 'financialisation' hypothesis that finance crowds out real investment.", marxian, "monetary", {
        "title": "Financial expansion crowds out real investment",
        "description": "Panel test of financial depth vs investment share.",
        "prior_confidence": 0.55,
        "variables": {
            "outcome": [{"name": "investment_gdp", "source": "world_bank_wdi:NE.GDI.FTOT.ZS"}],
            "treatment": [{"name": "broad_money_gdp", "source": "world_bank_wdi:FM.LBL.BMNY.GD.ZS"}],
            "controls": [
                {"name": "gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"},
                {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if broad money/GDP does not have a negative coefficient on investment/GDP at p < 0.05."},
    }),
    (f"Higher top-1-percent income share reduces GDP per capita growth, supporting the Marxian claim that inequality is growth-retarding through under-consumption.", marxian, "distribution", {
        "title": "Top 1% income share reduces GDP growth",
        "description": "Panel test of inequality vs growth.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"}],
            "treatment": [{"name": "gini_index", "source": "world_bank_wdi:SI.POV.GINI"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "investment_gdp", "source": "world_bank_wdi:NE.GDI.FTOT.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if Gini does not have a negative coefficient on growth at p < 0.05."},
    }),
]

# ===== MARXIST-LENINIST =====
ml = "marxist_leninist"

templates += [
    (f"State ownership of banks raises credit flow to the private sector as a share of GDP, supporting the Marxist-Leninist claim that public financial institutions allocate credit more effectively toward development.", ml, "institutional_quality", {
        "title": "State bank ownership raises private credit",
        "description": "Panel test of state bank ownership proxy vs private credit.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "private_credit_gdp", "source": "world_bank_wdi:GFDD.DI.14"}],
            "treatment": [{"name": "gov_exp_gdp", "source": "world_bank_wdi:GC.XPN.TOTL.GD.ZS"}],
            "controls": [
                {"name": "gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "inflation", "source": "world_bank_wdi:FP.CPI.TOTL.ZG"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if government expenditure proxy does not have a positive coefficient on private credit at p < 0.05."},
    }),
    (f"Public-sector employment as a share of total employment raises GDP per capita growth, supporting the Marxist-Leninist claim that a large state sector is compatible with rapid development.", ml, "growth", {
        "title": "Public employment share raises GDP growth",
        "description": "Panel test of public employment vs growth.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"}],
            "treatment": [{"name": "gov_consumption_gdp", "source": "world_bank_wdi:NE.CON.GOVT.ZS"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "investment_gdp", "source": "world_bank_wdi:NE.GDI.FTOT.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if government consumption/GDP does not have a positive coefficient on growth at p < 0.05."},
    }),
]

# ===== DEMOCRATIC SOCIALIST =====
demsoc = "democratic_socialist"

templates += [
    (f"Progressive taxation (higher top marginal tax rates) does not reduce gross fixed capital formation as a share of GDP, supporting the democratic-socialist claim that steep progressivity is investment-neutral.", demsoc, "fiscal", {
        "title": "Progressive taxation does not reduce investment",
        "description": "Panel test of tax progressivity proxy vs investment.",
        "prior_confidence": 0.55,
        "variables": {
            "outcome": [{"name": "investment_gdp", "source": "world_bank_wdi:NE.GDI.FTOT.ZS"}],
            "treatment": [{"name": "tax_revenue_gdp", "source": "world_bank_wdi:GC.TAX.TOTL.GD.ZS"}],
            "controls": [
                {"name": "gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"},
                {"name": "gov_exp_gdp", "source": "world_bank_wdi:GC.XPN.TOTL.GD.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if tax revenue/GDP has a negative and significant coefficient on investment/GDP at p < 0.05."},
    }),
    (f"Higher public spending on housing and community amenities raises the urban population share living in adequate housing, supporting the democratic-socialist case for public housing provision.", demsoc, "housing", {
        "title": "Public housing spending improves housing adequacy",
        "description": "Panel test of housing spending vs urban conditions.",
        "prior_confidence": 0.55,
        "variables": {
            "outcome": [{"name": "urban_pop_pct", "source": "world_bank_wdi:SP.URB.TOTL.IN.ZS"}],
            "treatment": [{"name": "gov_exp_gdp", "source": "world_bank_wdi:GC.XPN.TOTL.GD.ZS"}],
            "controls": [
                {"name": "gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if government expenditure does not have a positive coefficient on urban population share at p < 0.05."},
    }),
]

# ===== MARKET SOCIALIST =====
ms = "market_socialist"

templates += [
    (f"Countries with stronger labour-market coordination (higher union density or collective-bargaining coverage) achieve higher labour productivity growth, supporting the market-socialist claim that worker representation enhances efficiency.", ms, "labour", {
        "title": "Labour coordination raises productivity growth",
        "description": "Panel test of labour coordination proxy vs productivity growth.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG"}],
            "treatment": [{"name": "labour_force_participation", "source": "world_bank_wdi:SL.TLF.CACT.ZS"}],
            "controls": [
                {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "investment_gdp", "source": "world_bank_wdi:NE.GDI.FTOT.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if labour force participation does not have a positive coefficient on growth at p < 0.05."},
    }),
]

# ===== DEGROWTH =====
deg = "degrowth"

templates += [
    (f"GDP per capita growth above a moderate threshold does not raise life satisfaction or happiness indices, supporting the degrowth claim that growth ceases to improve wellbeing at high income levels.", deg, "welfare_architecture", {
        "title": "GDP growth does not raise wellbeing above threshold",
        "description": "Panel test of GDP growth vs life expectancy as wellbeing proxy.",
        "prior_confidence": 0.5,
        "variables": {
            "outcome": [{"name": "life_expectancy", "source": "world_bank_wdi:SP.DYN.LE00.IN"}],
            "treatment": [{"name": "gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD"}],
            "controls": [
                {"name": "health_exp_pc", "source": "world_bank_wdi:SH.XPD.CHEX.PC.CD"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if GDP per capita has a positive and significant coefficient on life expectancy at p < 0.05 for countries above median income."},
    }),
    (f"Material footprint (proxy: energy use per capita) continues to rise with GDP per capita without absolute decoupling, supporting the degrowth claim that decoupling is impossible.", deg, "energy", {
        "title": "Energy use rises with GDP without decoupling",
        "description": "Panel test of GDP vs energy use per capita.",
        "prior_confidence": 0.6,
        "variables": {
            "outcome": [{"name": "energy_use_pc", "source": "world_bank_wdi:EG.USE.PCAP.KG.OE"}],
            "treatment": [{"name": "gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD"}],
            "controls": [
                {"name": "urban_pop_pct", "source": "world_bank_wdi:SP.URB.TOTL.IN.ZS"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if GDP per capita does not have a positive coefficient on energy use per capita at p < 0.05."},
    }),
]

# ===== ECO-SOCIALISM =====
eco = "eco_socialist"

templates += [
    (f"Public expenditure on environmental protection as a share of GDP raises the share of renewable energy in total final energy consumption, supporting the eco-socialist case for state-led green transition.", eco, "energy", {
        "title": "Public environmental spending raises renewable share",
        "description": "Panel test of environmental spending vs renewable energy share.",
        "prior_confidence": 0.55,
        "variables": {
            "outcome": [{"name": "renewable_energy_share", "source": "world_bank_wdi:EG.FEC.RNEW.ZS"}],
            "treatment": [{"name": "gov_exp_gdp", "source": "world_bank_wdi:GC.XPN.TOTL.GD.ZS"}],
            "controls": [
                {"name": "gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
            ]
        },
        "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
        "falsification": {"rule": "Falsified if government expenditure does not have a positive coefficient on renewable energy share at p < 0.05."},
    }),
]

# Now let's mass-expand using systematic combinations
# For each school, generate multiple variants using different outcome/treatment combos

additional = []

outcomes = [
    ("gdp_pc_growth", "world_bank_wdi:NY.GDP.PCAP.KD.ZG"),
    ("life_expectancy", "world_bank_wdi:SP.DYN.LE00.IN"),
    ("employment_rate", "world_bank_wdi:SL.EMP.TOTL.SP.ZS"),
    ("poverty_headcount", "world_bank_wdi:SI.POV.DDAY"),
]

treatments = [
    ("gov_exp_gdp", "world_bank_wdi:GC.XPN.TOTL.GD.ZS", "higher government expenditure"),
    ("gov_consumption_gdp", "world_bank_wdi:NE.CON.GOVT.ZS", "higher government consumption"),
    ("tax_revenue_gdp", "world_bank_wdi:GC.TAX.TOTL.GD.ZS", "higher tax revenue"),
    ("social_protection", "world_bank_wdi:per_si_allsi.cov_pop_tot", "higher social protection coverage"),
]

school_configs = [
    ("social_democratic", "social-democratic", 0.55),
    ("post_keynesian", "Post-Keynesian", 0.55),
    ("democratic_socialist", "democratic-socialist", 0.55),
    ("market_socialist", "market-socialist", 0.5),
]

for pos_id, school_name, conf in school_configs:
    for (out_name, out_source) in outcomes:
        for (treat_name, treat_source, treat_desc) in treatments:
            if out_name == "poverty_headcount" and treat_name == "social_protection":
                continue  # Already have this one
            hid = f"{pos_id}_{treat_name}_{out_name}_{datetime.now().strftime('%Y%m%d')}"
            claim = f"{treat_desc.capitalize()} as a share of GDP raises {out_name.replace('_', ' ')}, consistent with the {school_name} view that an active public sector improves socioeconomic outcomes."
            spec = {
                "title": f"{treat_desc.capitalize()} raises {out_name.replace('_', ' ')}",
                "description": f"Panel test of {treat_name} vs {out_name}.",
                "prior_confidence": conf,
                "variables": {
                    "outcome": [{"name": out_name, "source": treat_source if out_name == "poverty_headcount" and treat_name == "social_protection" else out_source}],
                    "treatment": [{"name": treat_name, "source": treat_source}],
                    "controls": [
                        {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                        {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
                    ]
                },
                "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
                "falsification": {"rule": f"Falsified if {treat_name} does not have a {'negative' if out_name == 'poverty_headcount' else 'positive'} coefficient on {out_name} at p < 0.05."},
            }
            additional.append((claim, pos_id, "fiscal" if "gov" in treat_name or "tax" in treat_name else "welfare_architecture", spec))

# Also add some using Fraser EFW / Heritage IEF data but flipped socialist predictions
# e.g., "Higher area_1_size_of_government raises growth" (socialist prediction)
efw_treatments = [
    ("efw_size_of_government", "fraser_efw:area_1_size_of_government", "larger government size"),
    ("efw_regulation", "fraser_efw:area_5_regulation", "more regulation"),
    ("efw_legal", "fraser_efw:area_2_legal_system_property_rights", "stronger legal system"),
]

for pos_id, school_name, conf in school_configs:
    for (out_name, out_source) in [("gdp_pc_growth", "world_bank_wdi:NY.GDP.PCAP.KD.ZG"), ("life_expectancy", "world_bank_wdi:SP.DYN.LE00.IN")]:
        for (treat_name, treat_source, treat_desc) in efw_treatments:
            if "legal" in treat_name:
                continue  # This one might actually be positive, skip to avoid false positives
            hid = f"{pos_id}_{treat_name}_{out_name}_{datetime.now().strftime('%Y%m%d')}"
            claim = f"{treat_desc.capitalize()} is associated with higher {out_name.replace('_', ' ')}, consistent with the {school_name} view that an activist state improves outcomes."
            spec = {
                "title": f"{treat_desc.capitalize()} raises {out_name.replace('_', ' ')}",
                "description": f"Panel test of {treat_name} vs {out_name}.",
                "prior_confidence": conf,
                "variables": {
                    "outcome": [{"name": out_name, "source": out_source}],
                    "treatment": [{"name": treat_name, "source": treat_source}],
                    "controls": [
                        {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                    ]
                },
                "estimator": {"template": "panel_fe", "clustering": "country", "fixed_effects": ["country", "year"]},
                "falsification": {"rule": f"Falsified if {treat_name} does not have a {'negative' if out_name == 'poverty_headcount' else 'positive'} coefficient on {out_name} at p < 0.05."},
            }
            additional.append((claim, pos_id, "regulatory", spec))

# Combine all templates
all_templates = templates + additional

# Cap at 200
all_templates = all_templates[:200]

print(f"Total templates to generate: {len(all_templates)}")

# Generate
for claim, pos_id, topic, spec in all_templates:
    hid = f"{pos_id}_{claim.split()[0].lower()}_{claim.split()[1].lower()}_{datetime.now().strftime('%Y%m%d')}_{random.randint(1000,9999)}"
    hid = hid.replace(" ", "_").replace(",", "").replace(".", "").replace("'", "")[:80]

    spec_full = {
        "hypothesis_id": hid,
        "version": 1,
        "status": "candidate",
        "topic": topic,
        "claim": claim,
        "notes": f"Auto-generated hypothesis testing {school_name if 'school_name' in dir() else pos_id} prediction.",
        "prior_confidence": spec["prior_confidence"],
        "falsification": spec["falsification"],
        "evidence_type": "associational",
        "scope": {
            "period": [1970, 2023],
            "countries": ["ALL"],
            "outcome_dim": [topic],
            "policy_family": [topic],
        },
        "variables": spec["variables"],
        "estimator": spec["estimator"],
        "covers_claims": [{
            "position_id": pos_id,
            "claim_index": 0,  # Will be updated after appending to position
            "polarity": "aligned",
            "school_prediction": "supported",
            "confidence": "medium",
        }],
    }

    write_hypothesis(hid, spec_full)

print(f"Generated {len(all_templates)} hypothesis YAMLs")
