#!/usr/bin/env python3
"""Generate claim-level scoreboard promotion gates.

This joins the position scoreboard audit with second-order measurement gates so
the public UI/API can distinguish three separate questions:

* Did the hypothesis survive or fail?
* Did the school forecast that result?
* Is a failure forecast mechanism-attributable, or only a weak broad-screen hit?
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import audit_scoreboard_outcomes as scoreboard
import audit_second_order_measurement as second_order


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "engine" / "scoreboard_second_order_gates.json"
OUT_MD = ROOT / "engine" / "scoreboard_second_order_gates.md"

DISCRIMINATING_DESIGN_TERMS = (
    "controlled_vs_uncontrolled_categories",
    "treated_vs_untreated_units",
    "adjacent_market_comparison",
    "border_comparison",
    "high_frequency_event_study",
    "triple_difference",
    "distributional_decomposition",
    "welfare_accounting",
    "mechanism_channel_decomposition",
    "synthetic_control",
    "difference-in-differences",
    "diff-in-diff",
    "event study",
    "instrument",
    "decomposition",
    "heterogeneity",
)


def compact_lower_text(parts: list[Any]) -> str:
    return " ".join(str(part).lower() for part in parts if part not in (None, ""))


def has_mechanism_discriminating_design(hypothesis: dict[str, Any]) -> bool:
    """Whether the spec can attribute a failed hypothesis to a rival mechanism."""
    variables = hypothesis.get("variables") or {}
    if variables.get("decomposition_channels"):
        return True

    mechanism = hypothesis.get("mechanism_measurement") or {}
    design_features = mechanism.get("design_features") or []
    causal_layers = mechanism.get("causal_layers") or []
    measured_required_layers = [
        layer.get("layer")
        for layer in causal_layers
        if layer.get("required_for_dispositive_verdict")
        and layer.get("measurement_status") == "measured"
    ]
    if design_features and measured_required_layers:
        return True

    estimator = hypothesis.get("estimator") or {}
    falsification = hypothesis.get("falsification") or {}
    text = compact_lower_text(
        [
            estimator.get("template"),
            estimator.get("notes"),
            falsification.get("test"),
            falsification.get("rule"),
            hypothesis.get("methodology_note"),
            hypothesis.get("notes"),
            " ".join(str(x) for x in design_features),
        ]
    )
    return any(term in text for term in DISCRIMINATING_DESIGN_TERMS)


def failure_credit_for_claim(
    *,
    school_prediction: str | None,
    outcome: str,
    evidence_type: str | None,
    hypothesis: dict[str, Any],
    declared_gate: dict[str, Any],
    strict_gate: dict[str, Any],
) -> dict[str, Any]:
    """Classify credit when a school forecasted hypothesis failure.

    Raw scoreboard math can turn a REFUTED hypothesis into a school win when the
    school predicted falsification. That is only strong evidence for the school
    when the failed hypothesis was a discriminating mechanism test.
    """
    if (school_prediction or "").lower() != "falsified" or outcome != "supports_position":
        return {
            "kind": "not_failure_prediction_win",
            "recommended_multiplier": 1.0,
            "reason": "The claim is not a school win from forecasting hypothesis failure.",
        }

    if not declared_gate.get("scoreboard_eligible") or not strict_gate.get("scoreboard_eligible"):
        return {
            "kind": "second_order_gate_hold",
            "recommended_multiplier": 0.0,
            "reason": "The linked hypothesis is held by a second-order measurement gate.",
        }

    discriminating = has_mechanism_discriminating_design(hypothesis)
    if evidence_type == "causal" and discriminating:
        return {
            "kind": "full_discriminating_failure_credit",
            "recommended_multiplier": 1.0,
            "reason": "The failure forecast is backed by a causal, mechanism-discriminating design.",
        }
    if evidence_type == "causal":
        return {
            "kind": "causal_failure_credit_without_mechanism_attribution",
            "recommended_multiplier": 0.75,
            "reason": "The test is causal but does not explicitly isolate the rival mechanism.",
        }
    if discriminating:
        return {
            "kind": "partial_discriminating_failure_credit",
            "recommended_multiplier": 0.5,
            "reason": "The design targets mechanism/timing/channel differences but is not marked causal.",
        }
    if evidence_type in {"descriptive", "canonical_case_multi_metric"}:
        return {
            "kind": "weak_descriptive_failure_credit",
            "recommended_multiplier": 0.1,
            "reason": "A descriptive failure can be a clue, not a rival-school validation.",
        }
    return {
        "kind": "weak_associational_failure_credit",
        "recommended_multiplier": 0.25,
        "reason": "A broad associational failure gets at most weak credit without mechanism attribution.",
    }


def build_claim_gate_row(
    *,
    position_id: str,
    claim_index: int,
    claim: dict[str, Any],
    hypothesis: dict[str, Any],
    coverage: dict[str, Any],
    is_public: bool,
    verdict: str | None,
    scope: str,
) -> dict[str, Any]:
    hypothesis_id = claim.get("linked_hypothesis_id")
    prediction = coverage.get("school_prediction") or claim.get("school_prediction")
    polarity = coverage.get("polarity") or claim.get("claim_polarity") or "aligned"
    evidence_type = hypothesis.get("evidence_type")
    outcome = "untested"
    verdict_kind = scoreboard.verdict_class(verdict)
    if is_public:
        outcome = scoreboard.position_outcome(verdict_kind, prediction, polarity)

    declared_gate = second_order.second_order_gate_for_hypothesis(
        hypothesis,
        scope,
        strict_missing_contract=False,
    )
    strict_gate = second_order.second_order_gate_for_hypothesis(
        hypothesis,
        scope,
        strict_missing_contract=True,
    )
    failure_credit = failure_credit_for_claim(
        school_prediction=prediction,
        outcome=outcome,
        evidence_type=evidence_type,
        hypothesis=hypothesis,
        declared_gate=declared_gate,
        strict_gate=strict_gate,
    )
    evidence_weight = scoreboard.evidence_weight(evidence_type)
    raw_outcome_score = scoreboard.outcome_score(outcome) * evidence_weight
    recommended_score = raw_outcome_score
    if failure_credit["kind"] != "not_failure_prediction_win":
        recommended_score *= failure_credit["recommended_multiplier"]
    if not declared_gate["scoreboard_eligible"]:
        recommended_score = 0.0

    return {
        "position_id": position_id,
        "claim_index": claim_index,
        "hypothesis_id": hypothesis_id,
        "claim": str(claim.get("claim") or "")[:260],
        "verdict_public": bool(is_public),
        "verdict": verdict,
        "verdict_kind": verdict_kind,
        "school_prediction": prediction,
        "polarity": polarity,
        "evidence_type": evidence_type,
        "evidence_weight": evidence_weight,
        "raw_school_outcome": outcome,
        "raw_weighted_score": raw_outcome_score,
        "declared_scoreboard_eligible": bool(is_public and declared_gate["scoreboard_eligible"]),
        "strict_scoreboard_eligible": bool(is_public and strict_gate["scoreboard_eligible"]),
        "declared_gate_status": declared_gate["gate_status"],
        "strict_gate_status": strict_gate["gate_status"],
        "promotion_gate": declared_gate.get("promotion_gate") or strict_gate.get("promotion_gate"),
        "required_data_gaps": sorted(
            set(declared_gate.get("required_data_gaps") or [])
            | set(strict_gate.get("required_data_gaps") or [])
        ),
        "failure_credit_kind": failure_credit["kind"],
        "failure_credit_multiplier": failure_credit["recommended_multiplier"],
        "failure_credit_reason": failure_credit["reason"],
        "recommended_weighted_score_after_gates": recommended_score,
        "mechanism_discriminating_design": has_mechanism_discriminating_design(hypothesis),
    }


def build_gate_index(scope: str = "all") -> dict[str, Any]:
    hypotheses, coverage_index = scoreboard.build_hypothesis_index()
    claim_rows: list[dict[str, Any]] = []
    hypothesis_rows: dict[str, dict[str, Any]] = {}

    for path in sorted((ROOT / "positions").glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        position = second_order.load_yaml(path)
        position_id = position.get("position_id") or path.stem
        for claim_index, claim in enumerate(position.get("falsifiable_specific_claims") or []):
            hypothesis_id = claim.get("linked_hypothesis_id")
            if not hypothesis_id:
                continue
            hypothesis = hypotheses.get(hypothesis_id) or {}
            coverage = coverage_index.get((position_id, claim_index)) or {}
            is_public, verdict = scoreboard.hypothesis_public_verdict(hypothesis_id, hypotheses)
            row = build_claim_gate_row(
                position_id=position_id,
                claim_index=claim_index,
                claim=claim,
                hypothesis=hypothesis,
                coverage=coverage,
                is_public=is_public,
                verdict=verdict,
                scope=scope,
            )
            claim_rows.append(row)

            hyp_row = hypothesis_rows.setdefault(
                hypothesis_id,
                {
                    "hypothesis_id": hypothesis_id,
                    "evidence_type": hypothesis.get("evidence_type"),
                    "verdict_public": bool(is_public),
                    "verdict": verdict,
                    "declared_gate_status": row["declared_gate_status"],
                    "strict_gate_status": row["strict_gate_status"],
                    "declared_scoreboard_eligible_claim_links": 0,
                    "strict_scoreboard_eligible_claim_links": 0,
                    "held_claim_links_declared": 0,
                    "held_claim_links_strict": 0,
                    "failure_credit_kind_counts": Counter(),
                    "required_data_gaps": set(),
                },
            )
            if row["declared_scoreboard_eligible"]:
                hyp_row["declared_scoreboard_eligible_claim_links"] += 1
            elif row["verdict_public"]:
                hyp_row["held_claim_links_declared"] += 1
            if row["strict_scoreboard_eligible"]:
                hyp_row["strict_scoreboard_eligible_claim_links"] += 1
            elif row["verdict_public"]:
                hyp_row["held_claim_links_strict"] += 1
            hyp_row["failure_credit_kind_counts"][row["failure_credit_kind"]] += 1
            hyp_row["required_data_gaps"].update(row["required_data_gaps"])

    failure_credit_counts = Counter(row["failure_credit_kind"] for row in claim_rows)
    declared_gate_counts = Counter(row["declared_gate_status"] for row in claim_rows if row["verdict_public"])
    strict_gate_counts = Counter(row["strict_gate_status"] for row in claim_rows if row["verdict_public"])
    public_rows = [row for row in claim_rows if row["verdict_public"]]

    compact_hypotheses = []
    for row in hypothesis_rows.values():
        compact = dict(row)
        compact["failure_credit_kind_counts"] = dict(compact["failure_credit_kind_counts"])
        compact["required_data_gaps"] = sorted(compact["required_data_gaps"])
        compact_hypotheses.append(compact)

    return {
        "generated_by": "scripts/generate_scoreboard_second_order_gates.py",
        "generated_at": date.today().isoformat(),
        "scope": scope,
        "methodology": {
            "hypothesis_verdict": "The run verdict says whether the pre-registered hypothesis survived.",
            "school_forecast": "The school forecast is scored from verdict + school_prediction + polarity.",
            "mechanism_attribution": "A school gets strong credit for predicting failure only when the test discriminates the school's mechanism, channel, sign, heterogeneity, or timing.",
            "second_order_gate": "Policy-experiment links are held when required second-order layers are unmeasured or undocumented.",
        },
        "summary": {
            "claim_links": len(claim_rows),
            "public_claim_links": len(public_rows),
            "declared_scoreboard_eligible_public_links": sum(
                1 for row in public_rows if row["declared_scoreboard_eligible"]
            ),
            "declared_held_public_links": sum(
                1 for row in public_rows if not row["declared_scoreboard_eligible"]
            ),
            "strict_scoreboard_eligible_public_links": sum(
                1 for row in public_rows if row["strict_scoreboard_eligible"]
            ),
            "strict_held_public_links": sum(
                1 for row in public_rows if not row["strict_scoreboard_eligible"]
            ),
            "declared_gate_status_counts": dict(declared_gate_counts),
            "strict_gate_status_counts": dict(strict_gate_counts),
            "failure_credit_kind_counts": dict(failure_credit_counts),
        },
        "claim_links": sorted(
            claim_rows,
            key=lambda row: (
                not row["verdict_public"],
                row["position_id"],
                row["claim_index"],
                row["hypothesis_id"] or "",
            ),
        ),
        "hypotheses": sorted(compact_hypotheses, key=lambda row: row["hypothesis_id"]),
    }


def write_outputs(payload: dict[str, Any]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    summary = payload["summary"]
    lines = [
        "# Scoreboard Second-order Gates",
        "",
        "This generated artifact separates hypothesis verdicts, school forecast scoring, mechanism attribution, and second-order promotion gates.",
        "",
        "## Summary",
        "",
        f"- Claim links: {summary['claim_links']}",
        f"- Public claim links: {summary['public_claim_links']}",
        f"- Declared-gate eligible public links: {summary['declared_scoreboard_eligible_public_links']}",
        f"- Declared-gate held public links: {summary['declared_held_public_links']}",
        f"- Strict-gate eligible public links: {summary['strict_scoreboard_eligible_public_links']}",
        f"- Strict-gate held public links: {summary['strict_held_public_links']}",
        f"- Declared gate statuses: `{json.dumps(summary['declared_gate_status_counts'], sort_keys=True)}`",
        f"- Strict gate statuses: `{json.dumps(summary['strict_gate_status_counts'], sort_keys=True)}`",
        f"- Failure-credit classes: `{json.dumps(summary['failure_credit_kind_counts'], sort_keys=True)}`",
        "",
        "## Held Public Links",
        "",
        "| position | claim | hypothesis | declared gate | strict gate | gaps |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    held_rows = [
        row for row in payload["claim_links"]
        if row["verdict_public"] and (not row["declared_scoreboard_eligible"] or not row["strict_scoreboard_eligible"])
    ]
    for row in held_rows[:100]:
        gaps = ", ".join(row["required_data_gaps"]) or "-"
        lines.append(
            f"| `{row['position_id']}` | {row['claim_index']} | `{row['hypothesis_id']}` | "
            f"{row['declared_gate_status']} | {row['strict_gate_status']} | {gaps} |"
        )

    lines.extend(
        [
            "",
            "## Failure Forecast Credit",
            "",
            "| position | claim | hypothesis | evidence | class | multiplier |",
            "| --- | ---: | --- | --- | --- | ---: |",
        ]
    )
    failure_rows = [
        row for row in payload["claim_links"]
        if row["failure_credit_kind"] != "not_failure_prediction_win"
    ]
    for row in failure_rows[:100]:
        lines.append(
            f"| `{row['position_id']}` | {row['claim_index']} | `{row['hypothesis_id']}` | "
            f"{row['evidence_type'] or '-'} | {row['failure_credit_kind']} | "
            f"{row['failure_credit_multiplier']:.2f} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n")


def main() -> int:
    payload = build_gate_index(scope="all")
    write_outputs(payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
