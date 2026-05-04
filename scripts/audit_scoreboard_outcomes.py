#!/usr/bin/env python3
"""Audit school-level scoreboard outcomes from prediction + verdict polarity.

Raw hypothesis verdicts are not the same thing as school wins. If a school
predicted a hypothesis would be falsified, a SUPPORTED hypothesis verdict is a
loss for that school. This audit mirrors the web scoreboard logic so review
passes can catch raw `empirical_status` labels that are easy to misread.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
STUB_RULE_MARKER = "when this stub is promoted from draft"


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception as exc:  # pragma: no cover - defensive audit path
        return {"_parse_error": str(exc)}


def verdict_class(verdict: str | None) -> str:
    if not verdict:
        return "untested"
    v = verdict.lower().strip()
    if v.startswith(("blocked", "error", "no verdict", "inconclusive")):
        return "untested"
    if v.startswith(("weakened", "inconclusive")):
        return "partial"
    if v.startswith(("supported_subset", "supported subset")):
        return "partial_support"
    if v.startswith("supported"):
        return "supported"
    if v.startswith(("refuted", "not supported", "not_supported")):
        return "refuted"
    if v.startswith("partial") and any(
        marker in v
        for marker in (
            "direction inconclusive",
            "claim direction not auto-inferred",
            "effect magnitude effectively zero",
            "standard error/p-value not estimable",
        )
    ):
        return "partial"
    if v.startswith(("partial", "mixed", "weakly supported", "weakly_supported")):
        return "partial_support"
    return "partial"


def position_outcome(verdict_kind: str, prediction: str, polarity: str = "aligned") -> str:
    if verdict_kind == "untested":
        return "untested"
    if verdict_kind == "partial":
        return "partial"

    hyp_supported = verdict_kind == "supported"
    hyp_refuted = verdict_kind == "refuted"
    partial_dir = "toward_support" if verdict_kind == "partial_support" else None

    if polarity == "inverted":
        hyp_supported, hyp_refuted = hyp_refuted, hyp_supported
        if partial_dir == "toward_support":
            partial_dir = "toward_refute"

    pred = (prediction or "").lower()
    if partial_dir == "toward_support":
        if pred == "supported":
            return "partial_supports"
        if pred == "falsified":
            return "partial_refutes"
        return "partial"
    if partial_dir == "toward_refute":
        if pred == "supported":
            return "partial_refutes"
        if pred == "falsified":
            return "partial_supports"
        return "partial"

    if pred == "supported" and hyp_supported:
        return "supports_position"
    if pred == "supported" and hyp_refuted:
        return "refutes_position"
    if pred == "falsified" and hyp_refuted:
        return "supports_position"
    if pred == "falsified" and hyp_supported:
        return "refutes_position"
    if pred == "mixed":
        return "partial"
    return "untested"


def score_signal(net_score: float, tested: int) -> dict[str, Any]:
    """Classify tiny aggregate margins as no-call, without changing raw net."""
    if tested <= 0:
        return {
            "signal_threshold": 0.0,
            "net_margin_rate": 0.0,
            "score_signal": "untested",
        }

    signal_threshold = max(5.0, tested * 0.05)
    net_margin_rate = net_score / tested
    if abs(net_score) <= signal_threshold:
        signal = "too_close_to_call"
    elif net_score > 0:
        signal = "positive_signal"
    else:
        signal = "negative_signal"
    return {
        "signal_threshold": signal_threshold,
        "net_margin_rate": net_margin_rate,
        "score_signal": signal,
    }


def evidence_weight(evidence_type: str | None) -> float:
    if evidence_type == "causal":
        return 1.0
    if evidence_type == "associational":
        return 0.5
    if evidence_type in {"descriptive", "canonical_case_multi_metric"}:
        return 0.25
    return 0.25


def outcome_score(outcome: str) -> float:
    return {
        "supports_position": 1.0,
        "partial_supports": 0.5,
        "partial_refutes": -0.5,
        "refutes_position": -1.0,
    }.get(outcome, 0.0)


def hypothesis_public_verdict(hypothesis_id: str, hypotheses: dict[str, dict[str, Any]]) -> tuple[bool, str | None]:
    hyp = hypotheses.get(hypothesis_id) or {}
    run_dir = ROOT / "engine" / "runs" / hypothesis_id
    diagnostics_path = run_dir / "diagnostics.json"
    replication_path = run_dir / "replication.py"
    if not diagnostics_path.exists() or not replication_path.exists():
        return False, None

    try:
        diagnostics = json.loads(diagnostics_path.read_text())
    except Exception:
        return False, None

    verdict = diagnostics.get("verdict") or diagnostics.get("verdict_label")
    if verdict_class(verdict) == "untested":
        return False, verdict

    falsification = hyp.get("falsification") or {}
    rule = (falsification.get("rule") or "").lower()
    if STUB_RULE_MARKER not in rule:
        return True, verdict

    note_text = f"{hyp.get('notes') or ''} {hyp.get('methodology_note') or ''}".lower()
    if any(marker in note_text for marker in ("dispositive", "sharpened", "primary (dispositive")):
        return True, verdict

    return False, verdict


def build_hypothesis_index() -> tuple[dict[str, dict[str, Any]], dict[tuple[str, int], dict[str, Any]]]:
    hypotheses: dict[str, dict[str, Any]] = {}
    coverage_index: dict[tuple[str, int], dict[str, Any]] = {}
    hypothesis_root = ROOT / "hypotheses"
    for topic_dir in sorted(hypothesis_root.iterdir()):
        if not topic_dir.is_dir() or topic_dir.name == "steelman":
            continue
        for path in sorted(topic_dir.glob("*.yaml")):
            hyp = load_yaml(path)
            hypothesis_id = hyp.get("hypothesis_id") or path.stem
            hypotheses[hypothesis_id] = hyp
            for entry in hyp.get("covers_claims") or []:
                try:
                    key = (entry["position_id"], int(entry["claim_index"]))
                except (KeyError, TypeError, ValueError):
                    continue
                coverage_index[key] = entry
    return hypotheses, coverage_index


def score_positions() -> dict[str, Any]:
    hypotheses, coverage_index = build_hypothesis_index()

    positions: dict[str, dict[str, Any]] = {}
    raw_status_misread_risks: list[dict[str, Any]] = []
    public_claim_links = 0

    for path in sorted((ROOT / "positions").glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        position = load_yaml(path)
        position_id = position.get("position_id") or path.stem
        school = position.get("short_name") or position.get("school") or position_id
        counts: Counter[str] = Counter()
        adjusted_counts: Counter[str] = Counter()
        examples: list[dict[str, Any]] = []

        for claim_index, claim in enumerate(position.get("falsifiable_specific_claims") or []):
            hypothesis_id = claim.get("linked_hypothesis_id")
            if not hypothesis_id:
                counts["untested"] += 1
                continue

            is_public, verdict = hypothesis_public_verdict(hypothesis_id, hypotheses)
            evidence_type = (hypotheses.get(hypothesis_id) or {}).get("evidence_type")
            weight = evidence_weight(evidence_type)
            if not is_public:
                outcome = "untested"
                prediction = claim.get("school_prediction")
                polarity = claim.get("claim_polarity") or "aligned"
            else:
                coverage = coverage_index.get((position_id, claim_index)) or {}
                prediction = coverage.get("school_prediction") or claim.get("school_prediction")
                polarity = coverage.get("polarity") or claim.get("claim_polarity") or "aligned"
                outcome = position_outcome(verdict_class(verdict), prediction, polarity)
                public_claim_links += 1

            counts[outcome] += 1
            adjusted_counts["net_score"] += outcome_score(outcome) * weight
            if outcome != "untested":
                adjusted_counts["tested_weight"] += weight
            if outcome != "untested" and len(examples) < 12:
                examples.append(
                    {
                        "claim_index": claim_index,
                        "hypothesis_id": hypothesis_id,
                        "school_prediction": prediction,
                        "polarity": polarity,
                        "evidence_type": evidence_type,
                        "evidence_weight": weight,
                        "verdict": verdict,
                        "outcome": outcome,
                        "claim": str(claim.get("claim") or "")[:240],
                    }
                )

            raw_status = claim.get("empirical_status")
            if raw_status in {"supported", "falsified"} and outcome in {"supports_position", "refutes_position"}:
                if (raw_status == "supported" and outcome == "refutes_position") or (
                    raw_status == "falsified" and outcome == "supports_position"
                ):
                    raw_status_misread_risks.append(
                        {
                            "position_id": position_id,
                            "school": school,
                            "claim_index": claim_index,
                            "hypothesis_id": hypothesis_id,
                            "raw_empirical_status": raw_status,
                            "school_prediction": prediction,
                            "polarity": polarity,
                            "verdict": verdict,
                            "scoreboard_outcome": outcome,
                            "claim": str(claim.get("claim") or "")[:240],
                        }
                    )

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
        decisive_net = counts["supports_position"] - counts["refutes_position"]
        signal = score_signal(net_score, tested)
        adjusted_net_score = adjusted_counts["net_score"]
        adjusted_signal = score_signal(adjusted_net_score, adjusted_counts["tested_weight"])
        denominator = (
            counts["supports_position"]
            + counts["refutes_position"]
            + counts["partial_supports"]
            + counts["partial_refutes"]
        )
        support_rate = (
            (counts["supports_position"] + 0.5 * counts["partial_supports"])
            / denominator
            if denominator
            else 0.0
        )
        positions[position_id] = {
            "position_id": position_id,
            "school": school,
            "counts": dict(counts),
            "tested": tested,
            "net_score": net_score,
            "adjusted_net_score": adjusted_net_score,
            "adjusted_tested_weight": adjusted_counts["tested_weight"],
            "decisive_net": decisive_net,
            **signal,
            "adjusted_signal_threshold": adjusted_signal["signal_threshold"],
            "adjusted_net_margin_rate": adjusted_signal["net_margin_rate"],
            "adjusted_score_signal": adjusted_signal["score_signal"],
            "support_rate": support_rate,
            "examples": examples,
        }

    return {
        "generated_at": date.today().isoformat(),
        "methodology": {
            "principle": "Score school outcomes from verdict + school_prediction + polarity; never from raw empirical_status alone.",
            "win_rule": "SUPPORTED hypothesis verdict supports schools that predicted supported and refutes schools that predicted falsified; REFUTED reverses that.",
            "partial_rule": "Directional partials count half-weight in the predicted direction; neutral partials do not affect net score.",
            "signal_rule": "Rows with |weighted net| < max(5 points, 5% of tested predictions) are too_close_to_call, not positive or negative school findings.",
            "quality_adjustment_rule": "Q-net discounts lower-identification evidence: causal=1.0, associational=0.5, descriptive/canonical_case_multi_metric=0.25.",
        },
        "public_claim_links": public_claim_links,
        "positions": positions,
        "raw_status_misread_risks": raw_status_misread_risks,
    }


def write_outputs(audit: dict[str, Any], out_base: Path) -> None:
    out_base.parent.mkdir(parents=True, exist_ok=True)
    out_base.with_suffix(".json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")

    positions = audit["positions"]
    ranked = sorted(
        positions.values(),
        key=lambda p: (p["adjusted_net_score"], p["net_score"], p["tested"]),
        reverse=True,
    )
    lines = [
        "# Scoreboard Prediction-Outcome Audit",
        "",
        f"Generated: {audit['generated_at']}",
        "",
        "## Methodology Gate",
        "",
        "- School outcomes are computed from `verdict + school_prediction + polarity`.",
        "- Raw `empirical_status` is a hypothesis-verdict label, not automatically a school win.",
        "- `SUPPORTED` refutes a school that predicted `falsified`; `REFUTED` supports that school.",
        "- Directional partials count half-weight; neutral partials do not move net score.",
        "- Tiny aggregate margins are a no-call: `abs(net) < max(5, 5% of tested)` is `too_close_to_call`.",
        "- Q-net discounts lower-identification evidence: causal=1.0, associational=0.5, descriptive/canonical=0.25.",
        "",
        "## Ranked School Outcomes",
        "",
        "| school | signal | q-net | q-band | raw net | decisive net | tested | supports | partial + | partial - | refutes | neutral | untested |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in ranked:
        c = Counter(row["counts"])
        lines.append(
            f"| `{row['position_id']}` | {row['adjusted_score_signal']} | "
            f"{row['adjusted_net_score']:.1f} | ±{row['adjusted_signal_threshold']:.1f} | "
            f"{row['net_score']:.1f} | {row['decisive_net']} | {row['tested']} | "
            f"{c['supports_position']} | {c['partial_supports']} | {c['partial_refutes']} | "
            f"{c['refutes_position']} | {c['partial']} | {c['untested']} |"
        )

    lines += [
        "",
        "## Raw-Status Misread Risks",
        "",
        "These are claims where the raw `empirical_status` label points the opposite way from the school-level scoreboard outcome.",
        "",
    ]
    risks = audit["raw_status_misread_risks"]
    if risks:
        lines += [
            "| school | claim | hypothesis | raw status | prediction | outcome |",
            "| --- | ---: | --- | --- | --- | --- |",
        ]
        for item in risks:
            lines.append(
                f"| `{item['position_id']}` | {item['claim_index']} | `{item['hypothesis_id']}` | "
                f"{item['raw_empirical_status']} | {item['school_prediction']} | {item['scoreboard_outcome']} |"
            )
    else:
        lines.append("- None")

    lines += [
        "",
        "## Marxist-Cluster Readout",
        "",
    ]
    for position_id in ("marxian", "marxist_leninist"):
        row = positions.get(position_id)
        if not row:
            continue
        c = Counter(row["counts"])
        lines.append(
            f"- `{position_id}`: signal={row['adjusted_score_signal']}; "
            f"q-net={row['adjusted_net_score']:.1f}; raw-net={row['net_score']:.1f}; "
            f"q-band=±{row['adjusted_signal_threshold']:.1f}; supports={c['supports_position']}; "
            f"partial+={c['partial_supports']}; partial-={c['partial_refutes']}; "
            f"refutes={c['refutes_position']}; neutral={c['partial']}; untested={c['untested']}."
        )

    out_base.with_suffix(".md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default=str(ROOT / "engine" / "audits" / f"scoreboard_prediction_outcome_audit_{date.today().isoformat()}")
    )
    args = parser.parse_args()
    audit = score_positions()
    out_base = Path(args.out)
    write_outputs(audit, out_base)
    print(f"Wrote {out_base.with_suffix('.json')}")
    print(f"Wrote {out_base.with_suffix('.md')}")
    marxist = audit["positions"].get("marxist_leninist", {})
    if marxist:
        print("marxist_leninist", marxist["counts"], "net", marxist["net_score"])


if __name__ == "__main__":
    main()
