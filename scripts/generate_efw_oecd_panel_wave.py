#!/usr/bin/env python3
"""Generate a lean OECD/market-economy EFW panel wave.

This is the high-throughput, lower-friction companion to the broader EFW
market panel wave. It uses fewer countries and a deliberately lean control set
to reduce listwise-deletion failures while preserving the preregister-then-run
methodology gate.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
HYPOTHESES = ROOT / "hypotheses"
STEELMAN = HYPOTHESES / "steelman"
AUDITS = ROOT / "engine" / "audits"
WAVE = "efw_oecd_panel_wave_2026-05-03"
STAMP = "20260503"

COUNTRIES = [
    "AUS", "AUT", "BEL", "CAN", "CHE", "CHL", "COL", "CRI", "CZE", "DEU",
    "DNK", "ESP", "EST", "FIN", "FRA", "GBR", "GRC", "HUN", "IRL", "ISR",
    "ITA", "JPN", "KOR", "LTU", "LVA", "MEX", "NLD", "NOR", "NZL", "POL",
    "PRT", "ROU", "SGP", "SVK", "SVN", "SWE", "TUR", "URY", "USA", "ZAF",
]

MECHANISMS = {
    "efw_summary": {
        "topic": "institutional_quality",
        "name": "efw_summary_index",
        "source": "fraser_efw:summary_index",
        "label": "Fraser EFW summary index",
        "claim_prefix": "higher overall economic-freedom scores",
        "channel": "institutional",
        "policy_family": ["institutional_reform", "regulation", "trade_policy"],
        "tags": ["economic_freedom", "market_order", "property_rights"],
        "theory": "property-rights, price-system, and entry-competition channels",
        "prior": 0.58,
    },
    "size_government": {
        "topic": "fiscal",
        "name": "efw_size_of_government_score",
        "source": "fraser_efw:size_of_government",
        "label": "Fraser EFW size-of-government score",
        "claim_prefix": "higher size-of-government freedom scores",
        "channel": "fiscal",
        "policy_family": ["fiscal_policy", "tax_policy"],
        "tags": ["smaller_government", "tax_burden", "fiscal_freedom"],
        "theory": "tax-wedge, crowding-out, and private-allocation channels",
        "prior": 0.54,
    },
    "property_rights": {
        "topic": "institutional_quality",
        "name": "efw_legal_system_property_rights_score",
        "source": "fraser_efw:legal_system_property_rights",
        "label": "Fraser EFW legal-system and property-rights score",
        "claim_prefix": "stronger legal-system and property-rights scores",
        "channel": "institutional",
        "policy_family": ["institutional_reform", "regulation"],
        "tags": ["property_rights", "rule_of_law", "contract_enforcement"],
        "theory": "secure-title, contract-enforcement, and capital-formation channels",
        "prior": 0.59,
    },
    "sound_money": {
        "topic": "monetary",
        "name": "efw_sound_money_score",
        "source": "fraser_efw:sound_money",
        "label": "Fraser EFW sound-money score",
        "claim_prefix": "higher sound-money scores",
        "channel": "monetary",
        "policy_family": ["monetary_policy"],
        "tags": ["sound_money", "inflation_discipline", "monetary_stability"],
        "theory": "monetary-calculation, long-contracting, and price-stability channels",
        "prior": 0.57,
    },
    "trade_freedom": {
        "topic": "trade",
        "name": "efw_trade_freedom_score",
        "source": "fraser_efw:freedom_to_trade_internationally",
        "label": "Fraser EFW freedom-to-trade-internationally score",
        "claim_prefix": "higher international-trade-freedom scores",
        "channel": "regulatory",
        "policy_family": ["trade_policy", "competition_policy"],
        "tags": ["trade_freedom", "market_access", "competition"],
        "theory": "market-size, specialization, import-discipline, and export-learning channels",
        "prior": 0.56,
    },
    "regulation": {
        "topic": "regulatory",
        "name": "efw_regulation_score",
        "source": "fraser_efw:regulation",
        "label": "Fraser EFW regulation score",
        "claim_prefix": "higher regulation-freedom scores",
        "channel": "regulatory",
        "policy_family": ["regulation", "competition_policy"],
        "tags": ["regulatory_freedom", "market_entry", "competition"],
        "theory": "entry, labor-market flexibility, credit allocation, and competition channels",
        "prior": 0.55,
    },
}

OUTCOMES = {
    "gdp_pc_growth": {
        "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG",
        "label": "annual real GDP per capita growth",
        "dim": ["gdp_growth", "productivity"],
        "expected_sign": "+",
        "direction_phrase": "faster real GDP per capita growth",
    },
    "gdp_growth": {
        "source": "world_bank_wdi:NY.GDP.MKTP.KD.ZG",
        "label": "annual real GDP growth",
        "dim": ["gdp_growth", "productivity"],
        "expected_sign": "+",
        "direction_phrase": "faster real GDP growth",
    },
    "gni_pc_growth": {
        "source": "world_bank_wdi:NY.GNP.PCAP.KD.ZG",
        "label": "annual real GNI per capita growth",
        "dim": ["gdp_growth", "productivity"],
        "expected_sign": "+",
        "direction_phrase": "faster real GNI per capita growth",
    },
    "investment_share": {
        "source": "world_bank_wdi:NE.GDI.FTOT.ZS",
        "label": "gross fixed capital formation as a share of GDP",
        "dim": ["capital_flows", "gdp_growth"],
        "expected_sign": "+",
        "direction_phrase": "higher fixed-investment shares",
    },
    "gross_capital_formation": {
        "source": "world_bank_wdi:NE.GDI.TOTL.ZS",
        "label": "gross capital formation as a share of GDP",
        "dim": ["capital_flows", "gdp_growth"],
        "expected_sign": "+",
        "direction_phrase": "higher gross-capital-formation shares",
    },
    "gross_savings_share": {
        "source": "world_bank_wdi:NY.GNS.ICTR.ZS",
        "label": "gross domestic savings as a share of GDP",
        "dim": ["capital_flows", "gdp_growth"],
        "expected_sign": "+",
        "direction_phrase": "higher domestic savings shares",
    },
    "private_credit_depth": {
        "source": "world_bank_wdi:FS.AST.PRVT.GD.ZS",
        "label": "domestic credit to the private sector as a share of GDP",
        "dim": ["financialisation", "capital_flows"],
        "expected_sign": "+",
        "direction_phrase": "deeper private-credit intermediation",
    },
    "employment_rate": {
        "source": "world_bank_wdi:SL.EMP.TOTL.SP.ZS",
        "label": "employment-to-population ratio",
        "dim": ["employment_labour"],
        "expected_sign": "+",
        "direction_phrase": "higher employment rates",
    },
    "industry_employment": {
        "source": "world_bank_wdi:SL.IND.EMPL.ZS",
        "label": "industry employment as a share of total employment",
        "dim": ["employment_labour", "industrial_capability"],
        "expected_sign": "+",
        "direction_phrase": "higher industry-employment shares",
    },
    "manufacturing_share": {
        "source": "world_bank_wdi:NV.IND.MANF.ZS",
        "label": "manufacturing value added as a share of GDP",
        "dim": ["industrial_capability", "productivity"],
        "expected_sign": "+",
        "direction_phrase": "higher manufacturing value-added shares",
    },
    "services_value_added": {
        "source": "world_bank_wdi:NV.SRV.TOTL.ZS",
        "label": "services value added as a share of GDP",
        "dim": ["productivity", "industrial_capability"],
        "expected_sign": "+",
        "direction_phrase": "higher services value-added shares",
    },
    "high_tech_exports": {
        "source": "world_bank_wdi:TX.VAL.TECH.MF.ZS",
        "label": "high-technology exports as a share of manufactured exports",
        "dim": ["industrial_capability", "trade_liberalisation"],
        "expected_sign": "+",
        "direction_phrase": "higher high-technology export intensity",
    },
    "fdi_inflows_share": {
        "source": "world_bank_wdi:BX.KLT.DINV.WD.GD.ZS",
        "label": "FDI net inflows as a share of GDP",
        "dim": ["capital_flows", "trade_liberalisation"],
        "expected_sign": "+",
        "direction_phrase": "higher FDI inflows as a share of GDP",
    },
    "export_growth": {
        "source": "world_bank_wdi:NE.EXP.GNFS.KD.ZG",
        "label": "real exports of goods and services growth",
        "dim": ["trade_liberalisation", "gdp_growth"],
        "expected_sign": "+",
        "direction_phrase": "faster real export growth",
    },
    "life_expectancy": {
        "source": "world_bank_wdi:SP.DYN.LE00.IN",
        "label": "life expectancy at birth",
        "dim": ["life_expectancy_health", "gdp_growth"],
        "expected_sign": "+",
        "direction_phrase": "higher life expectancy",
    },
    "child_mortality": {
        "source": "world_bank_wdi:SH.DYN.MORT",
        "label": "under-five mortality rate",
        "dim": ["life_expectancy_health", "poverty_inequality"],
        "expected_sign": "-",
        "direction_phrase": "lower under-five mortality",
    },
    "inflation_rate": {
        "source": "world_bank_wdi:FP.CPI.TOTL.ZG",
        "label": "annual CPI inflation",
        "dim": ["inflation", "currency_purchasing_power"],
        "expected_sign": "-",
        "direction_phrase": "lower annual CPI inflation",
    },
    "nonperforming_loans": {
        "source": "world_bank_wdi:FB.AST.NPER.ZS",
        "label": "bank nonperforming loans as a share of gross loans",
        "dim": ["financial_crisis", "financialisation"],
        "expected_sign": "-",
        "direction_phrase": "lower bank nonperforming-loan shares",
    },
}

DESIGN = {mechanism_id: list(OUTCOMES) for mechanism_id in MECHANISMS}


def dump_yaml(doc: dict) -> str:
    return (
        "# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n"
        + yaml.safe_dump(doc, sort_keys=False, width=110, allow_unicode=False)
    )


def controls_for(_mechanism_id: str, _outcome_id: str) -> list[dict]:
    return [
        {
            "name": "log_gdp_pc_ppp",
            "source": "world_bank_wdi:NY.GDP.PCAP.PP.KD",
            "transformation": "log",
            "notes": "Income-level control.",
        },
        {
            "name": "population_growth",
            "source": "world_bank_wdi:SP.POP.GROW",
            "transformation": "level",
            "notes": "Demographic pressure control.",
        },
    ]


def build_spec(mechanism_id: str, outcome_id: str) -> dict:
    mechanism = MECHANISMS[mechanism_id]
    outcome = OUTCOMES[outcome_id]
    hid = f"efw_oecd_panel_{mechanism_id}_{outcome_id}_{STAMP}"
    direction = "positively" if outcome["expected_sign"] == "+" else "negatively"
    return {
        "hypothesis_id": hid,
        "version": 1,
        "status": "pre_registered",
        "topic": mechanism["topic"],
        "claim": (
            f"Across a narrower pre-registered OECD and market-economy peer panel from 1970 to 2023, "
            f"{mechanism['claim_prefix']} predict {outcome['direction_phrase']} after country and year fixed "
            "effects plus lean income and demographic controls. This is a hypothesis-only screen and does not "
            "create school-scoreboard links."
        ),
        "methodology_note": (
            "Lean EFW panel wave using local Fraser EFW and WDI vintages. This wave deliberately uses fewer "
            "countries and fewer controls than the broad market panel to reduce preventable listwise-deletion "
            "failures; the sample, variables, expected direction, and threshold are registered before estimation."
        ),
        "evidence_type": "associational",
        "sample": {
            "countries": COUNTRIES,
            "period": [1970, 2023],
            "temporal_structure": "panel",
            "exclusion_rules": [
                "drop country-years missing outcome, treatment, or retained controls",
                "do not impute treatment values across countries",
                "treat as associational evidence unless a later causal/event design is registered",
            ],
        },
        "scope": {
            "period": [1970, 2023],
            "countries": ["OECD", "GLOBAL"],
            "outcome_dim": outcome["dim"],
            "policy_family": mechanism["policy_family"],
            "treatment_tags": mechanism["tags"],
        },
        "variables": {
            "outcome": [{
                "name": outcome_id,
                "source": outcome["source"],
                "transformation": "level",
                "notes": outcome["label"],
            }],
            "treatment": [{
                "name": mechanism["name"],
                "source": mechanism["source"],
                "transformation": "level",
                "notes": mechanism["label"],
            }],
            "controls": controls_for(mechanism_id, outcome_id),
        },
        "intervention_channel": mechanism["channel"],
        "intervention_channel_justification": (
            f"The treatment uses {mechanism['label']} as a time-varying policy/institutional proxy, not a "
            "movement label or ex-post outcome screen."
        ),
        "estimator": {
            "template": "panel_fe",
            "fixed_effects": ["country", "year"],
            "clustering": "country",
            "notes": "Two-way fixed effects with country-clustered standard errors.",
        },
        "falsification": {
            "rule": (
                f"SUPPORTED if the coefficient on {mechanism['name']} is {direction} signed at p<0.10 with "
                "at least 30 usable observations after listwise deletion. REFUTED if the coefficient is "
                "significantly opposite-signed at p<0.10. Otherwise PARTIAL."
            ),
            "test": f"panel_fe_{hid}",
            "threshold": {
                "expected_sign": outcome["expected_sign"],
                "p_max": 0.10,
                "min_observations": 30,
            },
        },
        "prior_confidence": mechanism["prior"],
        "disclosure": (
            "The design prioritizes throughput but preserves preregistration. Supported results are broad "
            "associational screens; null and contrary results count against the registered proxy."
        ),
        "steelman": f"hypotheses/steelman/{hid}.md",
        "notes": "Hypothesis-only lean EFW/OECD-market panel test; no school-scoreboard linkage is asserted.",
    }


def steelman_text(mechanism_id: str, outcome_id: str) -> str:
    mechanism = MECHANISMS[mechanism_id]
    outcome = OUTCOMES[outcome_id]
    hid = f"efw_oecd_panel_{mechanism_id}_{outcome_id}_{STAMP}"
    return f"""# Steelman - {hid}

