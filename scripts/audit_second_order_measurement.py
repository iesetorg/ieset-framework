#!/usr/bin/env python3
"""Audit second-order measurement coverage for policy-experiment artifacts.

The goal is not to grade outcomes. It is to identify whether specs and policy
records have enough structured design metadata to distinguish:

* first-order price/transfer effects,
* second-order supply/allocation/quality/leakage effects,
* distributional incidence, and
* net welfare accounting.

This lets broad proxy screens stay visible without being mistaken for
dispositive tests.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SECOND_ORDER_SOURCES_PATH = ROOT / "data" / "second_order_sources.yaml"
SECOND_ORDER_HOLD_GATES = {
    "screen_only_until_second_order_measured",
    "descriptive_only",
}
SECOND_ORDER_PUBLIC_WITH_GAPS_GATES = {
    "dispositive_with_documented_layer_gaps",
}

CONTROL_TERMS = (
    "price control",
    "price controls",
    "price cap",
    "price caps",
    "price ceiling",
    "price ceilings",
    "wage-price",
    "rent control",
    "rent controls",
    "rent cap",
    "rent caps",
    "mietpreisbremse",
    "mietendeckel",
    "precios cuidados",
    "precios justos",
)

POLICY_EXPERIMENT_TERMS = CONTROL_TERMS + (
    "tax",
    "subsidy",
    "transfer",
    "minimum wage",
    "tariff",
    "deregulation",
    "privatisation",
    "nationalisation",
    "industrial policy",
    "monetary",
    "central bank",
    "immigration",
    "healthcare",
    "welfare",
    "energy",
    "housing",
    "education",
)

CONTROL_AXES = {
    "regulatory.price_control_intensity",
    "regulatory.housing_rent_control",
}

_SOURCE_WORD_RE = re.compile(r"[^a-z0-9]+")


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open() as f:
        doc = yaml.safe_load(f)
    return doc or {}


def normalise_source_text(text: str) -> str:
    return _SOURCE_WORD_RE.sub(" ", text.lower()).strip()


def load_second_order_source_families(path: Path = SECOND_ORDER_SOURCES_PATH) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    return (load_yaml(path).get("source_families") or {})


def match_source_family(source_text: str, families: dict[str, dict[str, Any]]) -> str | None:
    """Map free-form candidate source text to a registered source family."""
    norm = normalise_source_text(source_text)
    if not norm:
        return None
    best_family: str | None = None
    best_len = 0
    for family_id, rec in families.items():
        candidates = [family_id, rec.get("name", ""), *(rec.get("aliases") or [])]
        for candidate in candidates:
            alias = normalise_source_text(str(candidate))
            if not alias:
                continue
            if alias in norm or norm in alias:
                if len(alias) > best_len:
                    best_family = family_id
                    best_len = len(alias)
    return best_family


def audit_source_family_readiness(
    source_counts: Counter[str],
    families: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Summarize whether data/fetcher candidates have a registered source family."""
    families = families if families is not None else load_second_order_source_families()
    mentioned: dict[str, dict[str, Any]] = {}
    unmatched: Counter[str] = Counter()
    for source, count in source_counts.items():
        family_id = match_source_family(source, families)
        if family_id is None:
            unmatched[source] += count
            continue
        rec = families[family_id]
        row = mentioned.setdefault(
            family_id,
            {
                "family_id": family_id,
                "name": rec.get("name"),
                "readiness": rec.get("readiness"),
                "priority": rec.get("priority"),
                "publisher_refs": rec.get("publisher_refs") or [],
                "existing_fetchers": rec.get("existing_fetchers") or [],
                "candidate_mentions": 0,
                "source_examples": [],
            },
        )
        row["candidate_mentions"] += count
        if len(row["source_examples"]) < 6:
            row["source_examples"].append(source)

    readiness_counts = Counter(row["readiness"] for row in mentioned.values())
    return {
        "registered_source_families": len(families),
        "mentioned_source_families": len(mentioned),
        "mentions_by_readiness": dict(readiness_counts),
        "source_families": sorted(
            mentioned.values(),
            key=lambda row: (-row["candidate_mentions"], row["readiness"] or "", row["family_id"]),
        ),
        "unmatched_candidate_sources": unmatched.most_common(),
    }


