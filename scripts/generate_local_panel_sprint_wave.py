#!/usr/bin/env python3
"""Generate a high-throughput local-data panel sprint wave.

This wave is intentionally hypothesis-only: it does not create school
scoreboard links. That lets us complete a large batch of pre-registered tests
without touching fragile reciprocal position indexes.
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
WAVE = "local_panel_sprint_wave_2026-05-03"

COUNTRIES = [
    "ARG", "AUS", "AUT", "BEL", "BRA", "CAN", "CHE", "CHL", "CHN", "COL",
    "CRI", "CZE", "DEU", "DNK", "EGY", "ESP", "EST", "FIN", "FRA", "GBR",
    "GHA", "GRC", "HUN", "IDN", "IND", "IRL", "ISR", "ITA", "JPN", "KEN",
    "KOR", "LTU", "LVA", "MAR", "MEX", "MYS", "NGA", "NLD", "NOR", "NZL",
    "PER", "PHL", "POL", "PRT", "SGP", "SVK", "SVN", "SWE", "THA", "TUR",
    "URY", "USA", "ZAF",
]

OUTCOMES = {
    "gdp_pc_growth": {
        "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG",
        "label": "annual real GDP per capita growth",
        "dim": ["gdp_growth", "productivity"],
        "positive": "faster real GDP per capita growth",
        "negative": "slower real GDP per capita growth",
    },
    "investment_share": {
        "source": "world_bank_wdi:NE.GDI.FTOT.ZS",
        "label": "gross fixed capital formation as a share of GDP",
        "dim": ["capital_flows", "gdp_growth"],
        "positive": "higher fixed-investment shares",
        "negative": "lower fixed-investment shares",
    },
    "gross_savings_share": {
        "source": "world_bank_wdi:NY.GNS.ICTR.ZS",
        "label": "gross domestic savings as a share of GDP",
        "dim": ["capital_flows", "gdp_growth"],
        "positive": "higher domestic savings shares",
        "negative": "lower domestic savings shares",
    },
    "private_credit_depth": {
        "source": "world_bank_wdi:FS.AST.PRVT.GD.ZS",
        "label": "domestic credit to the private sector as a share of GDP",
        "dim": ["financialisation", "capital_flows"],
        "positive": "deeper private-credit intermediation",
        "negative": "shallower private-credit intermediation",
    },
    "employment_rate": {
        "source": "world_bank_wdi:SL.EMP.TOTL.SP.ZS",
        "label": "employment-to-population ratio",
        "dim": ["employment_labour"],
        "positive": "higher employment rates",
        "negative": "lower employment rates",
    },
    "manufacturing_share": {
        "source": "world_bank_wdi:NV.IND.MANF.ZS",
        "label": "manufacturing value added as a share of GDP",
        "dim": ["industrial_capability", "productivity"],
        "positive": "higher manufacturing value-added shares",
        "negative": "lower manufacturing value-added shares",
    },
    "high_tech_exports": {
        "source": "world_bank_wdi:TX.VAL.TECH.MF.ZS",
        "label": "high-technology exports as a share of manufactured exports",
        "dim": ["industrial_capability", "trade_liberalisation"],
        "positive": "higher high-technology export intensity",
        "negative": "lower high-technology export intensity",
    },
    "fdi_inflows_share": {
        "source": "world_bank_wdi:BX.KLT.DINV.WD.GD.ZS",
        "label": "FDI net inflows as a share of GDP",
        "dim": ["capital_flows", "trade_liberalisation"],
        "positive": "higher FDI inflows as a share of GDP",
        "negative": "lower FDI inflows as a share of GDP",
    },
}

MECHANISMS = {
    "rule_of_law": {
        "topic": "institutional_quality",
        "name": "rule_of_law_wgi",
        "label": "WGI rule of law",
        "source": "wgi:RL.EST",
        "sign": "+",
        "policy_family": ["institutional_reform", "regulation"],
        "tags": ["rule_of_law", "property_rights", "contract_enforcement"],
        "channel": "institutional",
        "claim_prefix": "stronger rule-of-law scores",
        "theory": "property-rights and contract-enforcement channels",
        "prior": 0.58,
    },
    "regulatory_quality": {
        "topic": "regulatory",
        "name": "regulatory_quality_wgi",
        "label": "WGI regulatory quality",
        "source": "wgi:GOV_WGI_RQ.EST",
        "sign": "+",
        "policy_family": ["regulation", "competition_policy"],
        "tags": ["regulatory_quality", "market_entry", "business_freedom"],
        "channel": "regulatory",
        "claim_prefix": "higher regulatory-quality scores",
        "theory": "entry, competition, and policy-predictability channels",
        "prior": 0.56,
    },
    "control_corruption": {
        "topic": "institutional_quality",
        "name": "control_corruption_wgi",
        "label": "WGI control of corruption",
        "source": "wgi:CC.EST",
        "sign": "+",
        "policy_family": ["institutional_reform", "regulation"],
        "tags": ["control_of_corruption", "rent_seeking", "rule_bound_governance"],
        "channel": "institutional",
        "claim_prefix": "stronger control-of-corruption scores",
        "theory": "rent-seeking and rule-bound-allocation channels",
        "prior": 0.57,
    },
    "government_effectiveness": {
        "topic": "institutional_quality",
        "name": "government_effectiveness_wgi",
        "label": "WGI government effectiveness",
        "source": "wgi:GE.EST",
        "sign": "+",
        "policy_family": ["institutional_reform", "regulation"],
        "tags": ["government_effectiveness", "state_capacity", "policy_credibility"],
        "channel": "institutional",
        "claim_prefix": "more effective public administration",
        "theory": "state-capacity and policy-credibility channels",
        "prior": 0.57,
    },
    "capital_account_openness": {
        "topic": "trade",
        "name": "capital_account_openness",
        "label": "Chinn-Ito normalized capital-account openness",
        "source": "chinn_ito:kaopen_index_normalized",
        "sign": "+",
        "policy_family": ["trade_policy", "exchange_rate_regime", "regulation"],
        "tags": ["capital_account_openness", "financial_openness", "market_access"],
        "channel": "regulatory",
        "claim_prefix": "more open capital accounts",
        "theory": "capital mobility and allocative-efficiency channels",
        "prior": 0.54,
    },
    "trade_openness": {
        "topic": "trade",
        "name": "trade_openness",
        "label": "trade openness",
        "source": "world_bank_wdi:NE.TRD.GNFS.ZS",
        "sign": "+",
        "policy_family": ["trade_policy", "competition_policy"],
        "tags": ["trade_openness", "market_access", "competition"],
        "channel": "regulatory",
        "claim_prefix": "higher trade openness",
        "theory": "market-size, specialization, and competition channels",
        "prior": 0.55,
    },
    "inflation_rate": {
        "topic": "monetary",
        "name": "inflation_rate",
        "label": "annual CPI inflation",
        "source": "world_bank_wdi:FP.CPI.TOTL.ZG",
        "sign": "-",
        "policy_family": ["monetary_policy"],
        "tags": ["inflation", "sound_money", "monetary_stability"],
        "channel": "monetary",
        "claim_prefix": "higher inflation",
        "theory": "calculation, real-contracting, and monetary-stability channels",
        "prior": 0.56,
    },
    "broad_money_growth": {
        "topic": "monetary",
        "name": "broad_money_growth",
        "label": "broad-money growth",
        "source": "world_bank_wdi:FM.LBL.BMNY.ZG",
        "sign": "-",
        "policy_family": ["monetary_policy"],
        "tags": ["money_growth", "monetary_expansion", "sound_money"],
        "channel": "monetary",
        "claim_prefix": "faster broad-money growth",
        "theory": "monetary-expansion and intertemporal-distortion channels",
        "prior": 0.52,
    },
    "government_spending": {
        "topic": "fiscal",
        "name": "government_spending_share",
        "label": "government expenditure as a share of GDP",
        "source": "world_bank_wdi:GC.XPN.TOTL.GD.ZS",
        "sign": "-",
        "policy_family": ["fiscal_policy"],
        "tags": ["government_spending", "fiscal_size", "crowding_out"],
        "channel": "fiscal",
        "claim_prefix": "larger government-expenditure shares",
        "theory": "crowding-out and fiscal-expectations channels",
        "prior": 0.53,
    },
    "tax_revenue": {
        "topic": "fiscal",
        "name": "tax_revenue_share",
        "label": "tax revenue as a share of GDP",
        "source": "world_bank_wdi:GC.TAX.TOTL.GD.ZS",
        "sign": "-",
        "policy_family": ["fiscal_policy", "tax_policy"],
        "tags": ["tax_burden", "tax_revenue", "private_incentives"],
        "channel": "fiscal",
        "claim_prefix": "larger tax-revenue shares",
        "theory": "deadweight-loss and retained-earnings channels",
        "prior": 0.51,
    },
    "public_debt": {
        "topic": "fiscal",
        "name": "public_debt_share",
        "label": "central government debt as a share of GDP",
        "source": "world_bank_wdi:GC.DOD.TOTL.GD.ZS",
        "sign": "-",
        "policy_family": ["fiscal_policy"],
        "tags": ["public_debt", "debt_overhang", "fiscal_prudence"],
        "channel": "fiscal",
        "claim_prefix": "larger public-debt shares",
        "theory": "debt-overhang and sovereign-risk channels",
        "prior": 0.50,
    },
    "fiscal_balance": {
        "topic": "fiscal",
        "name": "fiscal_balance_share",
        "label": "government net lending/borrowing as a share of GDP",
        "source": "world_bank_wdi:GC.NLD.TOTL.GD.ZS",
        "sign": "+",
        "policy_family": ["fiscal_policy"],
        "tags": ["fiscal_balance", "deficit_discipline", "fiscal_prudence"],
        "channel": "fiscal",
        "claim_prefix": "stronger fiscal balances",
        "theory": "risk-premium and fiscal-expectations channels",
        "prior": 0.53,
    },
}

DESIGN = {
    "rule_of_law": ["gdp_pc_growth", "investment_share", "private_credit_depth", "high_tech_exports"],
    "regulatory_quality": ["gdp_pc_growth", "investment_share", "employment_rate", "manufacturing_share"],
    "control_corruption": ["gdp_pc_growth", "investment_share", "private_credit_depth", "high_tech_exports"],
    "government_effectiveness": ["gdp_pc_growth", "investment_share", "gross_savings_share", "manufacturing_share"],
    "capital_account_openness": ["gdp_pc_growth", "investment_share", "fdi_inflows_share", "high_tech_exports"],
    "trade_openness": ["gdp_pc_growth", "investment_share", "manufacturing_share", "high_tech_exports"],
    "inflation_rate": ["gdp_pc_growth", "investment_share", "employment_rate", "private_credit_depth"],
    "broad_money_growth": ["gdp_pc_growth", "investment_share", "gross_savings_share", "private_credit_depth"],
    "government_spending": ["gdp_pc_growth", "investment_share", "gross_savings_share", "manufacturing_share"],
    "tax_revenue": ["gdp_pc_growth", "investment_share", "employment_rate", "manufacturing_share"],
    "public_debt": ["gdp_pc_growth", "investment_share", "gross_savings_share", "private_credit_depth"],
    "fiscal_balance": ["gdp_pc_growth", "investment_share", "gross_savings_share", "employment_rate"],
}


def dump_yaml(doc: dict) -> str:
    return (
        "# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n"
        + yaml.safe_dump(doc, sort_keys=False, width=110, allow_unicode=False)
    )


def outcome_phrase(outcome: dict, sign: str) -> str:
    return outcome["positive"] if sign == "+" else outcome["negative"]


def controls_for(mechanism_id: str) -> list[dict]:
    controls = [
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
    if mechanism_id != "trade_openness":
        controls.append({
            "name": "trade_openness_control",
            "source": "world_bank_wdi:NE.TRD.GNFS.ZS",
            "transformation": "level",
            "notes": "External-openness control.",
        })
    if mechanism_id not in {"government_spending", "tax_revenue", "public_debt", "fiscal_balance"}:
        controls.append({
            "name": "government_consumption_control",
            "source": "world_bank_wdi:NE.CON.GOVT.ZS",
            "transformation": "level",
            "notes": "Fiscal-demand control.",
        })
    return controls


def build_spec(mechanism_id: str, outcome_id: str) -> dict:
    mechanism = MECHANISMS[mechanism_id]
    outcome = OUTCOMES[outcome_id]
    hid = f"local_panel_sprint_{mechanism_id}_{outcome_id}_20260503"
    direction = "positively" if mechanism["sign"] == "+" else "negatively"
    return {
        "hypothesis_id": hid,
        "version": 1,
        "status": "pre_registered",
        "topic": mechanism["topic"],
        "claim": (
            f"Across a pre-registered panel of OECD and major emerging-market economies from 1996 to 2023, "
            f"{mechanism['claim_prefix']} predict {outcome_phrase(outcome, mechanism['sign'])} after country "
            f"and year fixed effects and basic macro controls. This sprint test uses only local vintages and "
            f"does not create school-scoreboard links."
        ),
        "methodology_note": (
            "High-throughput local-data sprint wave. The spec is registered before estimation, uses only "
            "already-local vintages, and deliberately omits position covers_claims so hypothesis testing can "
            "advance without creating fragile school-scoreboard mappings."
        ),
        "evidence_type": "associational",
        "sample": {
            "countries": COUNTRIES,
            "period": [1996, 2023],
            "temporal_structure": "panel",
            "exclusion_rules": [
                "drop country-years missing outcome, treatment, or retained controls",
                "do not impute treatment values across countries",
                "treat as associational evidence unless a later causal design is registered",
            ],
        },
        "scope": {
            "period": [1996, 2023],
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
            "controls": controls_for(mechanism_id),
        },
        "intervention_channel": mechanism["channel"],
        "intervention_channel_justification": (
            f"The treatment operationalizes {mechanism['label']} as a time-varying policy or institutional "
            "proxy rather than an ex-post result screen."
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
                "expected_sign": mechanism["sign"],
                "p_max": 0.10,
                "min_observations": 30,
            },
        },
        "prior_confidence": mechanism["prior"],
        "disclosure": (
            "This sprint intentionally prioritizes throughput and may include broad proxies. Favorable "
            "selection risk is handled by committing the hypothesis, variables, sample, and direction before "
            "estimation; null and contrary results count."
        ),
        "steelman": f"hypotheses/steelman/{hid}.md",
        "notes": "Hypothesis-only sprint test; no school-scoreboard linkage is asserted.",
    }


def steelman_text(mechanism_id: str, outcome_id: str) -> str:
    mechanism = MECHANISMS[mechanism_id]
    outcome = OUTCOMES[outcome_id]
    hid = f"local_panel_sprint_{mechanism_id}_{outcome_id}_20260503"
    return f"""# Steelman - {hid}