The strongest objection is that {mechanism['label']} may proxy for prior income, historical institutions,
regional reform clusters, or country-specific modernization paths rather than {mechanism['theory']} itself.
Country and year fixed effects reduce some bias but do not identify a clean causal effect.

A second objection is sample selection. The narrower OECD/market-economy sample improves comparability and data
coverage, but it may not generalize to low-income or authoritarian settings.

A third objection is construct validity. EFW is a broad policy/institution index; null or contrary results count
against this broad registered proxy, while later event studies can test narrower mechanisms.
"""


def main() -> int:
    AUDITS.mkdir(parents=True, exist_ok=True)
    STEELMAN.mkdir(parents=True, exist_ok=True)
    meta = []
    for mechanism_id, outcomes in DESIGN.items():
        mechanism = MECHANISMS[mechanism_id]
        topic_dir = HYPOTHESES / mechanism["topic"]
        topic_dir.mkdir(parents=True, exist_ok=True)
        for outcome_id in outcomes:
            hid = f"efw_oecd_panel_{mechanism_id}_{outcome_id}_{STAMP}"
            spec_path = topic_dir / f"{hid}.yaml"
            run_path = ROOT / "engine" / "runs" / hid
            if spec_path.exists() or run_path.exists():
                raise SystemExit(f"Refusing to overwrite existing hypothesis/run: {hid}")
            spec_path.write_text(dump_yaml(build_spec(mechanism_id, outcome_id)))
            (STEELMAN / f"{hid}.md").write_text(steelman_text(mechanism_id, outcome_id))
            meta.append({
                "hypothesis_id": hid,
                "mechanism": mechanism_id,
                "outcome": outcome_id,
                "topic": mechanism["topic"],
                "expected_sign": OUTCOMES[outcome_id]["expected_sign"],
            })

    ids = [row["hypothesis_id"] for row in meta]
    (AUDITS / f"{WAVE}.ids").write_text("\n".join(ids) + "\n")
    audit = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "methodology_gate": "hypothesis_specs_and_steelmen_created_before_estimation",
        "count": len(ids),
        "position_linkage": "none",
        "sample_countries": COUNTRIES,
        "period": [1970, 2023],
        "specs": meta,
    }
    (AUDITS / f"{WAVE}.json").write_text(json.dumps(audit, indent=2))
    lines = [
        "# EFW OECD/Market Panel Wave - 2026-05-03",
        "",
        "## Methodology Gate",
        "",
        "- Hypothesis specs and steelmen are written before estimation.",
        "- The wave uses local Fraser EFW and WDI vintages.",
        "- The country sample is intentionally narrower than the broad market panel.",
        "- No `covers_claims` or position-scoreboard mappings are asserted.",
        "- Run artifacts must be created only after this wave is committed.",
        "",
        f"## Count: {len(ids)}",
        "",
    ]
    by_mechanism: dict[str, int] = defaultdict(int)
    for row in meta:
        by_mechanism[row["mechanism"]] += 1
    for mechanism_id in sorted(by_mechanism):
        lines.append(f"- {mechanism_id}: {by_mechanism[mechanism_id]}")
    lines.extend(["", "## Hypotheses", ""])
    for row in meta:
        lines.append(
            f"- `{row['hypothesis_id']}` | mechanism={row['mechanism']} | outcome={row['outcome']} | "
            f"expected_sign={row['expected_sign']}"
        )
    (AUDITS / f"{WAVE}.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"generated": len(ids), "ids": ids}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
