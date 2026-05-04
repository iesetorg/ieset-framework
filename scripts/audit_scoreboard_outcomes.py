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
        examples: list[dict[str, Any]] = []

        for claim_index, claim in enumerate(position.get("falsifiable_specific_claims") or []):
            hypothesis_id = claim.get("linked_hypothesis_id")
            if not hypothesis_id:
                counts["untested"] += 1
                continue

            is_public, verdict = hypothesis_public_verdict(hypothesis_id, hypotheses)
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
            if outcome != "untested" and len(examples) < 12:
                examples.append(
                    {
                        "claim_index": claim_index,
                        "hypothesis_id": hypothesis_id,
                        "school_prediction": prediction,
                        "polarity": polarity,
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
        denominator = (
            counts["supports_position"]
            + counts["refutes_position"]
            + counts["partial_supports"]
            + counts["partial_refutes"]
        )
        support_rate = (
            (counts["supports_position"] + 0.5 * counts["partial_supports"] - 0.5 * counts["partial_refutes"])
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
            "support_rate": support_rate,
            "examples": examples,
        }

    return {
        "generated_at": date.today().isoformat(),
        "methodology": {
            "principle": "Score school outcomes from verdict + school_prediction + polarity; never from raw empirical_status alone.",
            "win_rule": "SUPPORTED hypothesis verdict supports schools that predicted supported and refutes schools that predicted falsified; REFUTED reverses that.",
            "partial_rule": "Directional partials count half-weight in the predicted direction; neutral partials do not affect net score.",
        },
        "public_claim_links": public_claim_links,
        "positions": positions,
        "raw_status_misread_risks": raw_status_misread_risks,
    }


def write_outputs(audit: dict[str, Any], out_base: Path) -> None:
    out_base.parent.mkdir(parents=True, exist_ok=True)
    out_base.with_suffix(".json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")

    positions = audit["positions"]
    ranked = sorted(positions.values(), key=lambda p: (p["net_score"], p["tested"]), reverse=True)
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
        "",
        "## Ranked School Outcomes",
        "",
        "| school | net | tested | supports | partial + | partial - | refutes | neutral | untested |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in ranked:
        c = Counter(row["counts"])
        lines.append(
            f"| `{row['position_id']}` | {row['net_score']:.1f} | {row['tested']} | "
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
            f"- `{position_id}`: net={row['net_score']:.1f}; supports={c['supports_position']}; "
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