The strongest objection is that {mechanism['label']} may proxy for omitted country-specific trends, income
level, administrative capacity, geography, or global-cycle exposure rather than {mechanism['theory']} itself.
Country and year fixed effects reduce some bias but do not prove causality.

A second objection is reverse causality: countries with {outcome['positive']} may find it easier to improve
policy and institutional scores. A supported result should therefore be treated as an associational hurdle,
not a final causal claim.

A third objection is measurement. The treatment is a broad proxy and may miss the precise mechanism a school
would defend. Null or contrary results count against this registered broad proxy, while sharper event studies
can be registered later.
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
            hid = f"local_panel_sprint_{mechanism_id}_{outcome_id}_20260503"
            spec_path = topic_dir / f"{hid}.yaml"
            if spec_path.exists() or (ROOT / "engine" / "runs" / hid).exists():
                raise SystemExit(f"Refusing to overwrite existing hypothesis/run: {hid}")
            spec_path.write_text(dump_yaml(build_spec(mechanism_id, outcome_id)))
            (STEELMAN / f"{hid}.md").write_text(steelman_text(mechanism_id, outcome_id))
            meta.append({
                "hypothesis_id": hid,
                "mechanism": mechanism_id,
                "outcome": outcome_id,
                "topic": mechanism["topic"],
                "expected_sign": mechanism["sign"],
            })

    ids = [row["hypothesis_id"] for row in meta]
    (AUDITS / f"{WAVE}.ids").write_text("\n".join(ids) + "\n")
    audit = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "methodology_gate": "hypothesis_specs_and_steelmen_created_before_estimation",
        "count": len(ids),
        "position_linkage": "none",
        "specs": meta,
    }
    (AUDITS / f"{WAVE}.json").write_text(json.dumps(audit, indent=2))
    lines = [
        "# Local Panel Sprint Wave - 2026-05-03",
        "",
        "## Methodology Gate",
        "",
        "- Hypothesis specs and steelmen are written before estimation.",
        "- The wave uses only already-local vintages.",
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
