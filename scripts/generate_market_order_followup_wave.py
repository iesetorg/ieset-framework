#!/usr/bin/env python3
"""Generate a 20-spec market-order follow-up pre-registration wave.

This keeps the IESET loop intact:
  1. write hypothesis specs, steelmen, and reciprocal position links;
  2. commit those files as the pre-registration timestamp;
  3. only then run the estimators and publish result artifacts.

The wave deliberately uses a narrower OECD/market-peer sample than the first
market-order batch so tests are easier to satisfy with complete panel data.
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
POSITIONS = ROOT / "positions"
AUDITS = ROOT / "engine" / "audits"

WAVE = "market_order_followup_wave_2026-05-03"

COUNTRIES = [
    "AUS", "AUT", "BEL", "CAN", "CHE", "CHL", "CZE", "DEU", "DNK", "ESP",
    "EST", "FIN", "FRA", "GBR", "GRC", "HUN", "IRL", "ISR", "ITA", "JPN",
    "KOR", "LTU", "LVA", "MEX", "NLD", "NOR", "NZL", "POL", "PRT", "SVK",
    "SVN", "SWE", "USA",
]

OUTCOMES = {
    "private_investment_share": {
        "label": "private fixed investment as a share of GDP",
        "source": "world_bank_wdi:NE.GDI.FPRV.ZS",
        "dim": ["gdp_growth", "capital_flows"],
        "positive_phrase": "higher private fixed-investment shares",
        "negative_phrase": "lower private fixed-investment shares",
    },
    "gross_savings_share": {
        "label": "gross domestic savings as a share of GDP",
        "source": "world_bank_wdi:NY.GNS.ICTR.ZS",
        "dim": ["capital_flows", "gdp_growth"],
        "positive_phrase": "higher domestic savings shares",
        "negative_phrase": "lower domestic savings shares",
    },
    "gdp_pc_growth": {
        "label": "annual real GDP per capita growth",
        "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG",
        "dim": ["gdp_growth", "productivity"],
        "positive_phrase": "faster real GDP per capita growth",
        "negative_phrase": "slower real GDP per capita growth",
    },
    "manufacturing_share": {
        "label": "manufacturing value added as a share of GDP",
        "source": "world_bank_wdi:NV.IND.MANF.ZS",
        "dim": ["industrial_capability", "productivity"],
        "positive_phrase": "higher manufacturing value-added shares",
        "negative_phrase": "lower manufacturing value-added shares",
    },
    "private_credit_depth": {
        "label": "domestic credit to the private sector as a share of GDP",
        "source": "world_bank_wdi:FS.AST.PRVT.GD.ZS",
        "dim": ["financialisation", "capital_flows"],
        "positive_phrase": "deeper private credit intermediation",
        "negative_phrase": "shallower private credit intermediation",
    },
    "fdi_inflows_share": {
        "label": "foreign direct investment net inflows as a share of GDP",
        "source": "world_bank_wdi:BX.KLT.DINV.WD.GD.ZS",
        "dim": ["capital_flows", "trade_liberalisation"],
        "positive_phrase": "higher FDI inflows as a share of GDP",
        "negative_phrase": "lower FDI inflows as a share of GDP",
    },
    "high_tech_exports": {
        "label": "high-technology exports as a share of manufactured exports",
        "source": "world_bank_wdi:TX.VAL.TECH.MF.ZS",
        "dim": ["industrial_capability", "trade_liberalisation"],
        "positive_phrase": "higher high-technology export intensity",
        "negative_phrase": "lower high-technology export intensity",
    },
}

MECHANISMS = {
    "government_effectiveness": {
        "topic": "institutional_quality",
        "treatment_name": "government_effectiveness_wgi",
        "treatment_label": "WGI government effectiveness",
        "source": "wgi:GE.EST",
        "expected_sign": "+",
        "policy_family": ["institutional_reform", "regulation"],
        "treatment_tags": ["government_effectiveness", "state_capacity", "rule_bound_governance"],
        "positions": ["ordoliberal", "institutionalism", "classical_liberal", "empirical_pragmatist"],
        "claim_prefix": "more effective rule-bound public administration",
        "theory": "state-capacity, policy-credibility, and contract-enforcement channels",
        "prior": 0.60,
    },
    "capital_account_openness": {
        "topic": "trade",
        "treatment_name": "capital_account_openness",
        "treatment_label": "Chinn-Ito normalized capital-account openness",
        "source": "chinn_ito:kaopen_index_normalized",
        "expected_sign": "+",
        "policy_family": ["trade_policy", "exchange_rate_regime", "regulation"],
        "treatment_tags": ["capital_account_openness", "financial_openness", "market_access"],
        "positions": ["austrian", "classical_liberal", "ordoliberal", "empirical_pragmatist"],
        "claim_prefix": "more open capital accounts",
        "theory": "capital mobility, allocative-efficiency, and external-discipline channels",
        "prior": 0.55,
    },
    "fiscal_balance": {
        "topic": "fiscal",
        "treatment_name": "fiscal_balance_share",
        "treatment_label": "general government net lending/borrowing as a share of GDP",
        "source": "world_bank_wdi:GC.NLD.TOTL.GD.ZS",
        "expected_sign": "+",
        "policy_family": ["fiscal_policy"],
        "treatment_tags": ["fiscal_balance", "fiscal_prudence", "deficit_discipline"],
        "positions": ["austrian", "ordoliberal", "classical_liberal", "chicago_monetarism"],
        "claim_prefix": "stronger fiscal balances",
        "theory": "crowding-out, risk-premium, and fiscal-expectations channels",
        "prior": 0.54,
    },
    "public_debt": {
        "topic": "fiscal",
        "treatment_name": "public_debt_share",
        "treatment_label": "central government debt as a share of GDP",
        "source": "world_bank_wdi:GC.DOD.TOTL.GD.ZS",
        "expected_sign": "-",
        "policy_family": ["fiscal_policy"],
        "treatment_tags": ["public_debt", "debt_overhang", "fiscal_prudence"],
        "positions": ["austrian", "ordoliberal", "classical_liberal", "chicago_monetarism"],
        "claim_prefix": "larger public-debt shares",
        "theory": "debt-overhang, future-tax-expectation, and sovereign-risk channels",
        "prior": 0.52,
    },
    "government_consumption": {
        "topic": "fiscal",
        "treatment_name": "government_consumption_share",
        "treatment_label": "government final consumption expenditure as a share of GDP",
        "source": "world_bank_wdi:NE.CON.GOVT.ZS",
        "expected_sign": "-",
        "policy_family": ["fiscal_policy"],
        "treatment_tags": ["government_consumption", "fiscal_size", "crowding_out"],
        "positions": ["austrian", "ordoliberal", "classical_liberal"],
        "claim_prefix": "larger government-consumption shares",
        "theory": "resource-crowding, bureaucratic-consumption, and private-sector displacement channels",
        "prior": 0.51,
    },
}

DESIGN = {
    "government_effectiveness": [
        "private_investment_share", "gross_savings_share", "manufacturing_share", "gdp_pc_growth",
    ],
    "capital_account_openness": [
        "fdi_inflows_share", "private_investment_share", "high_tech_exports", "gdp_pc_growth",
    ],
    "fiscal_balance": [
        "private_investment_share", "gross_savings_share", "gdp_pc_growth", "private_credit_depth",
    ],
    "public_debt": [
        "private_investment_share", "gross_savings_share", "gdp_pc_growth", "private_credit_depth",
    ],
    "government_consumption": [
        "private_investment_share", "gross_savings_share", "manufacturing_share", "gdp_pc_growth",
    ],
}

POSITION_SCHOOLS = {
    "austrian": "Austrian",
    "chicago_monetarism": "Chicago monetarist",
    "classical_liberal": "Classical liberal",
    "ordoliberal": "Ordoliberal",
    "institutionalism": "Institutionalist",
    "empirical_pragmatist": "Empirical pragmatist",
}


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


def dump_yaml(doc: dict) -> str:
    return (
        "# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n"
        + yaml.safe_dump(doc, sort_keys=False, width=110, allow_unicode=False)
    )


def render_claim_block(claim: dict) -> str:
    return yaml.safe_dump([claim], sort_keys=False, width=110, allow_unicode=False)


def insert_claims(position_id: str, claims: list[dict]) -> list[int]:
    path = POSITIONS / f"{position_id}.yaml"
    doc = load_yaml(path)
    existing = doc.get("falsifiable_specific_claims") or []
    existing_by_hid = {
        claim.get("linked_hypothesis_id"): i
        for i, claim in enumerate(existing)
        if claim.get("linked_hypothesis_id")
    }
    indexes: list[int] = []
    new_claims: list[dict] = []
    for claim in claims:
        hid = claim["linked_hypothesis_id"]
        if hid in existing_by_hid:
            indexes.append(existing_by_hid[hid])
            continue
        indexes.append(len(existing) + len(new_claims))
        new_claims.append(claim)
    if not new_claims:
        return indexes

    text = path.read_text()
    start = text.index("falsifiable_specific_claims:")
    tail_candidates = []
    for marker in ("\nempirical_record_summary:", "\nscope_decisions:", "\nlinked_hypotheses:", "\nnotes:"):
        pos = text.find(marker, start)
        if pos != -1:
            tail_candidates.append(pos)
    insert_at = min(tail_candidates) if tail_candidates else len(text)
    block = "\n" + "".join(render_claim_block(claim) for claim in new_claims)
    path.write_text(text[:insert_at].rstrip() + block + "\n" + text[insert_at:].lstrip("\n"))
    return indexes


def outcome_text(outcome: dict, expected_sign: str) -> str:
    return outcome["positive_phrase"] if expected_sign == "+" else outcome["negative_phrase"]


def build_controls(mechanism_id: str) -> list[dict]:
    controls = [
        {
            "name": "log_gdp_pc_ppp",
            "source": "world_bank_wdi:NY.GDP.PCAP.PP.KD",
            "transformation": "log",
            "notes": "Income-level control to reduce development-level bias.",
        },
        {
            "name": "population_growth",
            "source": "world_bank_wdi:SP.POP.GROW",
            "transformation": "level",
            "notes": "Demographic pressure control.",
        },
    ]
    if mechanism_id != "capital_account_openness":
        controls.append(
            {
                "name": "trade_openness_control",
                "source": "world_bank_wdi:NE.TRD.GNFS.ZS",
                "transformation": "level",
                "notes": "Goods-and-services openness control; omitted when external openness is the treatment.",
            }
        )
    if mechanism_id not in {"fiscal_balance", "public_debt", "government_consumption"}:
        controls.append(
            {
                "name": "government_consumption_control",
                "source": "world_bank_wdi:NE.CON.GOVT.ZS",
                "transformation": "level",
                "notes": "Fiscal-demand control; omitted for fiscal stance and fiscal-size treatments.",
            }
        )
    return controls


def build_spec(mechanism_id: str, outcome_id: str, covers: list[dict]) -> dict:
    mechanism = MECHANISMS[mechanism_id]
    outcome = OUTCOMES[outcome_id]
    hid = f"market_order_{mechanism_id}_{outcome_id}_panel"
    expected = mechanism["expected_sign"]
    direction = "positively" if expected == "+" else "negatively"
    claim = (
        f"Across a pre-registered narrower OECD/market-peer panel from 1996 to 2021, "
        f"{mechanism['claim_prefix']} predict {outcome_text(outcome, expected)} after country and year fixed "
        f"effects and basic macro controls. This tests the {mechanism['theory']} as a second-wave "
        f"market-order hypothesis rather than reusing the Heritage latest-year cross-section."
    )
    return {
        "hypothesis_id": hid,
        "version": 1,
        "status": "pre_registered",
        "topic": mechanism["topic"],
        "claim": claim,
        "methodology_note": (
            "Second-wave market-order pre-registration. This spec narrows the country sample to OECD and "
            "market-peer economies to improve panel completeness while preserving a pre-run fixed sample, "
            "variables, direction, and reciprocal position links."
        ),
        "evidence_type": "associational",
        "sample": {
            "countries": COUNTRIES,
            "period": [1996, 2021],
            "temporal_structure": "panel",
            "exclusion_rules": [
                "drop country-years missing the outcome, treatment, or retained controls",
                "do not impute treatment values across countries",
                "treat this as associational evidence unless a later event-study or DiD design is registered",
            ],
        },
        "scope": {
            "period": [1996, 2021],
            "countries": ["OECD"],
            "outcome_dim": outcome["dim"],
            "policy_family": mechanism["policy_family"],
            "treatment_tags": mechanism["treatment_tags"],
        },
        "variables": {
            "outcome": [
                {
                    "name": outcome_id,
                    "source": outcome["source"],
                    "transformation": "level",
                    "notes": outcome["label"],
                }
            ],
            "treatment": [
                {
                    "name": mechanism["treatment_name"],
                    "source": mechanism["source"],
                    "transformation": "level",
                    "notes": mechanism["treatment_label"],
                }
            ],
            "controls": build_controls(mechanism_id),
        },
        "intervention_channel": (
            "institutional" if mechanism["topic"] == "institutional_quality"
            else ("regulatory" if mechanism["topic"] == "trade" else "fiscal")
        ),
        "intervention_channel_justification": (
            f"The treatment operationalizes {mechanism['treatment_label']} as a time-varying policy or "
            "institutional channel, not an ex-post outcome screen."
        ),
        "estimator": {
            "template": "panel_fe",
            "fixed_effects": ["country", "year"],
            "clustering": "country",
            "notes": (
                "Primary test is two-way fixed effects with country-clustered standard errors. This is a "
                "registered associational hurdle; causal promotion requires a sharper subsequent design."
            ),
        },
        "falsification": {
            "rule": (
                f"SUPPORTED if the coefficient on {mechanism['treatment_name']} is {direction} signed at "
                "p<0.10 with at least 30 usable observations after listwise deletion. REFUTED if the "
                "coefficient is significantly opposite-signed at p<0.10. Otherwise PARTIAL."
            ),
            "test": f"panel_fe_{hid}",
            "threshold": {
                "expected_sign": expected,
                "p_max": 0.10,
                "min_observations": 30,
            },
        },
        "prior_confidence": mechanism["prior"],
        "disclosure": (
            "The author is actively stress-testing free-market, Austrian, and ordoliberal claims. Favorable "
            "selection risk is handled by recording the claim, sample, variables, direction, and position "
            "links before estimation; null or contrary results count."
        ),
        "steelman": f"hypotheses/steelman/{hid}.md",
        "covers_claims": covers,
        "notes": "Second-wave market-order panel test. Do not edit v1 after first run.",
    }


def build_position_claim(position_id: str, mechanism_id: str, outcome_id: str) -> dict:
    mechanism = MECHANISMS[mechanism_id]
    outcome = OUTCOMES[outcome_id]
    expected = mechanism["expected_sign"]
    hid = f"market_order_{mechanism_id}_{outcome_id}_panel"
    school = POSITION_SCHOOLS[position_id]
    return {
        "claim": (
            f"{school} theory predicts that, in a 1996-2021 OECD/market-peer panel, "
            f"{mechanism['claim_prefix']} should be associated with "
            f"{outcome_text(outcome, expected)} through {mechanism['theory']}."
        ),
        "linked_hypothesis_id": hid,
        "school_prediction": "supported",
        "claim_polarity": "aligned",
        "empirical_status": "untested",
        "scope": {
            "period": [1996, 2021],
            "countries": ["OECD"],
            "outcome_dim": outcome["dim"],
            "policy_family": mechanism["policy_family"],
            "treatment_tags": mechanism["treatment_tags"],
        },
        "notes": (
            "Market-order follow-up prereg wave 2026-05-03: position linkage declared before estimation; "
            "update empirical_status only after run artifacts exist."
        ),
    }


def build_steelman(mechanism_id: str, outcome_id: str) -> str:
    mechanism = MECHANISMS[mechanism_id]
    outcome = OUTCOMES[outcome_id]
    return f"""# Steelman - market_order_{mechanism_id}_{outcome_id}_panel

