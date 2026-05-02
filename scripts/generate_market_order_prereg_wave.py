#!/usr/bin/env python3
"""Generate a methodology-safe market-order pre-registration wave.

This script converts the Heritage candidate-screen signal into fresh,
theory-shaped panel hypotheses. It writes the hypothesis specs, steelman files,
position-side claims, and hypothesis-side covers_claims before any estimation
run is created. The first git commit containing these files is therefore the
pre-registration timestamp under METHODOLOGY.md.
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

COUNTRIES = [
    "ARG", "AUS", "AUT", "BEL", "BRA", "CAN", "CHE", "CHL", "CHN", "COL",
    "CRI", "CZE", "DEU", "DNK", "EGY", "ESP", "EST", "FIN", "FRA", "GBR",
    "GHA", "GRC", "HUN", "IDN", "IND", "IRL", "ISR", "ITA", "JPN", "KEN",
    "KOR", "LTU", "LVA", "MAR", "MEX", "MYS", "NGA", "NLD", "NOR", "NZL",
    "PER", "PHL", "POL", "PRT", "SGP", "SVK", "SVN", "SWE", "THA", "TUR",
    "URY", "USA", "ZAF",
]

OUTCOMES = {
    "investment_share": {
        "label": "gross capital formation as a share of GDP",
        "source": "world_bank_wdi:NE.GDI.TOTL.ZS",
        "dim": ["gdp_growth", "capital_flows"],
        "positive_phrase": "higher private and total investment shares",
        "negative_phrase": "lower investment shares",
    },
    "private_credit_depth": {
        "label": "domestic credit to the private sector as a share of GDP",
        "source": "world_bank_wdi:FS.AST.PRVT.GD.ZS",
        "dim": ["financialisation", "capital_flows"],
        "positive_phrase": "deeper private credit intermediation",
        "negative_phrase": "shallower private credit intermediation",
    },
    "gdp_pc_growth": {
        "label": "annual real GDP per capita growth",
        "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG",
        "dim": ["gdp_growth", "productivity"],
        "positive_phrase": "faster real GDP per capita growth",
        "negative_phrase": "slower real GDP per capita growth",
    },
    "high_tech_exports": {
        "label": "high-technology exports as a share of manufactured exports",
        "source": "world_bank_wdi:TX.VAL.TECH.MF.ZS",
        "dim": ["industrial_capability", "trade_liberalisation"],
        "positive_phrase": "higher high-technology export intensity",
        "negative_phrase": "lower high-technology export intensity",
    },
    "employment_rate": {
        "label": "employment-to-population ratio",
        "source": "world_bank_wdi:SL.EMP.TOTL.SP.ZS",
        "dim": ["employment_labour"],
        "positive_phrase": "higher employment rates",
        "negative_phrase": "lower employment rates",
    },
}

MECHANISMS = {
    "rule_of_law": {
        "topic": "institutional_quality",
        "treatment_name": "rule_of_law_wgi",
        "treatment_label": "WGI rule of law",
        "source": "wgi:RL.EST",
        "expected_sign": "+",
        "policy_family": ["institutional_reform", "regulation"],
        "treatment_tags": ["rule_of_law", "property_rights", "contract_enforcement"],
        "positions": ["classical_liberal", "ordoliberal", "austrian", "institutionalism", "empirical_pragmatist"],
        "claim_prefix": "stronger rule-of-law institutions",
        "theory": "property-rights, contract-enforcement, and economic-calculation channels",
        "prior": 0.62,
    },
    "regulatory_quality": {
        "topic": "regulatory",
        "treatment_name": "regulatory_quality_wgi",
        "treatment_label": "WGI regulatory quality",
        "source": "wgi:GOV_WGI_RQ.EST",
        "expected_sign": "+",
        "policy_family": ["regulation", "competition_policy"],
        "treatment_tags": ["regulatory_quality", "business_freedom", "market_entry"],
        "positions": ["classical_liberal", "ordoliberal", "austrian", "empirical_pragmatist"],
        "claim_prefix": "more predictable and market-compatible regulation",
        "theory": "entry, competition, and entrepreneurship channels",
        "prior": 0.58,
    },
    "control_corruption": {
        "topic": "institutional_quality",
        "treatment_name": "control_corruption_wgi",
        "treatment_label": "WGI control of corruption",
        "source": "wgi:CC.EST",
        "expected_sign": "+",
        "policy_family": ["institutional_reform", "regulation"],
        "treatment_tags": ["control_of_corruption", "rent_seeking", "rule_bound_governance"],
        "positions": ["ordoliberal", "institutionalism", "classical_liberal", "empirical_pragmatist"],
        "claim_prefix": "stronger control of corruption",
        "theory": "rent-seeking and rule-bound-competition channels",
        "prior": 0.64,
    },
    "economic_freedom": {
        "topic": "institutional_quality",
        "treatment_name": "fraser_economic_freedom",
        "treatment_label": "Fraser EFW summary score",
        "source": "fraser_efw:efw_panel",
        "expected_sign": "+",
        "policy_family": ["institutional_reform", "regulation", "trade_policy"],
        "treatment_tags": ["economic_freedom", "market_order", "fraser_efw"],
        "positions": ["classical_liberal", "austrian", "ordoliberal", "empirical_pragmatist"],
        "claim_prefix": "higher broad economic-freedom scores",
        "theory": "market-order, decentralized-allocation, and policy-predictability channels",
        "prior": 0.56,
    },
    "sound_money": {
        "topic": "monetary",
        "treatment_name": "inflation_rate",
        "treatment_label": "annual CPI inflation",
        "source": "world_bank_wdi:FP.CPI.TOTL.ZG",
        "expected_sign": "-",
        "policy_family": ["monetary_policy"],
        "treatment_tags": ["sound_money", "inflation_discipline", "monetary_stability"],
        "positions": ["austrian", "chicago_monetarism", "ordoliberal", "classical_liberal"],
        "claim_prefix": "higher inflation",
        "theory": "sound-money, calculation, and real-contracting channels",
        "prior": 0.61,
    },
    "government_spending": {
        "topic": "fiscal",
        "treatment_name": "government_spending_share",
        "treatment_label": "government expenditure as a share of GDP",
        "source": "world_bank_wdi:GC.XPN.TOTL.GD.ZS",
        "expected_sign": "-",
        "policy_family": ["fiscal_policy"],
        "treatment_tags": ["government_spending", "fiscal_size", "crowding_out"],
        "positions": ["classical_liberal", "austrian", "ordoliberal"],
        "claim_prefix": "larger government expenditure shares",
        "theory": "crowding-out, tax-expectation, and discretionary-allocation channels",
        "prior": 0.52,
    },
    "tax_burden": {
        "topic": "fiscal",
        "treatment_name": "tax_revenue_share",
        "treatment_label": "tax revenue as a share of GDP",
        "source": "world_bank_wdi:GC.TAX.TOTL.GD.ZS",
        "expected_sign": "-",
        "policy_family": ["fiscal_policy", "tax_policy"],
        "treatment_tags": ["tax_burden", "marginal_tax_wedge", "private_incentives"],
        "positions": ["classical_liberal", "austrian", "ordoliberal"],
        "claim_prefix": "larger tax-revenue shares",
        "theory": "private-incentive, retained-earnings, and deadweight-loss channels",
        "prior": 0.50,
    },
    "trade_openness": {
        "topic": "trade",
        "treatment_name": "trade_openness",
        "treatment_label": "trade openness",
        "source": "world_bank_wdi:NE.TRD.GNFS.ZS",
        "expected_sign": "+",
        "policy_family": ["trade_policy", "competition_policy"],
        "treatment_tags": ["trade_openness", "market_access", "competition"],
        "positions": ["classical_liberal", "ordoliberal", "empirical_pragmatist"],
        "claim_prefix": "higher trade openness",
        "theory": "competition, specialization, and market-size channels",
        "prior": 0.57,
    },
}

DESIGN = {
    "rule_of_law": ["investment_share", "private_credit_depth", "gdp_pc_growth", "high_tech_exports"],
    "regulatory_quality": ["investment_share", "employment_rate", "high_tech_exports", "gdp_pc_growth"],
    "control_corruption": ["investment_share", "private_credit_depth", "gdp_pc_growth", "high_tech_exports"],
    "economic_freedom": ["investment_share", "gdp_pc_growth", "employment_rate", "high_tech_exports"],
    "sound_money": ["investment_share", "gdp_pc_growth", "private_credit_depth", "employment_rate"],
    "government_spending": ["investment_share", "gdp_pc_growth", "private_credit_depth", "employment_rate"],
    "tax_burden": ["investment_share", "gdp_pc_growth", "private_credit_depth", "employment_rate"],
    "trade_openness": ["investment_share", "gdp_pc_growth", "high_tech_exports", "employment_rate"],
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


def build_spec(mechanism_id: str, outcome_id: str, covers: list[dict]) -> dict:
    mechanism = MECHANISMS[mechanism_id]
    outcome = OUTCOMES[outcome_id]
    hid = f"market_order_{mechanism_id}_{outcome_id}_panel"
    expected = mechanism["expected_sign"]
    direction = "positively" if expected == "+" else "negatively"
    claim = (
        f"Across a pre-registered panel of OECD and major emerging-market economies from 1996 to 2023, "
        f"{mechanism['claim_prefix']} predict {outcome_text(outcome, expected)} after country and year fixed "
        f"effects and basic macro controls. This tests the {mechanism['theory']} without using the Heritage "
        f"latest-year cross-section as the treatment."
    )
    controls = [
        {
            "name": "log_gdp_pc_ppp",
            "source": "world_bank_wdi:NY.GDP.PCAP.PP.KD",
            "transformation": "log",
            "notes": "Income-level control to reduce short-run development-level bias.",
        },
        {
            "name": "population_growth",
            "source": "world_bank_wdi:SP.POP.GROW",
            "transformation": "level",
            "notes": "Demographic pressure control.",
        },
    ]
    if mechanism_id != "trade_openness":
        controls.append(
            {
                "name": "trade_openness_control",
                "source": "world_bank_wdi:NE.TRD.GNFS.ZS",
                "transformation": "level",
                "notes": "Openness control except when openness is the treatment.",
            }
        )
    if mechanism_id not in {"government_spending", "tax_burden"}:
        controls.append(
            {
                "name": "government_consumption_share",
                "source": "world_bank_wdi:NE.CON.GOVT.ZS",
                "transformation": "level",
                "notes": "Fiscal-demand control; omitted when fiscal size is the treatment.",
            }
        )
    return {
        "hypothesis_id": hid,
        "version": 1,
        "status": "pre_registered",
        "topic": mechanism["topic"],
        "claim": claim,
        "methodology_note": (
            "Second-stage market-order pre-registration generated from a prior candidate-screen queue. "
            "The Heritage screen is used only for triage; this spec is registered before estimation and uses "
            "time-varying WGI, Fraser EFW, or WDI panel measures rather than Heritage latest-year scores."
        ),
        "evidence_type": "associational",
        "sample": {
            "countries": COUNTRIES,
            "period": [1996, 2023],
            "temporal_structure": "panel",
            "exclusion_rules": [
                "drop country-years missing the outcome, treatment, or retained controls",
                "do not impute treatment values across countries",
                "treat this as associational evidence unless a later event-study or DiD design is registered",
            ],
        },
        "scope": {
            "period": [1996, 2023],
            "countries": ["OECD", "GLOBAL"],
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
            "controls": controls,
        },
        "intervention_channel": "institutional"
        if mechanism["topic"] in {"institutional_quality", "regulatory", "trade"}
        else ("monetary" if mechanism["topic"] == "monetary" else "fiscal"),
        "intervention_channel_justification": (
            f"The treatment operationalizes {mechanism['treatment_label']} as a time-varying policy or "
            "institutional channel, not a contemporaneous outcome cherry-pick."
        ),
        "estimator": {
            "template": "panel_fe",
            "fixed_effects": ["country", "year"],
            "clustering": "country",
            "notes": (
                "Primary test is two-way fixed effects with country-clustered standard errors. The first "
                "public verdict should not be treated as causal; it is the registered panel hurdle before "
                "any scoreboard interpretation."
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
            "The author is actively testing market-liberal and Austrian/ordoliberal claims, so favorable "
            "selection risk is real. This spec counters that risk by recording the claim, sample, variables, "
            "direction, and position links before the run; null or contrary results count."
        ),
        "steelman": f"hypotheses/steelman/{hid}.md",
        "covers_claims": covers,
        "notes": (
            "Do not promote from the earlier Heritage screen directly. This v1 panel spec is the registered "
            "second-stage test."
        ),
    }


def build_position_claim(position_id: str, mechanism_id: str, outcome_id: str) -> dict:
    mechanism = MECHANISMS[mechanism_id]
    outcome = OUTCOMES[outcome_id]
    expected = mechanism["expected_sign"]
    hid = f"market_order_{mechanism_id}_{outcome_id}_panel"
    school = POSITION_SCHOOLS[position_id]
    return {
        "claim": (
            f"{school} theory predicts that, in a 1996-2023 country panel, {mechanism['claim_prefix']} "
            f"should be associated with {outcome_text(outcome, expected)} through {mechanism['theory']}."
        ),
        "linked_hypothesis_id": hid,
        "school_prediction": "supported",
        "claim_polarity": "aligned",
        "empirical_status": "untested",
        "scope": {
            "period": [1996, 2023],
            "countries": ["OECD", "GLOBAL"],
            "outcome_dim": outcome["dim"],
            "policy_family": mechanism["policy_family"],
            "treatment_tags": mechanism["treatment_tags"],
        },
        "notes": (
            "Market-order prereg wave 2026-05-03: position linkage declared before estimation; "
            "update empirical_status only after run artifacts exist."
        ),
    }


def build_steelman(mechanism_id: str, outcome_id: str) -> str:
    mechanism = MECHANISMS[mechanism_id]
    outcome = OUTCOMES[outcome_id]
    return f"""# Steelman — market_order_{mechanism_id}_{outcome_id}_panel

