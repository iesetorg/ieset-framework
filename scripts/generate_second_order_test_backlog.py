#!/usr/bin/env python3
"""Generate a prioritized backlog for second-order test upgrades.

The scoreboard is now strict-gated: most public claim links no longer move the
high-integrity score until the linked hypotheses measure or document their
second-order mechanism layers. This script turns those holds into a work queue:
which hypothesis should be upgraded, which layers are missing, which designs are
most appropriate, and which source families/fetchers would unblock it.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import yaml

import audit_scoreboard_outcomes as scoreboard
import audit_second_order_measurement as second_order


ROOT = Path(__file__).resolve().parents[1]
GATES_JSON = ROOT / "engine" / "scoreboard_second_order_gates.json"
OUT_JSON = ROOT / "engine" / "second_order_test_backlog.json"
OUT_MD = ROOT / "engine" / "second_order_test_backlog.md"

CONTROL_DESIGN_LAYERS = {
    "first_order_price_or_transfer",
    "second_order_supply_response",
    "leakage_or_substitution",
    "quality_margin",
    "net_welfare",
    "distributional_incidence",
    "allocation_distortion",
}

POLICY_FAMILY_LAYERS = {
    "competition_policy": [
        "market_structure_response",
        "allocation_distortion",
        "quality_margin",
        "distributional_incidence",
        "net_welfare",
    ],
    "energy_policy": [
        "second_order_supply_response",
        "quality_margin",
        "fiscal_or_enforcement_cost",
        "distributional_incidence",
        "net_welfare",
    ],
    "environmental_policy": [
        "externality_or_spillover",
        "leakage_or_substitution",
        "distributional_incidence",
        "net_welfare",
        "macro_feedback",
    ],
    "fiscal_policy": [
        "distributional_incidence",
        "behavioral_response",
        "fiscal_or_enforcement_cost",
        "macro_feedback",
        "net_welfare",
    ],
    "healthcare_policy": [
        "first_order_policy_effect",
        "quality_margin",
        "distributional_incidence",
        "fiscal_or_enforcement_cost",
        "net_welfare",
    ],
    "housing_policy": [
        "second_order_supply_response",
        "quality_margin",
        "allocation_distortion",
        "distributional_incidence",
        "net_welfare",
    ],
    "industrial_policy": [
        "market_structure_response",
        "dynamic_investment_response",
        "allocation_distortion",
        "fiscal_or_enforcement_cost",
        "net_welfare",
    ],
    "institutional_reform": [
        "implementation_capacity",
        "externality_or_spillover",
        "macro_feedback",
        "distributional_incidence",
    ],
    "labour_market": [
        "behavioral_response",
        "distributional_incidence",
        "market_structure_response",
        "fiscal_or_enforcement_cost",
        "net_welfare",
    ],
    "monetary_policy": [
        "macro_feedback",
        "behavioral_response",
        "distributional_incidence",
        "dynamic_investment_response",
        "net_welfare",
    ],
    "regulation": [
        "market_structure_response",
        "implementation_capacity",
        "quality_margin",
        "allocation_distortion",
        "distributional_incidence",
        "net_welfare",
    ],
    "tax_policy": [
        "distributional_incidence",
        "behavioral_response",
        "dynamic_investment_response",
        "fiscal_or_enforcement_cost",
        "net_welfare",
    ],
    "trade_policy": [
        "leakage_or_substitution",
        "market_structure_response",
        "distributional_incidence",
        "externality_or_spillover",
        "net_welfare",
    ],
    "welfare_architecture": [
        "distributional_incidence",
        "behavioral_response",
        "fiscal_or_enforcement_cost",
        "net_welfare",
    ],
}

POLICY_FAMILY_DOMAINS = {
    "competition_policy": {"competition_policy"},
    "energy_policy": {"energy_policy"},
    "environmental_policy": {"environmental_policy"},
    "fiscal_policy": {"fiscal_transfer", "public_spending", "tax_policy"},
    "healthcare_policy": {"healthcare_policy"},
    "housing_policy": {"housing_supply_policy", "land_use_regulation", "rent_control"},
    "industrial_policy": {"industrial_policy"},
    "institutional_reform": {"institutional_reform"},
    "labour_market": {"labour_market"},
    "monetary_policy": {"monetary_policy"},
    "regulation": {"competition_policy", "financial_regulation", "labour_market"},
    "tax_policy": {"tax_policy"},
    "trade_policy": {"trade_policy"},
    "welfare_architecture": {"fiscal_transfer", "welfare_policy"},
}

LAYER_DESIGNS = {
    "allocation_distortion": ["mechanism_channel_decomposition", "treated_vs_untreated_units"],
    "behavioral_response": ["high_frequency_event_study", "eligible_vs_ineligible_groups"],
    "distributional_incidence": ["distributional_decomposition", "eligible_vs_ineligible_groups"],
    "dynamic_investment_response": ["dynamic_investment_followup", "high_frequency_event_study"],
    "externality_or_spillover": ["spillover_tracking", "adjacent_market_comparison"],
    "first_order_policy_effect": ["treated_vs_untreated_units", "high_frequency_event_study"],
    "first_order_price_or_transfer": ["controlled_vs_uncontrolled_categories", "high_frequency_event_study"],
    "fiscal_or_enforcement_cost": ["welfare_accounting", "mechanism_channel_decomposition"],
    "implementation_capacity": ["phase_in_or_threshold_comparison", "mechanism_channel_decomposition"],
    "leakage_or_substitution": ["adjacent_market_comparison", "controlled_vs_uncontrolled_categories"],
    "macro_feedback": ["high_frequency_event_study", "mechanism_channel_decomposition"],
    "market_structure_response": ["treated_vs_untreated_units", "dynamic_investment_followup"],
    "net_welfare": ["welfare_accounting", "distributional_decomposition"],
    "quality_margin": ["controlled_vs_uncontrolled_categories", "high_frequency_event_study"],
    "second_order_supply_response": ["triple_difference", "treated_vs_untreated_units", "dynamic_investment_followup"],
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text()) or {}


def text_blob(doc: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in (
        "hypothesis_id",
        "claim",
        "title",
        "description",
        "methodology_note",
        "notes",
        "intervention_channel",
    ):
        value = doc.get(key)
        if value:
            parts.append(str(value))
    scope = doc.get("scope") or {}
    for key in ("policy_family", "treatment_tags", "outcome_dim", "countries"):
        parts.extend(str(x) for x in scope.get(key) or [])
    return " ".join(parts).lower()


def policy_families(doc: dict[str, Any]) -> list[str]:
    scope = doc.get("scope") or {}
    return [str(x) for x in scope.get("policy_family") or []]


def policy_domains_for_hypothesis(doc: dict[str, Any]) -> set[str]:
    domains: set[str] = set()
    text = text_blob(doc)
    mechanism_type = str((doc.get("mechanism_measurement") or {}).get("mechanism_type") or "").lower()
    declared_price_or_rent_control = False
    if "rent_control" in mechanism_type:
        domains.update({"rent_control", "housing_supply_policy", "land_use_regulation"})
        declared_price_or_rent_control = True
    elif "price_control" in mechanism_type:
        domains.update({"price_control", "administered_price_subsidy", "competition_policy"})
        declared_price_or_rent_control = True
    if not declared_price_or_rent_control:
        for family in policy_families(doc):
            domains.update(POLICY_FAMILY_DOMAINS.get(family, set()))
    if "rent control" in text or "rent cap" in text or "mietpreisbremse" in text:
        domains.update({"rent_control", "housing_supply_policy", "land_use_regulation"})
    if "price control" in text or "price cap" in text or "price ceiling" in text:
        domains.update({"price_control", "administered_price_subsidy", "competition_policy"})
    if "fuel" in text or "electricity" in text or "energy" in text:
        domains.add("energy_policy")
    if "tariff" in text or "customs" in text or "trade" in text:
        domains.add("trade_policy")
    if "minimum wage" in text or "employment" in text or "unemployment" in text:
        domains.add("labour_market")
    return domains


def explicit_missing_layers(doc: dict[str, Any], gate_rows: list[dict[str, Any]]) -> list[str]:
    layers: set[str] = set()
    for row in gate_rows:
        layers.update(row.get("required_data_gaps") or [])
    mechanism = doc.get("mechanism_measurement") or {}
    for layer in mechanism.get("causal_layers") or []:
        if layer.get("required_for_dispositive_verdict") and layer.get("measurement_status") == "data_gap":
            layers.add(str(layer.get("layer")))
    return sorted(layer for layer in layers if layer)


def inferred_layers_for_hypothesis(doc: dict[str, Any]) -> list[str]:
    """Infer a minimum second-order layer set for missing-contract holds."""
    text = text_blob(doc)
    layers: set[str] = set()

    if any(term in text for term in second_order.CONTROL_TERMS):
        layers.update(CONTROL_DESIGN_LAYERS)

    for family in policy_families(doc):
        layers.update(POLICY_FAMILY_LAYERS.get(family, []))

    channel = str(doc.get("intervention_channel") or "").lower()
    if channel == "fiscal":
        layers.update(POLICY_FAMILY_LAYERS["fiscal_policy"])
    elif channel == "regulatory":
        layers.update(POLICY_FAMILY_LAYERS["regulation"])
    elif channel == "bundled":
        layers.update(POLICY_FAMILY_LAYERS["fiscal_policy"])
        layers.update(POLICY_FAMILY_LAYERS["regulation"])

    variables = doc.get("variables") or {}
    if variables.get("treatment") or variables.get("instruments"):
        layers.update(["first_order_policy_effect", "behavioral_response", "distributional_incidence"])
    if variables.get("decomposition_channels"):
        layers.update(["mechanism_channel_decomposition", "net_welfare"])
        layers.discard("mechanism_channel_decomposition")

    if not layers:
        layers.update(["first_order_policy_effect", "distributional_incidence", "net_welfare"])

    return sorted(layers)


def missing_layers_for_hypothesis(
    doc: dict[str, Any],
    gate_rows: list[dict[str, Any]],
) -> tuple[list[str], str]:
    explicit = explicit_missing_layers(doc, gate_rows)
    if explicit:
        return explicit, "declared_contract_or_gate"
    return inferred_layers_for_hypothesis(doc), "inferred_missing_contract"


def recommended_designs_for_layers(layers: list[str]) -> list[str]:
    designs: list[str] = []
    seen: set[str] = set()
    for layer in layers:
        for design in LAYER_DESIGNS.get(layer, []):
            if design not in seen:
                designs.append(design)
                seen.add(design)
    return designs


def source_family_details(
    layers: list[str],
    families: dict[str, dict[str, Any]],
    policy_domains: set[str] | None = None,
) -> list[dict[str, Any]]:
    family_ids = second_order.source_family_ids_for_layers(layers, families)
    rows: list[dict[str, Any]] = []
    domain_filter = policy_domains or set()
    for family_id in family_ids:
        rec = families[family_id]
        family_domains = set(rec.get("policy_domains") or [])
        if domain_filter and family_domains and not family_domains.intersection(domain_filter):
            continue
        rows.append(
            {
                "family_id": family_id,
                "name": rec.get("name"),
                "readiness": rec.get("readiness"),
                "priority": rec.get("priority"),
                "existing_fetchers": rec.get("existing_fetchers") or [],
                "publisher_refs": rec.get("publisher_refs") or [],
            }
        )
    return rows


def backlog_priority(
    rows: list[dict[str, Any]],
    layers: list[str],
    source_families: list[dict[str, Any]],
) -> float:
    public_rows = [row for row in rows if row.get("verdict_public")]
    claim_weight = sum(abs(float(row.get("raw_weighted_score") or 0)) for row in public_rows)
    failure_rows = sum(1 for row in public_rows if row.get("failure_credit_kind") != "not_failure_prediction_win")
    declared_hold_rows = sum(1 for row in public_rows if row.get("declared_gate_status") == "declared_measurement_hold")
    ready_family_bonus = sum(1 for row in source_families if row.get("readiness") in {"ready", "partial_ready"})
    proprietary_penalty = sum(1 for row in source_families if row.get("readiness") == "proprietary_gap")
    layer_penalty = max(0, len(layers) - 5) * 0.15
    return round(
        len(public_rows)
        + claim_weight
        + failure_rows * 0.75
        + declared_hold_rows * 1.25
        + ready_family_bonus * 0.1
        - proprietary_penalty * 0.2
        - layer_penalty,
        3,
    )


def build_backlog() -> dict[str, Any]:
    gate_payload = load_json(GATES_JSON)
    hypotheses, _coverage = scoreboard.build_hypothesis_index()
    families = second_order.load_second_order_source_families()

    held_by_hypothesis: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in gate_payload.get("claim_links") or []:
        if not row.get("verdict_public"):
            continue
        if row.get("strict_scoreboard_eligible"):
            continue
        hypothesis_id = row.get("hypothesis_id")
        if hypothesis_id:
            held_by_hypothesis[hypothesis_id].append(row)

    rows: list[dict[str, Any]] = []
    for hypothesis_id, gate_rows in held_by_hypothesis.items():
        doc = hypotheses.get(hypothesis_id) or {"hypothesis_id": hypothesis_id}
        layers, layer_source = missing_layers_for_hypothesis(doc, gate_rows)
        source_families = source_family_details(layers, families, policy_domains_for_hypothesis(doc))
        readiness_counts = Counter(row.get("readiness", "unknown") for row in source_families)
        rows.append(
            {
                "hypothesis_id": hypothesis_id,
                "topic": doc.get("topic"),
                "status": doc.get("status"),
                "evidence_type": doc.get("evidence_type"),
                "public_claim_links_held": len(gate_rows),
                "positions_held": sorted({row.get("position_id") for row in gate_rows if row.get("position_id")}),
                "gate_status_counts": dict(Counter(row.get("strict_gate_status") for row in gate_rows)),
                "failure_credit_holds": sum(
                    1 for row in gate_rows
                    if row.get("failure_credit_kind") != "not_failure_prediction_win"
                ),
                "raw_weighted_score_at_hold": round(
                    sum(float(row.get("raw_weighted_score") or 0) for row in gate_rows),
                    3,
                ),
                "missing_layers": layers,
                "missing_layer_source": layer_source,
                "recommended_designs": recommended_designs_for_layers(layers),
                "source_readiness_counts": dict(readiness_counts),
                "source_families": source_families,
                "claim_examples": [
                    {
                        "position_id": row.get("position_id"),
                        "claim_index": row.get("claim_index"),
                        "raw_school_outcome": row.get("raw_school_outcome"),
                        "claim": row.get("claim"),
                    }
                    for row in gate_rows[:5]
                ],
            }
        )

    for row in rows:
        row["priority"] = backlog_priority(
            held_by_hypothesis[row["hypothesis_id"]],
            row["missing_layers"],
            row["source_families"],
        )

    rows.sort(
        key=lambda row: (
            -row["priority"],
            row["missing_layer_source"] != "declared_contract_or_gate",
            -row["public_claim_links_held"],
            row["hypothesis_id"],
        )
    )

    layer_counts = Counter()
    readiness_counts = Counter()
    design_counts = Counter()
    for row in rows:
        layer_counts.update(row["missing_layers"])
        readiness_counts.update(row["source_readiness_counts"])
        design_counts.update(row["recommended_designs"])

    return {
        "generated_by": "scripts/generate_second_order_test_backlog.py",
        "generated_at": date.today().isoformat(),
        "scoreboard_gate_artifact": str(GATES_JSON.relative_to(ROOT)),
        "summary": {
            "held_hypotheses": len(rows),
            "held_public_claim_links": sum(row["public_claim_links_held"] for row in rows),
            "failure_credit_holds": sum(row["failure_credit_holds"] for row in rows),
            "missing_layer_counts": dict(layer_counts),
            "source_readiness_counts": dict(readiness_counts),
            "recommended_design_counts": dict(design_counts),
        },
        "backlog": rows,
    }


def write_outputs(payload: dict[str, Any]) -> None:
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    summary = payload["summary"]
    lines = [
        "# Second-order Test Backlog",
        "",
        "This generated backlog prioritizes held public claim links that need second-order measurement before they can move the high-integrity scoreboard.",
        "",
        "## Summary",
        "",
        f"- Held hypotheses: {summary['held_hypotheses']}",
        f"- Held public claim links: {summary['held_public_claim_links']}",
        f"- Failure-forecast holds: {summary['failure_credit_holds']}",
        f"- Missing layers: `{json.dumps(summary['missing_layer_counts'], sort_keys=True)}`",
        f"- Source readiness: `{json.dumps(summary['source_readiness_counts'], sort_keys=True)}`",
        f"- Recommended designs: `{json.dumps(summary['recommended_design_counts'], sort_keys=True)}`",
        "",
        "## Top Upgrade Queue",
        "",
        "| priority | hypothesis | held links | layer source | missing layers | designs | source readiness |",
        "| ---: | --- | ---: | --- | --- | --- | --- |",
    ]
    for row in payload["backlog"][:100]:
        layers = ", ".join(row["missing_layers"][:6])
        if len(row["missing_layers"]) > 6:
            layers += ", ..."
        designs = ", ".join(row["recommended_designs"][:5])
        if len(row["recommended_designs"]) > 5:
            designs += ", ..."
        readiness = json.dumps(row["source_readiness_counts"], sort_keys=True)
        lines.append(
            f"| {row['priority']:.2f} | `{row['hypothesis_id']}` | "
            f"{row['public_claim_links_held']} | {row['missing_layer_source']} | "
            f"{layers} | {designs} | `{readiness}` |"
        )

    lines.extend(["", "## Top Source-Family Gaps", ""])
    family_counts = Counter()
    for row in payload["backlog"]:
        for family in row["source_families"]:
            family_counts[family["family_id"]] += row["public_claim_links_held"]
    for family_id, count in family_counts.most_common(25):
        lines.append(f"- `{family_id}` ({count} held-link mentions)")

    OUT_MD.write_text("\n".join(lines) + "\n")


def main() -> int:
    payload = build_backlog()
    write_outputs(payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