The strongest objection is that {mechanism['treatment_label']} may proxy for income level, administrative
capacity, political history, commodity exposure, or global-cycle timing rather than the {mechanism['theory']}
itself. Country and year fixed effects reduce some bias, but they do not prove causality.

A second objection is reverse causality: countries with {outcome['positive_phrase']} may find it easier to
sustain reforms, fiscal discipline, or openness. A supported result should therefore be interpreted as a
scoreboard-eligible associational hurdle, not as final causal proof.

A third objection is measurement. The treatment proxy is broad and may miss the exact Austrian, ordoliberal,
Chicago monetarist, or classical-liberal mechanism being claimed. Null or contrary results should count
against this broad registered proxy, while sharper reform episodes can be registered later.

The result should be upgraded only through a later design with sharper event timing, lag structure,
event-study/DID identification, synthetic controls, or external instruments registered before estimation.
"""


def main() -> int:
    AUDITS.mkdir(parents=True, exist_ok=True)
    STEELMAN.mkdir(parents=True, exist_ok=True)

    position_claims: dict[str, list[dict]] = defaultdict(list)
    specs_meta: list[dict] = []
    for mechanism_id, outcomes in DESIGN.items():
        for outcome_id in outcomes:
            for position_id in MECHANISMS[mechanism_id]["positions"]:
                position_claims[position_id].append(
                    build_position_claim(position_id, mechanism_id, outcome_id)
                )

    claim_indexes: dict[str, dict[str, int]] = defaultdict(dict)
    for position_id, claims in position_claims.items():
        indexes = insert_claims(position_id, claims)
        for claim, index in zip(claims, indexes):
            claim_indexes[claim["linked_hypothesis_id"]][position_id] = index

    for mechanism_id, outcomes in DESIGN.items():
        for outcome_id in outcomes:
            mechanism = MECHANISMS[mechanism_id]
            hid = f"market_order_{mechanism_id}_{outcome_id}_panel"
            covers = [
                {
                    "position_id": position_id,
                    "claim_index": claim_indexes[hid][position_id],
                    "polarity": "aligned",
                    "school_prediction": "supported",
                    "confidence": "medium",
                    "notes": (
                        "Pre-run coverage declaration for the 2026-05-03 market-order follow-up wave; "
                        "position claim and hypothesis claim were linked before estimation."
                    ),
                }
                for position_id in mechanism["positions"]
            ]
            spec = build_spec(mechanism_id, outcome_id, covers)
            topic_dir = HYPOTHESES / mechanism["topic"]
            topic_dir.mkdir(parents=True, exist_ok=True)
            (topic_dir / f"{hid}.yaml").write_text(dump_yaml(spec))
            (STEELMAN / f"{hid}.md").write_text(build_steelman(mechanism_id, outcome_id))
            specs_meta.append(
                {
                    "hypothesis_id": hid,
                    "topic": mechanism["topic"],
                    "mechanism": mechanism_id,
                    "outcome": outcome_id,
                    "positions": mechanism["positions"],
                    "expected_sign": mechanism["expected_sign"],
                }
            )

    ids = [item["hypothesis_id"] for item in specs_meta]
    (AUDITS / f"{WAVE}.ids").write_text("\n".join(ids) + "\n")
    audit = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "methodology_gate": "pre_registered_specs_and_position_links_created_before_estimation",
        "count": len(specs_meta),
        "sample_country_count": len(COUNTRIES),
        "period": [1996, 2021],
        "specs": specs_meta,
    }
    (AUDITS / f"{WAVE}.json").write_text(json.dumps(audit, indent=2))
    lines = [
        "# Market-Order Follow-Up Pre-Registration Wave - 2026-05-03",
        "",
        "## Methodology Gate",
        "",
        "- These are new second-wave panel tests, not result-driven scoreboard mappings.",
        "- Hypothesis specs, position claims, and covers_claims are written before estimation.",
        "- The sample is deliberately narrower than the first wave: 33 OECD/market-peer economies, 1996-2021.",
        "- First git commit of these files is the pre-registration timestamp.",
        "- Run artifacts must be created only after that commit.",
        "",
        f"## Count: {len(specs_meta)}",
        "",
    ]
    by_mechanism: dict[str, int] = defaultdict(int)
    for item in specs_meta:
        by_mechanism[item["mechanism"]] += 1
    for mechanism_id in sorted(by_mechanism):
        lines.append(f"- {mechanism_id}: {by_mechanism[mechanism_id]}")
    lines.extend(["", "## Hypotheses", ""])
    for item in specs_meta:
        lines.append(
            f"- `{item['hypothesis_id']}` | mechanism={item['mechanism']} | outcome={item['outcome']} | "
            f"positions={','.join(item['positions'])}"
        )
    (AUDITS / f"{WAVE}.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"generated": len(specs_meta), "ids": ids}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