def load_axis_second_order_index() -> dict[str, dict[str, Any]]:
    doc = load_yaml(ROOT / "axes.yaml")
    out: dict[str, dict[str, Any]] = {}
    for axis in doc.get("axes") or []:
        axis_id = axis.get("id")
        if not axis_id:
            continue
        second = axis.get("second_order_measurement") or {}
        out[axis_id] = {
            "axis": axis_id,
            "channel": axis.get("channel"),
            "required_layers": second.get("required_layers") or [],
            "preferred_designs": second.get("preferred_designs") or [],
            "canonical_outcomes": second.get("canonical_outcomes") or [],
            "has_second_order_measurement": bool(second),
        }
    return out


def source_family_ids_for_layers(
    layers: list[str] | set[str],
    families: dict[str, dict[str, Any]],
) -> list[str]:
    layer_set = set(layers)
    if not layer_set:
        return []
    out = []
    for family_id, rec in families.items():
        if layer_set.intersection(rec.get("layers") or []):
            out.append(family_id)
    return sorted(out)


def source_family_readiness_counts(
    family_ids: list[str],
    families: dict[str, dict[str, Any]],
) -> dict[str, int]:
    counts = Counter()
    for family_id in family_ids:
        counts[families.get(family_id, {}).get("readiness", "unknown")] += 1
    return dict(counts)


