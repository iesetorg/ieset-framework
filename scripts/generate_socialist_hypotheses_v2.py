#!/usr/bin/env python3
"""Generate ~200 socialist/Marxist hypotheses."""

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

# Schools and their framing
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

# WDI outcome variables
outcomes = [
    ("gdp_pc_growth", "world_bank_wdi:NY.GDP.PCAP.KD.ZG", "GDP per capita growth"),
    ("gdp_growth", "world_bank_wdi:NY.GDP.MKTP.KD.ZG", "GDP growth"),
    ("life_expectancy", "world_bank_wdi:SP.DYN.LE00.IN", "life expectancy"),
    ("employment_rate", "world_bank_wdi:SL.EMP.TOTL.SP.ZS", "employment rate"),
    ("poverty_headcount", "world_bank_wdi:SI.POV.DDAY", "extreme poverty headcount"),
    ("gini", "world_bank_wdi:SI.POV.GINI", "Gini coefficient"),
    ("infant_mortality", "world_bank_wdi:SP.DYN.IMRT.IN", "infant mortality"),
    ("mean_years_schooling", "world_bank_wdi:BAR.SCHL.15UP", "mean years of schooling"),
    ("renewable_share", "world_bank_wdi:EG.FEC.RNEW.ZS", "renewable energy share"),
    ("co2_pc", "world_bank_wdi:EN.ATM.CO2E.PC", "CO2 emissions per capita"),
]

# WDI treatment variables (socialist-friendly framings)
wdi_treatments = [
    ("gov_exp_gdp", "world_bank_wdi:GC.XPN.TOTL.GD.ZS", "government expenditure"),
    ("gov_consumption_gdp", "world_bank_wdi:NE.CON.GOVT.ZS", "government consumption"),
    ("tax_revenue_gdp", "world_bank_wdi:GC.TAX.TOTL.GD.ZS", "tax revenue"),
    ("social_protection", "world_bank_wdi:per_si_allsi.cov_pop_tot", "social protection coverage"),
    ("health_exp_gdp", "world_bank_wdi:SH.XPD.CHEX.GD.ZS", "health expenditure"),
    ("education_exp_gdp", "world_bank_wdi:SE.XPD.TOTL.GD.ZS", "education expenditure"),
    ("public_investment", "world_bank_wdi:NE.GDI.FTOT.ZS", "gross capital formation"),
]

# Fraser EFW treatments (socialist prediction: higher = better for some, worse for others)
efw_treatments = [
    ("efw_size_of_government", "fraser_efw:area_1_size_of_government", "size of government"),
    ("efw_regulation", "fraser_efw:area_5_regulation", "regulation"),
    ("efw_sound_money", "fraser_efw:area_3_sound_money", "sound money"),
]

# Heritage IEF treatments
heritage_treatments = [
    ("ief_government_spending", "heritage_ief:government_spending", "government spending"),
    ("ief_tax_burden", "heritage_ief:tax_burden", "tax burden"),
    ("ief_labor_freedom", "heritage_ief:labor_freedom", "labor freedom"),
]

# Topic mapping
def topic_for(treat_name, out_name):
    if "gov" in treat_name or "tax" in treat_name or "public" in treat_name:
        return "fiscal"
    if "health" in treat_name or "life" in out_name or "mortality" in out_name:
        return "healthcare"
    if "education" in treat_name or "school" in out_name:
        return "institutional_quality"
    if "renewable" in out_name or "co2" in out_name or "energy" in out_name:
        return "energy"
    if "gini" in out_name or "poverty" in out_name:
        return "distribution"
    if "employment" in out_name or "labor" in treat_name:
        return "labour"
    if "efw" in treat_name or "ief" in treat_name:
        return "regulatory"
    return "growth"

def direction_for(out_name):
    if out_name in ["poverty_headcount", "infant_mortality", "gini", "co2_pc"]:
        return "negative"
    return "positive"

def claim_text(treat_desc, out_desc, school_name, direction):
    if direction == "negative":
        return f"Higher {treat_desc} reduces {out_desc}, consistent with the {school_name} view that an active public sector improves socioeconomic outcomes."
    else:
        return f"Higher {treat_desc} raises {out_desc}, consistent with the {school_name} view that an active public sector improves socioeconomic outcomes."

# Generate hypotheses
count = 0
for pos_id, (school_name, conf) in schools.items():
    # WDI x WDI combos
    for (out_name, out_source, out_desc) in outcomes:
        for (treat_name, treat_source, treat_desc) in wdi_treatments:
            if count >= 200:
                break
            direction = direction_for(out_name)
            claim = claim_text(treat_desc, out_desc, school_name, direction)
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
            count += 1
        if count >= 200:
            break

    # EFW x WDI combos (socialist prediction: bigger govt = better)
    if count < 200:
        for (out_name, out_source, out_desc) in outcomes[:4]:  # Only top 4 outcomes
            for (treat_name, treat_source, treat_desc) in efw_treatments:
                if count >= 200:
                    break
                # For socialist schools: they might claim larger government / less regulation is better
                # But actually EFW area_1_size_of_government is scored so HIGHER = smaller govt
                # So socialist prediction would be: higher score = worse outcomes (negative coef)
                direction = "negative" if "size" in treat_name or "regulation" in treat_name else direction_for(out_name)
                claim = f"Larger {treat_desc} (lower Fraser score) is associated with better {out_desc}, consistent with the {school_name} view."
                topic = topic_for(treat_name, out_name)
                hid = clean_hid(f"{pos_id}_{treat_name}_{out_name}_{datetime.now().strftime('%Y%m%d')}_{random.randint(1000,9999)}")

                spec = {
                    "hypothesis_id": hid,
                    "version": 1,
                    "status": "candidate",
                    "topic": topic,
                    "claim": claim,
                    "notes": f"Auto-generated hypothesis testing {school_name} prediction using Fraser EFW panel.",
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
                count += 1
            if count >= 200:
                break

print(f"Generated {count} hypothesis YAMLs")