The strongest objection is that {mechanism['treatment_label']} may proxy for income level, administrative
capacity, geography, colonial history, or global-cycle exposure rather than the {mechanism['theory']} itself.
The registered panel fixed-effects design reduces pure cross-sectional bias, but it does not prove causality.

A second objection is reverse causality: countries with {outcome['positive_phrase']} may find it easier to
improve institutions, sustain openness, or maintain stable macro policy. This is why a supported result should
be treated as a scoreboard-eligible associational hurdle, not as final causal proof.

A third objection is measurement: WGI, Fraser EFW, and WDI variables are broad institutional proxies. They may
miss the specific Austrian, ordoliberal, or classical-liberal mechanism that the school would emphasize. If the
coefficient is null or contrary, the fair interpretation is that this broad proxy did not clear the registered
panel test, not that every variant of the theory is impossible.

The result should be upgraded only by a later design that uses sharper reform episodes, lag structures,
event-study/DID identification, or external instruments registered before estimation.
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
                        "Pre-run coverage declaration for the 2026-05-03 market-order prereg wave; "
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
    (AUDITS / "market_order_prereg_wave_2026-05-03.ids").write_text("\n".join(ids) + "\n")
    audit = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "methodology_gate": "pre_registered_specs_and_position_links_created_before_estimation",
        "count": len(specs_meta),
        "specs": specs_meta,
    }
    (AUDITS / "market_order_prereg_wave_2026-05-03.json").write_text(json.dumps(audit, indent=2))
    lines = [
        "# Market-Order Pre-Registration Wave - 2026-05-03",
        "",
        "## Methodology Gate",
        "",
        "- These specs are new second-stage panel tests, not Heritage scoreboard mappings.",
        "- Hypothesis specs, position claims, and covers_claims are written before estimation.",
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
    (AUDITS / "market_order_prereg_wave_2026-05-03.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"generated": len(specs_meta), "ids": ids}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