def inherited_axis_requirements(
    axes: list[str],
    axis_index: dict[str, dict[str, Any]],
    families: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Return second-order requirements inherited from a policy/movement's axes."""
    required_layers: set[str] = set()
    preferred_designs: set[str] = set()
    canonical_outcomes: list[str] = []
    axes_with_requirements: list[str] = []
    missing_axis_guidance: list[str] = []
    for axis_id in axes:
        axis = axis_index.get(axis_id)
        if not axis or not axis.get("has_second_order_measurement"):
            missing_axis_guidance.append(axis_id)
            continue
        axes_with_requirements.append(axis_id)
        required_layers.update(axis.get("required_layers") or [])
        preferred_designs.update(axis.get("preferred_designs") or [])
        canonical_outcomes.extend(str(x) for x in axis.get("canonical_outcomes") or [])

    source_family_ids = source_family_ids_for_layers(required_layers, families)
    return {
        "has_axis_requirements": bool(axes_with_requirements),
        "axes_with_requirements": sorted(axes_with_requirements),
        "missing_axis_guidance": sorted(missing_axis_guidance),
        "required_layers": sorted(required_layers),
        "preferred_designs": sorted(preferred_designs),
        "canonical_outcomes": sorted(set(canonical_outcomes)),
        "source_families": source_family_ids,
        "source_readiness_counts": source_family_readiness_counts(source_family_ids, families),
    }


def text_blob(doc: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("hypothesis_id", "policy_id", "movement_id", "title", "name", "claim", "description", "doctrine", "notes"):
        value = doc.get(key)
        if isinstance(value, str):
            parts.append(value)
    scope = doc.get("scope")
    if isinstance(scope, dict):
        parts.extend(str(x) for x in scope.get("treatment_tags") or [])
        parts.extend(str(x) for x in scope.get("policy_family") or [])
    for axis in doc.get("axes_moved") or doc.get("axes_summary") or []:
        if isinstance(axis, dict):
            parts.append(str(axis.get("axis", "")))
            parts.append(str(axis.get("rationale", "")))
    for item in doc.get("linked_hypotheses") or []:
        parts.append(str(item))
    return "\n".join(parts).lower()


def is_price_or_rent_control(doc: dict[str, Any]) -> bool:
    blob = text_blob(doc)
    if any(term in blob for term in CONTROL_TERMS):
        return True
    return any(axis in blob for axis in CONTROL_AXES)


def is_policy_experiment_hypothesis(doc: dict[str, Any]) -> bool:
    """Heuristic for hypotheses that should eventually carry second-order design.

    Pure descriptive claims with no treatment or policy family can stay outside
    this audit. Anything with a treatment, intervention channel, or non-none
    policy family is a policy experiment for integrity purposes.
    """
    if doc.get("source_provenance") and doc.get("status") == "draft":
        # Corpus-mined stubs are still allowed to be rough.
        return False
    variables = doc.get("variables") or {}
    if variables.get("treatment") or variables.get("instruments"):
        return True
    if doc.get("intervention_channel"):
        return True
    scope = doc.get("scope") or {}
    families = scope.get("policy_family") or []
    if any(f != "none" for f in families):
        return True
    blob = text_blob(doc)
    return any(term in blob for term in POLICY_EXPERIMENT_TERMS)


def iter_specs(base: str) -> list[tuple[Path, dict[str, Any]]]:
    root = ROOT / base
    if not root.exists():
        return []
    paths = sorted(p for p in root.rglob("*.yaml") if not p.name.startswith("_") and "steelman" not in p.parts)
    return [(p, load_yaml(p)) for p in paths]


def summarize_layers(mm: dict[str, Any] | None) -> dict[str, Any]:
    if not mm:
        return {
            "has_contract": False,
            "promotion_gate": None,
            "layers": [],
            "status_counts": {},
            "required_data_gaps": [],
            "candidate_sources": [],
        }
    layers = mm.get("causal_layers") or []
    status_counts = Counter(layer.get("measurement_status", "missing") for layer in layers)
    required_data_gaps = [
        layer.get("layer")
        for layer in layers
        if layer.get("required_for_dispositive_verdict") and layer.get("measurement_status") == "data_gap"
    ]
    candidate_sources: list[str] = []
    for layer in layers:
        if layer.get("measurement_status") == "data_gap":
            candidate_sources.extend(str(src) for src in layer.get("candidate_sources") or [])
    return {
        "has_contract": True,
        "promotion_gate": mm.get("promotion_gate"),
        "layers": [layer.get("layer") for layer in layers],
        "status_counts": dict(status_counts),
        "required_data_gaps": required_data_gaps,
        "candidate_sources": sorted(set(candidate_sources)),
    }


def second_order_gate_for_hypothesis(
    doc: dict[str, Any],
    scope: str,
    *,
    strict_missing_contract: bool = False,
) -> dict[str, Any]:
    """Return whether an otherwise-public verdict should count on the scoreboard.

    The declared gate is conservative but not retroactive: hypotheses without a
    contract are flagged as gaps, while strict mode models the stronger rule
    that every in-scope policy experiment must first declare second-order
    measurement before it can affect school scores.
    """
    in_scope = include_doc(doc, scope, kind="hypothesis")
    if not in_scope:
        return {
            "scoreboard_eligible": True,
            "gate_status": "out_of_scope",
            "reason": "Hypothesis is outside this audit scope.",
            "promotion_gate": None,
            "required_data_gaps": [],
        }

    mm = doc.get("mechanism_measurement") or {}
    if not mm:
        return {
            "scoreboard_eligible": not strict_missing_contract,
            "gate_status": "missing_contract_hold" if strict_missing_contract else "missing_contract_flag",
            "reason": "No mechanism_measurement contract is present for an in-scope policy experiment.",
            "promotion_gate": None,
            "required_data_gaps": [],
        }

    summary = summarize_layers(mm)
    promotion_gate = summary.get("promotion_gate")
    required_gaps = summary.get("required_data_gaps") or []
    if promotion_gate in SECOND_ORDER_HOLD_GATES:
        return {
            "scoreboard_eligible": False,
            "gate_status": "declared_measurement_hold",
            "reason": "Hypothesis is declared screen-only/descriptive until second-order layers are measured.",
            "promotion_gate": promotion_gate,
            "required_data_gaps": required_gaps,
        }
    if required_gaps and promotion_gate not in SECOND_ORDER_PUBLIC_WITH_GAPS_GATES:
        return {
            "scoreboard_eligible": False,
            "gate_status": "required_layer_gap_hold",
            "reason": "A required second-order layer is still a data gap.",
            "promotion_gate": promotion_gate,
            "required_data_gaps": required_gaps,
        }
    if required_gaps:
        return {
            "scoreboard_eligible": True,
            "gate_status": "public_with_documented_gaps",
            "reason": "The test can stay public, but the remaining gaps are explicitly documented.",
            "promotion_gate": promotion_gate,
            "required_data_gaps": required_gaps,
        }
    return {
        "scoreboard_eligible": True,
        "gate_status": "measurement_ready",
        "reason": "Required second-order layers are measured or not required for the verdict.",
        "promotion_gate": promotion_gate,
        "required_data_gaps": [],
    }


def include_doc(doc: dict[str, Any], scope: str, *, kind: str) -> bool:
    if scope == "controls":
        return is_price_or_rent_control(doc)
    if kind == "hypothesis":
        return is_policy_experiment_hypothesis(doc)
    if kind == "policy":
        return bool(doc.get("axes_moved")) or is_price_or_rent_control(doc)
    if kind == "movement":
        return bool(doc.get("policies") or doc.get("axes_summary"))
    return True


def audit_hypotheses(scope: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, doc in iter_specs("hypotheses"):
        if not include_doc(doc, scope, kind="hypothesis"):
            continue
        mm_summary = summarize_layers(doc.get("mechanism_measurement"))
        rows.append({
            "kind": "hypothesis",
            "id": doc.get("hypothesis_id"),
            "path": str(path.relative_to(ROOT)),
            "status": doc.get("status"),
            "topic": doc.get("topic"),
            "evidence_type": doc.get("evidence_type"),
            "control_focus": is_price_or_rent_control(doc),
            **mm_summary,
        })
    return rows


def audit_policies(
    scope: str,
    axis_index: dict[str, dict[str, Any]] | None = None,
    families: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    axis_index = axis_index if axis_index is not None else load_axis_second_order_index()
    families = families if families is not None else load_second_order_source_families()
    rows: list[dict[str, Any]] = []
    for path, doc in iter_specs("policies"):
        if not include_doc(doc, scope, kind="policy"):
            continue
        axes = [a.get("axis") for a in doc.get("axes_moved") or [] if isinstance(a, dict)]
        design = doc.get("evaluation_design") or {}
        inherited = inherited_axis_requirements(axes, axis_index, families)
        if design:
            evaluation_design_status = "explicit"
        elif inherited["has_axis_requirements"]:
            evaluation_design_status = "axis_inherited_missing_explicit_design"
        else:
            evaluation_design_status = "missing_axis_requirements"
        rows.append({
            "kind": "policy",
            "id": doc.get("policy_id"),
            "path": str(path.relative_to(ROOT)),
            "status": doc.get("status"),
            "control_focus": is_price_or_rent_control(doc),
            "has_evaluation_design": bool(design),
            "control_axes": sorted(axis for axis in axes if axis in CONTROL_AXES),
            "axes": sorted(axis for axis in axes if axis),
            "design_features": design.get("design_features") or [],
            "known_data_gaps": design.get("known_data_gaps") or [],
            "evaluation_design_status": evaluation_design_status,
            "axis_inherited_requirements": inherited,
        })
    return rows


def audit_movements(
    policy_rows: list[dict[str, Any]],
    scope: str,
    axis_index: dict[str, dict[str, Any]] | None = None,
    families: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    axis_index = axis_index if axis_index is not None else load_axis_second_order_index()
    families = families if families is not None else load_second_order_source_families()
    policy_ids_with_design = {row["id"] for row in policy_rows if row.get("has_evaluation_design")}
    policy_ids_with_axis_requirements = {
        row["id"]
        for row in policy_rows
        if (row.get("axis_inherited_requirements") or {}).get("has_axis_requirements")
    }
    policy_ids = {row["id"] for row in policy_rows}
    control_policy_ids = {row["id"] for row in policy_rows if row.get("control_focus")}
    rows: list[dict[str, Any]] = []
    for path, doc in iter_specs("movements"):
        policies = set(doc.get("policies") or [])
        if not include_doc(doc, scope, kind="movement"):
            continue
        if scope == "controls" and not policies.intersection(control_policy_ids) and not is_price_or_rent_control(doc):
            continue
        axes = [a.get("axis") for a in doc.get("axes_summary") or [] if isinstance(a, dict)]
        inherited = inherited_axis_requirements(axes, axis_index, families)
        rows.append({
            "kind": "movement",
            "id": doc.get("movement_id"),
            "path": str(path.relative_to(ROOT)),
            "status": doc.get("status"),
            "control_focus": is_price_or_rent_control(doc) or bool(policies.intersection(control_policy_ids)),
            "control_axes": sorted(axis for axis in axes if axis in CONTROL_AXES),
            "axes": sorted(axis for axis in axes if axis),
            "policies_in_audit": sorted(policies.intersection(policy_ids)),
            "policies_with_design": sorted(policies.intersection(policy_ids_with_design)),
            "policies_with_axis_requirements": sorted(policies.intersection(policy_ids_with_axis_requirements)),
            "control_policies": sorted(policies.intersection(control_policy_ids)),
            "control_policies_with_design": sorted(policies.intersection(policy_ids_with_design).intersection(control_policy_ids)),
            "axis_inherited_requirements": inherited,
        })
    return rows


def audit_axes(scope: str, axis_index: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    axis_index = axis_index if axis_index is not None else load_axis_second_order_index()
    rows: list[dict[str, Any]] = []
    for axis_id, axis in sorted(axis_index.items()):
        if scope == "controls" and axis_id not in CONTROL_AXES:
            continue
        rows.append({
            "kind": "axis",
            "id": axis_id,
            "channel": axis.get("channel"),
            "has_second_order_measurement": bool(axis.get("has_second_order_measurement")),
            "required_layers": axis.get("required_layers") or [],
            "preferred_designs": axis.get("preferred_designs") or [],
            "canonical_outcomes": axis.get("canonical_outcomes") or [],
        })
    return rows


def _score_positions_with_second_order_gate(
    scope: str,
    *,
    strict_missing_contract: bool,
) -> dict[str, Any]:
    """Mirror the scoreboard audit while applying second-order public gates."""
    import audit_scoreboard_outcomes as scoreboard

    hypotheses, coverage_index = scoreboard.build_hypothesis_index()
    positions: dict[str, dict[str, Any]] = {}
    public_claim_links = 0
    held_claims = 0
    hold_reasons: Counter[str] = Counter()
    held_by_hypothesis: Counter[str] = Counter()
    held_examples: list[dict[str, Any]] = []

    for path in sorted((ROOT / "positions").glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        position = load_yaml(path)
        position_id = position.get("position_id") or path.stem
        school = position.get("short_name") or position.get("school") or position_id
        scoreboard_role = position.get("scoreboard_role") or (
            "benchmark_control" if position_id in scoreboard.BENCHMARK_CONTROL_POSITION_IDS else "school"
        )
        counts: Counter[str] = Counter()
        adjusted_counts: Counter[str] = Counter()

        for claim_index, claim in enumerate(position.get("falsifiable_specific_claims") or []):
            hypothesis_id = claim.get("linked_hypothesis_id")
            if not hypothesis_id:
                counts["untested"] += 1
                continue

            is_public, verdict = scoreboard.hypothesis_public_verdict(hypothesis_id, hypotheses)
            hyp = hypotheses.get(hypothesis_id) or {}
            evidence_type = hyp.get("evidence_type")
            weight = scoreboard.evidence_weight(evidence_type)
            gate = second_order_gate_for_hypothesis(
                hyp,
                scope,
                strict_missing_contract=strict_missing_contract,
            )
            if is_public and not gate["scoreboard_eligible"]:
                held_claims += 1
                hold_reasons[gate["gate_status"]] += 1
                held_by_hypothesis[hypothesis_id] += 1
                if len(held_examples) < 40:
                    held_examples.append(
                        {
                            "position_id": position_id,
                            "claim_index": claim_index,
                            "hypothesis_id": hypothesis_id,
                            "gate_status": gate["gate_status"],
                            "promotion_gate": gate["promotion_gate"],
                            "required_data_gaps": gate["required_data_gaps"],
                            "claim": str(claim.get("claim") or "")[:220],
                        }
                    )
                outcome = "untested"
            elif not is_public:
                outcome = "untested"
            else:
                coverage = coverage_index.get((position_id, claim_index)) or {}
                prediction = coverage.get("school_prediction") or claim.get("school_prediction")
                polarity = coverage.get("polarity") or claim.get("claim_polarity") or "aligned"
                outcome = scoreboard.position_outcome(scoreboard.verdict_class(verdict), prediction, polarity)
                public_claim_links += 1

            counts[outcome] += 1
            adjusted_counts["net_score"] += scoreboard.outcome_score(outcome) * weight
            if outcome != "untested":
                adjusted_counts["tested_weight"] += weight

        tested = (
            counts["supports_position"]
            + counts["refutes_position"]
            + counts["partial_supports"]
            + counts["partial_refutes"]
            + counts["partial"]
        )
        net_score = (
            counts["supports_position"]
            + 0.5 * counts["partial_supports"]
            - 0.5 * counts["partial_refutes"]
            - counts["refutes_position"]
        )
        signal = scoreboard.score_signal(net_score, tested)
        adjusted_signal = scoreboard.score_signal(adjusted_counts["net_score"], adjusted_counts["tested_weight"])
        positions[position_id] = {
            "position_id": position_id,
            "school": school,
            "scoreboard_role": scoreboard_role,
            "counts": dict(counts),
            "tested": tested,
            "net_score": net_score,
            "adjusted_net_score": adjusted_counts["net_score"],
            "adjusted_tested_weight": adjusted_counts["tested_weight"],
            **signal,
            "adjusted_score_signal": adjusted_signal["score_signal"],
            "adjusted_signed_lean": adjusted_signal["signed_lean"],
            "adjusted_signal_threshold": adjusted_signal["signal_threshold"],
            "adjusted_net_margin_rate": adjusted_signal["net_margin_rate"],
        }

    return {
        "mode": "strict_missing_contract" if strict_missing_contract else "declared_gate_only",
        "public_claim_links_after_gate": public_claim_links,
        "held_claims": held_claims,
        "hold_reasons": dict(hold_reasons),
        "held_hypotheses_top": held_by_hypothesis.most_common(25),
        "held_examples": held_examples,
        "positions": positions,
    }


def scoreboard_impact(scope: str) -> dict[str, Any]:
    import audit_scoreboard_outcomes as scoreboard

    current = scoreboard.score_positions()
    declared = _score_positions_with_second_order_gate(scope, strict_missing_contract=False)
    strict = _score_positions_with_second_order_gate(scope, strict_missing_contract=True)

    def deltas(after: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for position_id, before_row in current["positions"].items():
            after_row = after["positions"].get(position_id)
            if not after_row:
                continue
            q_delta = after_row["adjusted_net_score"] - before_row["adjusted_net_score"]
            tested_delta = after_row["adjusted_tested_weight"] - before_row["adjusted_tested_weight"]
            if q_delta == 0 and tested_delta == 0:
                continue
            rows.append(
                {
                    "position_id": position_id,
                    "scoreboard_role": before_row.get("scoreboard_role"),
                    "current_q_net": before_row["adjusted_net_score"],
                    "after_q_net": after_row["adjusted_net_score"],
                    "q_net_delta": q_delta,
                    "current_tested_weight": before_row["adjusted_tested_weight"],
                    "after_tested_weight": after_row["adjusted_tested_weight"],
                    "tested_weight_delta": tested_delta,
                    "current_signal": before_row["adjusted_score_signal"],
                    "after_signal": after_row["adjusted_score_signal"],
                    "current_lean": before_row["adjusted_signed_lean"],
                    "after_lean": after_row["adjusted_signed_lean"],
                }
            )
        return sorted(rows, key=lambda row: (abs(row["q_net_delta"]), abs(row["tested_weight_delta"])), reverse=True)[:30]

    return {
        "scope": scope,
        "generated_at": date.today().isoformat(),
        "current_public_claim_links": current["public_claim_links"],
        "declared_gate_only": {
            key: value
            for key, value in declared.items()
            if key != "positions"
        },
        "declared_gate_position_deltas": deltas(declared),
        "strict_missing_contract": {
            key: value
            for key, value in strict.items()
            if key != "positions"
        },
        "strict_missing_contract_position_deltas": deltas(strict),
    }


def aggregate_policy_axis_requirements(policy_rows: list[dict[str, Any]]) -> dict[str, Any]:
    readiness_counts: Counter[str] = Counter()
    layer_counts: Counter[str] = Counter()
    design_counts: Counter[str] = Counter()
    source_family_counts: Counter[str] = Counter()
    missing_explicit_queue: list[dict[str, Any]] = []

    for row in policy_rows:
        inherited = row.get("axis_inherited_requirements") or {}
        status = row.get("evaluation_design_status") or "unknown"
        design_counts[status] += 1
        if not inherited.get("has_axis_requirements"):
            continue
        layer_counts.update(inherited.get("required_layers") or [])
        source_family_counts.update(inherited.get("source_families") or [])
        readiness_counts.update(inherited.get("source_readiness_counts") or {})
        if status == "axis_inherited_missing_explicit_design" and len(missing_explicit_queue) < 100:
            missing_explicit_queue.append(
                {
                    "id": row.get("id"),
                    "path": row.get("path"),
                    "status": row.get("status"),
                    "control_focus": row.get("control_focus"),
                    "axes": row.get("axes") or [],
                    "required_layers": inherited.get("required_layers") or [],
                    "source_readiness_counts": inherited.get("source_readiness_counts") or {},
                }
            )

    return {
        "policies_with_axis_requirements": sum(
            1 for row in policy_rows
            if (row.get("axis_inherited_requirements") or {}).get("has_axis_requirements")
        ),
        "policies_missing_explicit_design_but_axis_requirements": design_counts.get(
            "axis_inherited_missing_explicit_design",
            0,
        ),
        "evaluation_design_status_counts": dict(design_counts),
        "required_layer_policy_mentions": dict(layer_counts),
        "source_family_policy_mentions_top": source_family_counts.most_common(25),
        "source_readiness_policy_mentions": dict(readiness_counts),
        "missing_explicit_design_queue": missing_explicit_queue,
    }


def build_report(data: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Second-order measurement audit")
    lines.append("")
    lines.append("This audit checks whether policy-experiment artifacts separate first-order effects from second-order behavioral, supply, allocation, leakage, quality, welfare, distributional, implementation, and spillover effects.")
    lines.append("")
    summary = data["summary"]
    lines.append("## Summary")
    for key, value in summary.items():
        lines.append(f"- **{key}**: {value}")
    lines.append("")
    lines.append("## Hypotheses missing contracts")
    missing = [r for r in data["hypotheses"] if not r["has_contract"]]
    if missing:
        for row in missing:
            lines.append(f"- `{row['id']}` ({row['status']}, {row['path']})")
    else:
        lines.append("- None among matched price/rent-control hypotheses.")
    lines.append("")
    lines.append("## Screen-only or non-promotable hypotheses")
    gated = [
        r for r in data["hypotheses"]
        if r["has_contract"] and r.get("promotion_gate") in {"screen_only_until_second_order_measured", "descriptive_only"}
    ]
    for row in gated:
        gaps = ", ".join(row.get("required_data_gaps") or [])
        lines.append(f"- `{row['id']}` -> `{row['promotion_gate']}`; required gaps: {gaps or 'none listed'}")
    lines.append("")
    lines.append("## Policies missing evaluation designs")
    policy_missing = [r for r in data["policies"] if not r["has_evaluation_design"]]
    if policy_missing:
        for row in policy_missing:
            axes = ", ".join(row.get("control_axes") or [])
            lines.append(f"- `{row['id']}` ({row['path']}); explicit control axes: {axes or 'none'}")
    else:
        lines.append("- None among matched price/rent-control policies.")
    lines.append("")
    policy_axis = data.get("policy_axis_requirements") or {}
    if policy_axis:
        lines.append("## Axis-inherited policy requirements")
        lines.append("")
        lines.append(f"- Policies with axis-inherited second-order requirements: {policy_axis['policies_with_axis_requirements']}")
        lines.append(f"- Policies missing explicit evaluation design despite axis requirements: {policy_axis['policies_missing_explicit_design_but_axis_requirements']}")
        lines.append(f"- Evaluation-design status counts: `{json.dumps(policy_axis['evaluation_design_status_counts'], sort_keys=True)}`")
        lines.append(f"- Source readiness across policy-axis requirements: `{json.dumps(policy_axis['source_readiness_policy_mentions'], sort_keys=True)}`")
        lines.append("")
        lines.append("### Most common required layers")
        for layer, count in sorted(
            policy_axis.get("required_layer_policy_mentions", {}).items(),
            key=lambda item: (-item[1], item[0]),
        )[:15]:
            lines.append(f"- `{layer}` ({count})")
        lines.append("")
        lines.append("### Top source-family requirements")
        for family_id, count in policy_axis.get("source_family_policy_mentions_top") or []:
            lines.append(f"- `{family_id}` ({count})")
        lines.append("")
        queue = policy_axis.get("missing_explicit_design_queue") or []
        if queue:
            lines.append("### Missing explicit design queue")
            for row in queue[:25]:
                axes = ", ".join(row.get("axes") or [])
                readiness = json.dumps(row.get("source_readiness_counts") or {}, sort_keys=True)
                lines.append(f"- `{row['id']}` ({row['status']}, {row['path']}): axes={axes}; source readiness=`{readiness}`")
            lines.append("")
    lines.append("## Movement axis/design gaps")
    movement_gaps = [
        r for r in data["movements"]
        if r["policies_in_audit"] and not r["policies_with_design"]
    ]
    if movement_gaps:
        for row in movement_gaps:
            lines.append(f"- `{row['id']}` has audited policies {row['policies_in_audit']} but no child policy has an evaluation design.")
    else:
        lines.append("- None among matched movements.")
    lines.append("")
    lines.append("## Axes missing second-order guidance")
    axis_gaps = [r for r in data["axes"] if not r["has_second_order_measurement"]]
    if axis_gaps:
        for row in axis_gaps:
            lines.append(f"- `{row['id']}` ({row['channel']})")
    else:
        lines.append("- None among matched axes.")
    lines.append("")
    lines.append("## Data/fetcher gap candidates")
    for source, count in data["data_gap_candidates"]:
        lines.append(f"- {source} ({count})")
    lines.append("")
    source_readiness = data.get("source_family_readiness") or {}
    if source_readiness:
        lines.append("## Data/fetcher readiness")
        lines.append("")
        lines.append(f"- Registered source families: {source_readiness['registered_source_families']}")
        lines.append(f"- Mentioned source families: {source_readiness['mentioned_source_families']}")
        lines.append(f"- Mentions by readiness: `{json.dumps(source_readiness['mentions_by_readiness'], sort_keys=True)}`")
        unmatched = source_readiness.get("unmatched_candidate_sources") or []
        lines.append(f"- Unmatched candidate source labels: {len(unmatched)}")
        lines.append("")
        lines.append("### Mentioned source families")
        families = source_readiness.get("source_families") or []
        if families:
            for row in families:
                fetcher_text = ", ".join(row.get("existing_fetchers") or []) or "none"
                lines.append(
                    f"- `{row['family_id']}` ({row['readiness']}, priority={row['priority']}): "
                    f"{row['candidate_mentions']} mention(s); fetchers: {fetcher_text}"
                )
        else:
            lines.append("- No data/fetcher candidates mapped to a registered source family.")
        if unmatched:
            lines.append("")
            lines.append("### Unmatched source labels")
            for source, count in unmatched[:25]:
                lines.append(f"- {source} ({count})")
        lines.append("")
    impact = data.get("scoreboard_impact") or {}
    if impact:
        declared = impact["declared_gate_only"]
        strict = impact["strict_missing_contract"]
        lines.append("## Scoreboard impact")
        lines.append("")
        lines.append(f"- Current public claim links: {impact['current_public_claim_links']}")
        lines.append(f"- After declared second-order gates: {declared['public_claim_links_after_gate']} public, {declared['held_claims']} held")
        lines.append(f"- After strict missing-contract gate: {strict['public_claim_links_after_gate']} public, {strict['held_claims']} held")
        if declared["hold_reasons"]:
            lines.append(f"- Declared-gate hold reasons: `{json.dumps(declared['hold_reasons'], sort_keys=True)}`")
        if strict["hold_reasons"]:
            lines.append(f"- Strict-gate hold reasons: `{json.dumps(strict['hold_reasons'], sort_keys=True)}`")
        lines.append("")
        lines.append("### Largest declared-gate scoreboard deltas")
        if impact["declared_gate_position_deltas"]:
            for row in impact["declared_gate_position_deltas"][:12]:
                lines.append(
                    f"- `{row['position_id']}`: q-net {row['current_q_net']:.1f} -> "
                    f"{row['after_q_net']:.1f} ({row['q_net_delta']:+.1f}); "
                    f"tested weight {row['current_tested_weight']:.1f} -> {row['after_tested_weight']:.1f}"
                )
        else:
            lines.append("- No public scoreboard claims are affected by declared gates.")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=["all", "controls"], default="all")
    parser.add_argument("--write", action="store_true", help="Write JSON and Markdown audit artifacts under engine/audits.")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()

    axis_index = load_axis_second_order_index()
    source_families = load_second_order_source_families()
    hypotheses = audit_hypotheses(args.scope)
    policies = audit_policies(args.scope, axis_index=axis_index, families=source_families)
    movements = audit_movements(policies, args.scope, axis_index=axis_index, families=source_families)
    axes = audit_axes(args.scope, axis_index=axis_index)

    source_counts: Counter[str] = Counter()
    for row in hypotheses:
        source_counts.update(row.get("candidate_sources") or [])
    for row in policies:
        source_counts.update(row.get("known_data_gaps") or [])
    source_family_readiness = audit_source_family_readiness(source_counts)
    policy_axis_requirements = aggregate_policy_axis_requirements(policies)

    summary = {
        "matched_hypotheses": len(hypotheses),
        "hypotheses_with_contract": sum(1 for r in hypotheses if r["has_contract"]),
        "control_focused_hypotheses": sum(1 for r in hypotheses if r.get("control_focus")),
        "matched_policies": len(policies),
        "policies_with_evaluation_design": sum(1 for r in policies if r["has_evaluation_design"]),
        "policies_with_axis_second_order_requirements": policy_axis_requirements["policies_with_axis_requirements"],
        "policies_missing_explicit_design_but_axis_requirements": policy_axis_requirements["policies_missing_explicit_design_but_axis_requirements"],
        "control_focused_policies": sum(1 for r in policies if r.get("control_focus")),
        "matched_movements": len(movements),
        "movements_with_control_axis": sum(1 for r in movements if r["control_axes"]),
        "matched_axes": len(axes),
        "axes_with_second_order_measurement": sum(1 for r in axes if r["has_second_order_measurement"]),
    }
    data = {
        "summary": summary,
        "hypotheses": hypotheses,
        "policies": policies,
        "movements": movements,
        "axes": axes,
        "data_gap_candidates": source_counts.most_common(),
        "source_family_readiness": source_family_readiness,
        "policy_axis_requirements": policy_axis_requirements,
        "scoreboard_impact": scoreboard_impact(args.scope),
    }

    if args.write:
        out_dir = ROOT / "engine" / "audits"
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = f"second_order_measurement_audit_{args.date}"
        if args.scope != "all":
            stem = f"{stem}_{args.scope}"
        (out_dir / f"{stem}.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        (out_dir / f"{stem}.md").write_text(build_report(data) + "\n")
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
