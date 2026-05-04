#!/usr/bin/env python3
"""Generate ~200 socialist/Marxist hypotheses using ONLY valid data series."""

import yaml
import random
from pathlib import Path
from datetime import datetime

REPO = Path(__file__).resolve().parents[1]
HYP_ROOT = REPO / "hypotheses"

random.seed(42)

def write_hypothesis(hid, spec, topic):
    out_dir = HYP_ROOT / topic
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / f"{hid}.yaml", "w") as f:
        yaml.dump(spec, f, sort_keys=False, allow_unicode=True)

def clean_hid(prefix):
    return prefix.replace(" ", "_").replace(",", "").replace(".", "").replace("'", "").replace("-", "_").replace("(", "").replace(")", "")[:80]

schools = {
    "social_democratic": ("Social Democratic", 0.55),
    "post_keynesian": ("Post-Keynesian", 0.55),
    "democratic_socialist": ("Democratic Socialist", 0.55),
    "market_socialist": ("Market Socialist", 0.5),
    "mmt": ("MMT", 0.5),
    "marxian": ("Marxian", 0.5),
    "marxist_leninist": ("Marxist-Leninist", 0.5),
    "degrowth": ("Degrowth", 0.5),
    "eco_socialist": ("Eco-Socialist", 0.55),
}

# VALID WDI series only
outcomes = [
    ("gdp_pc_growth", "world_bank_wdi:NY.GDP.PCAP.KD.ZG", "GDP per capita growth"),
    ("gdp_growth", "world_bank_wdi:NY.GDP.MKTP.KD.ZG", "GDP growth"),
    ("life_expectancy", "world_bank_wdi:SP.DYN.LE00.IN", "life expectancy"),
    ("employment_rate", "world_bank_wdi:SL.EMP.TOTL.SP.ZS", "employment rate"),
    ("poverty_headcount", "world_bank_wdi:SI.POV.DDAY", "extreme poverty headcount"),
    ("gini", "world_bank_wdi:SI.POV.GINI", "Gini coefficient"),
    ("infant_mortality", "world_bank_wdi:SP.DYN.IMRT.IN", "infant mortality"),
    ("primary_enrollment", "world_bank_wdi:SE.PRM.ENRR", "primary school enrollment"),
    ("electricity_access", "world_bank_wdi:EG.ELC.ACCS.ZS", "electricity access"),
    ("energy_use_pc", "world_bank_wdi:EG.USE.PCAP.KG.OE", "energy use per capita"),
    ("unemployment", "world_bank_wdi:SL.UEM.TOTL.ZS", "unemployment rate"),
    ("maternal_mortality", "world_bank_wdi:SH.STA.MMRT", "maternal mortality"),
    ("under5_mortality", "world_bank_wdi:SH.DYN.MORT", "under-5 mortality"),
]

wdi_treatments = [
    ("gov_exp_gdp", "world_bank_wdi:GC.XPN.TOTL.GD.ZS", "government expenditure"),
    ("gov_consumption_gdp", "world_bank_wdi:NE.CON.GOVT.ZS", "government consumption"),
    ("tax_revenue_gdp", "world_bank_wdi:GC.TAX.TOTL.GD.ZS", "tax revenue"),
    ("health_exp_gdp", "world_bank_wdi:SH.XPD.CHEX.GD.ZS", "health expenditure"),
    ("education_exp_gdp", "world_bank_wdi:SE.XPD.TOTL.GD.ZS", "education expenditure"),
    ("investment_gdp", "world_bank_wdi:NE.GDI.FTOT.ZS", "gross capital formation"),
    ("fiscal_balance_gdp", "world_bank_wdi:GC.NLD.TOTL.GD.ZS", "fiscal balance"),
    ("gov_debt_gdp", "world_bank_wdi:GC.DOD.TOTL.GD.ZS", "government debt"),
]

# EFW treatments - socialist prediction: smaller govt / less freedom = better
efw_treatments = [
    ("efw_size_of_government", "fraser_efw:area_1_size_of_government", "size of government"),
    ("efw_regulation", "fraser_efw:area_5_regulation", "regulation"),
    ("efw_summary", "fraser_efw:efw_summary", "economic freedom summary"),
]

# Heritage IEF treatments
ief_treatments = [
    ("ief_government_spending", "heritage_ief:government_spending", "government spending"),
    ("ief_tax_burden", "heritage_ief:tax_burden", "tax burden"),
    ("ief_labor_freedom", "heritage_ief:labor_freedom", "labor freedom"),
    ("ief_overall", "heritage_ief:overall_score", "overall economic freedom"),
]

def topic_for(treat_name, out_name):
    if "gov" in treat_name or "tax" in treat_name or "fiscal" in treat_name or "debt" in treat_name:
        return "fiscal"
    if "health" in treat_name or "life" in out_name or "mortality" in out_name:
        return "healthcare"
    if "education" in treat_name or "enrollment" in out_name:
        return "institutional_quality"
    if "electricity" in out_name or "energy" in out_name:
        return "energy"
    if "gini" in out_name or "poverty" in out_name:
        return "distribution"
    if "employment" in out_name or "unemployment" in out_name or "labor" in treat_name:
        return "labour"
    if "efw" in treat_name or "ief" in treat_name:
        return "regulatory"
    return "growth"

def direction_for(out_name):
    if out_name in ["poverty_headcount", "infant_mortality", "gini", "unemployment", "maternal_mortality", "under5_mortality", "energy_use_pc"]:
        return "negative"
    return "positive"

# Generate systematically - aim for ~22 per school
count = 0
max_per_school = 22

for pos_id, (school_name, conf) in schools.items():
    school_count = 0

    # WDI x WDI combos
    for (out_name, out_source, out_desc) in outcomes:
        for (treat_name, treat_source, treat_desc) in wdi_treatments:
            if school_count >= max_per_school or count >= 200:
                break
            direction = direction_for(out_name)

            # Skip redundant: fiscal balance with growth is already well-tested
            if treat_name == "fiscal_balance_gdp" and out_name in ["gdp_pc_growth", "gdp_growth"]:
                continue

            claim = f"Higher {treat_desc} as a share of GDP is associated with {'lower' if direction == 'negative' else 'higher'} {out_desc}, consistent with the {school_name} view that an active public sector improves socioeconomic outcomes."
            topic = topic_for(treat_name, out_name)
            hid = clean_hid(f"{pos_id}_{treat_name}_{out_name}_{datetime.now().strftime('%Y%m%d')}_{random.randint(1000,9999)}")

            spec = {
                "hypothesis_id": hid,
                "version": 1,
                "status": "candidate",
                "topic": topic,
                "claim": claim,
                "notes": f"Auto-generated hypothesis testing {school_name} prediction using WDI panel.",
                "prior_confidence": conf,
                "falsification": {
                    "rule": f"Falsified if {treat_name} does not have a {direction} coefficient on {out_name} at p < 0.05 in a panel with country and year fixed effects."
                },
                "evidence_type": "associational",
                "scope": {
                    "period": [1970, 2023],
                    "countries": ["ALL"],
                    "outcome_dim": [topic],
                    "policy_family": [topic],
                },
                "variables": {
                    "outcome": [{"name": out_name, "source": out_source}],
                    "treatment": [{"name": treat_name, "source": treat_source}],
                    "controls": [
                        {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                        {"name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
                        {"name": "population_growth", "source": "world_bank_wdi:SP.POP.GROW"},
                    ]
                },
                "estimator": {
                    "template": "panel_fe",
                    "clustering": "country",
                    "fixed_effects": ["country", "year"],
                },
                "covers_claims": [{
                    "position_id": pos_id,
                    "claim_index": 0,
                    "polarity": "aligned",
                    "school_prediction": "supported",
                    "confidence": "medium",
                }],
            }
            write_hypothesis(hid, spec, topic)
            school_count += 1
            count += 1
        if school_count >= max_per_school or count >= 200:
            break

    # EFW/ Heritage combos
    if school_count < max_per_school and count < 200:
        for (out_name, out_source, out_desc) in outcomes[:6]:
            for (treat_name, treat_source, treat_desc) in efw_treatments + ief_treatments:
                if school_count >= max_per_school or count >= 200:
                    break
                direction = direction_for(out_name)
                # For EFW, higher score = more freedom = smaller govt, so socialist predicts negative
                if "efw" in treat_name or "ief" in treat_name:
                    direction = "negative"

                claim = f"Higher {treat_desc} is associated with {'lower' if direction == 'negative' else 'higher'} {out_desc}, consistent with the {school_name} view that market-liberal policies are detrimental to socioeconomic outcomes."
                topic = topic_for(treat_name, out_name)
                hid = clean_hid(f"{pos_id}_{treat_name}_{out_name}_{datetime.now().strftime('%Y%m%d')}_{random.randint(1000,9999)}")

                spec = {
                    "hypothesis_id": hid,
                    "version": 1,
                    "status": "candidate",
                    "topic": topic,
                    "claim": claim,
                    "notes": f"Auto-generated hypothesis testing {school_name} prediction using EFW/Heritage panel.",
                    "prior_confidence": conf,
                    "falsification": {
                        "rule": f"Falsified if {treat_name} does not have a {direction} coefficient on {out_name} at p < 0.05."
                    },
                    "evidence_type": "associational",
                    "scope": {
                        "period": [1970, 2023],
                        "countries": ["ALL"],
                        "outcome_dim": [topic],
                        "policy_family": [topic],
                    },
                    "variables": {
                        "outcome": [{"name": out_name, "source": out_source}],
                        "treatment": [{"name": treat_name, "source": treat_source}],
                        "controls": [
                            {"name": "initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                        ]
                    },
                    "estimator": {
                        "template": "panel_fe",
                        "clustering": "country",
                        "fixed_effects": ["country", "year"],
                    },
                    "covers_claims": [{
                        "position_id": pos_id,
                        "claim_index": 0,
                        "polarity": "aligned",
                        "school_prediction": "supported",
                        "confidence": "medium",
                    }],
                }
                write_hypothesis(hid, spec, topic)
                school_count += 1
                count += 1
            if school_count >= max_per_school or count >= 200:
                break

print(f"Generated {count} hypothesis YAMLs")
