#!/usr/bin/env python3
"""Plan pending runs with pre-run school forecasts for coverage balance.

This does not create, alter, or score hypotheses. It ranks already-linked,
not-yet-public hypotheses that already have an eligible pre-run school forecast
by how many under-covered schools they could help after evidence repair.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from audit_scoreboard_outcomes import (
    BENCHMARK_CONTROL_POSITION_IDS,
    build_hypothesis_index,
    hypothesis_public_verdict,
    live_evidence_index,
    load_school_timing_index,
    load_yaml,
    position_outcome,
    school_prediction_pre_run,
    verdict_class,
)
from audit_school_coverage_balance import (
    DEFAULT_LINKED_FLOOR,
    DEFAULT_TESTED_FLOOR,
    ROOT,
    STUB_RULE_MARKER,
    build_web_hypothesis_index,
    load_axis_index,
    primary_axis,
)


def strict_json_load(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return (
            json.loads(
                path.read_text(),
                parse_constant=lambda value: (_ for _ in ()).throw(
                    ValueError(f"non-standard JSON constant: {value}")
                ),
            ),
            None,
        )
    except Exception as exc:
        return None, str(exc).splitlines()[0]


def pending_reason(hypothesis_id: str, hypothesis: dict[str, Any]) -> str:
    run_dir = ROOT / "engine" / "runs" / hypothesis_id
    diagnostics_path = run_dir / "diagnostics.json"
    replication_path = run_dir / "replication.py"
    if not run_dir.exists():
        return "needs_run_dir"
    if not diagnostics_path.exists():
        return "needs_diagnostics"
    diagnostics, error = strict_json_load(diagnostics_path)
    if error:
        return "repair_invalid_diagnostics_json"
    verdict = (diagnostics.get("verdict") or "").lower().strip()
    if not verdict:
        return "needs_canonical_verdict"
    if verdict.startswith(("inconclusive", "blocked", "error", "no verdict")):
        return "needs_successful_rerun"
    if not replication_path.exists():
        return "needs_replication"

    falsification = hypothesis.get("falsification") or {}
    rule = (falsification.get("rule") or "").lower()
    if STUB_RULE_MARKER in rule:
        note_text = f"{hypothesis.get('notes') or ''} {hypothesis.get('methodology_note') or ''}".lower()
        if not any(
            marker in note_text
            for marker in ("dispositive", "sharpened", "primary (dispositive")
        ):
            return "needs_sharpened_rule"
    return "pending_unknown"


def collect_position_states(
    hypotheses: dict[str, dict[str, Any]],
    linked_floor: int,
    tested_floor: int,
    *,
    evidence_index: dict[str, dict[str, Any]] | None = None,
    timing_index: dict[str, dict[str, Any]] | None = None,
    coverage_index: dict[tuple[str, int], dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    if evidence_index is None:
        evidence_index = live_evidence_index()
    if timing_index is None:
        timing_index = load_school_timing_index()
    if coverage_index is None:
        _, coverage_index = build_hypothesis_index()
    states: dict[str, dict[str, Any]] = {}
    for path in sorted((ROOT / "positions").glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        position = load_yaml(path)
        position_id = position.get("position_id") or path.stem
        if (position.get("scoreboard_role") == "benchmark_control"
                or position_id in BENCHMARK_CONTROL_POSITION_IDS):
            continue
        school = position.get("school") or position.get("short_name") or position_id
        claims = position.get("falsifiable_specific_claims") or []

        linked: set[str] = set()
        tested: set[str] = set()
        pending: set[str] = set()
        blocked: Counter[str] = Counter()
        for claim_index, claim in enumerate(claims):
            hypothesis_id = claim.get("linked_hypothesis_id")
            if not hypothesis_id or hypothesis_id not in hypotheses:
                continue
            linked.add(hypothesis_id)
            is_public, verdict = hypothesis_public_verdict(
                hypothesis_id, hypotheses, evidence_index
            )
            evidence = evidence_index.get(hypothesis_id) or {}
            school_score_eligible = evidence.get("school_score_eligible") is not False
            coverage = coverage_index.get((position_id, claim_index)) or {}
            prediction = coverage.get("school_prediction") or claim.get("school_prediction")
            polarity = coverage.get("polarity") or claim.get("claim_polarity") or "aligned"
            prediction_pre_run = school_prediction_pre_run(
                timing_index, position_id, claim_index, claim, prediction, polarity
            )
            outcome = position_outcome(verdict_class(verdict), prediction, polarity)
            if is_public and school_score_eligible and prediction_pre_run and outcome != "untested":
                tested.add(hypothesis_id)
            elif not is_public and school_score_eligible and prediction_pre_run:
                pending.add(hypothesis_id)
            elif is_public and not school_score_eligible:
                blocked["school_score_eligible_false"] += 1
            elif not is_public and evidence.get("registration_status") == "registered_no_run":
                blocked["awaiting_first_run"] += 1
            elif not prediction_pre_run:
                blocked["school_prediction_not_pre_run"] += 1
            else:
                blocked["public_verdict_not_scorable"] += 1
        pending.difference_update(tested)

        states[position_id] = {
            "position_id": position_id,
            "school": school,
            "linked": sorted(linked),
            "tested": sorted(tested),
            "pending": sorted(pending),
            "blocked_claim_reasons": dict(blocked),
            "linked_gap": max(0, linked_floor - len(linked)),
            "tested_gap": max(0, tested_floor - len(tested)),
        }
    return states


def plan_queue(limit: int, linked_floor: int, tested_floor: int) -> dict[str, Any]:
    hypotheses = build_web_hypothesis_index()
    axis_index = load_axis_index()
    states = collect_position_states(hypotheses, linked_floor, tested_floor)
    under_covered = {
        position_id: state
        for position_id, state in states.items()
        if state["linked_gap"] > 0 or state["tested_gap"] > 0
    }

    by_hypothesis: dict[str, dict[str, Any]] = {}
    for position_id, state in under_covered.items():
        for hypothesis_id in state["pending"]:
            hypothesis = hypotheses[hypothesis_id]
            entry = by_hypothesis.setdefault(
                hypothesis_id,
                {
                    "hypothesis_id": hypothesis_id,
                    "claim": hypothesis.get("claim")
                    or hypothesis.get("title")
                    or hypothesis_id,
                    "topic": hypothesis.get("topic") or "uncategorised",
                    "primary_axis": primary_axis(axis_index, hypothesis_id),
                    "reason": pending_reason(hypothesis_id, hypothesis),
                    "helps_schools": [],
                    "coverage_score": 0.0,
                },
            )
            if state["tested_gap"] <= 0:
                continue
            # Weight schools with bigger run gaps more heavily, while keeping
            # each additional school as a concrete benefit.
            school_weight = 1.0 + (state["tested_gap"] / max(1, tested_floor))
            entry["coverage_score"] += school_weight
            entry["helps_schools"].append(
                {
                    "position_id": position_id,
                    "school": state["school"],
                    "tested_gap": state["tested_gap"],
                    "linked_gap": state["linked_gap"],
                }
            )

    rows = [
        row
        for row in by_hypothesis.values()
        if row["coverage_score"] > 0 and row["helps_schools"]
    ]
    for row in rows:
        row["helps_schools"].sort(
            key=lambda item: (item["tested_gap"], item["linked_gap"]),
            reverse=True,
        )
        row["school_count"] = len(row["helps_schools"])
        row["coverage_score"] = round(row["coverage_score"], 3)

    rows.sort(
        key=lambda row: (
            row["coverage_score"],
            row["school_count"],
            row["reason"] == "repair_invalid_diagnostics_json",
        ),
        reverse=True,
    )

    reason_counts = Counter(row["reason"] for row in rows)
    blocked_claim_reasons = Counter()
    for state in states.values():
        blocked_claim_reasons.update(state["blocked_claim_reasons"])
    axis_counts = Counter(row["primary_axis"] for row in rows)
    school_pending_counts = {
        position_id: len(state["pending"])
        for position_id, state in under_covered.items()
    }
    school_gap_counts = {
        position_id: {
            "linked_gap": state["linked_gap"],
            "tested_gap": state["tested_gap"],
            "pending": len(state["pending"]),
            "blocked_claim_reasons": state["blocked_claim_reasons"],
        }
        for position_id, state in under_covered.items()
    }
    remaining_link_gap_after_pending = sum(state["linked_gap"] for state in under_covered.values())
    tested_gap_after_exhausting_pending = sum(
        max(0, state["tested_gap"] - len(state["pending"]))
        for state in under_covered.values()
    )

    return {
        "generated_at": date.today().isoformat(),
        "methodology": {
            "principle": "Rank already-linked pending hypotheses by coverage unlocked for under-covered schools.",
            "coverage_floor": {
                "unique_hypotheses": linked_floor,
                "unique_tested": tested_floor,
            },
            "score": "For each under-covered school helped: 1 + tested_gap/selected_tested_floor. One hypothesis can help multiple schools.",
            "non_action": "This queue does not change scores or verdicts; it only prioritizes work.",
            "new_hypothesis_gate": "Run/repair eligible pre-run pending links first. Any remaining tested gap requires new prospectively registered school predictions and tests; attaching a school to an old result cannot fill it.",
        },
        "summary": {
            "under_covered_schools": len(under_covered),
            "pending_candidates": len(rows),
            "reason_counts": dict(reason_counts),
            "blocked_claim_reasons": dict(blocked_claim_reasons),
            "top_axes": axis_counts.most_common(10),
            "school_pending_counts": school_pending_counts,
            "school_gap_counts": school_gap_counts,
            "remaining_link_gap_after_pending": remaining_link_gap_after_pending,
            "tested_gap_after_exhausting_pending": tested_gap_after_exhausting_pending,
        },
        "queue": rows[:limit],
    }


def school_list(row: dict[str, Any], max_items: int = 5) -> str:
    schools = [item["position_id"] for item in row["helps_schools"][:max_items]]
    suffix = ""
    if len(row["helps_schools"]) > max_items:
        suffix = f" +{len(row['helps_schools']) - max_items}"
    return ", ".join(f"`{school}`" for school in schools) + suffix


def write_outputs(plan: dict[str, Any], out_base: Path) -> None:
    out_base.parent.mkdir(parents=True, exist_ok=True)
    out_base.with_suffix(".json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    out_base.with_suffix(".ids").write_text(
        "\n".join(row["hypothesis_id"] for row in plan["queue"]) + "\n"
    )

    summary = plan["summary"]
    blocker_text = ", ".join(
        f"{k}={v}" for k, v in Counter(summary["reason_counts"]).most_common(6)
    ) or "none"
    lines = [
        "# School Coverage Run Queue",
        "",
        f"Generated: {plan['generated_at']}",
        "",
        "## Methodology Gate",
        "",
        "- This queue ranks hidden linked hypotheses only where a reciprocal school forecast was frozen before the first run.",
        "- Historical school links, school-score holds, and unrun future registrations remain visible but cannot enter this existing-result repair queue.",
        "- It does not change verdicts, school predictions, polarity, or net scores.",
        "- Repair eligible pre-run pending hypotheses first, then preregister new school predictions and tests for the remaining gap.",
        "- Attaching a school to an existing result after its first run does not create an advance result.",
        "",
        "## Summary",
        "",
        f"- Under-covered schools: {summary['under_covered_schools']}",
        f"- Pending candidates with coverage benefit: {summary['pending_candidates']}",
        f"- Top blocker types: {blocker_text}",
        f"- Claim links held outside the repair queue: `{summary['blocked_claim_reasons']}`",
        f"- Linked gap remaining after pending runs: {summary['remaining_link_gap_after_pending']}",
        f"- Tested gap remaining after exhausting pending runs: {summary['tested_gap_after_exhausting_pending']}",
        "",
        "## Highest-Leverage Queue",
        "",
        "| rank | hypothesis | score | schools helped | axis | blocker |",
        "| ---: | --- | ---: | ---: | --- | --- |",
    ]
    for idx, row in enumerate(plan["queue"], start=1):
        lines.append(
            f"| {idx} | `{row['hypothesis_id']}` | {row['coverage_score']:.3f} | "
            f"{row['school_count']} ({school_list(row)}) | `{row['primary_axis']}` | {row['reason']} |"
        )

    lines += [
        "",
        "## First Batch IDs",
        "",
        "Use the companion `.ids` file for automation input. The first 20 IDs are:",
    ]
    for row in plan["queue"][:20]:
        lines.append(f"- `{row['hypothesis_id']}`")

    out_base.with_suffix(".md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--linked-floor", type=int, default=DEFAULT_LINKED_FLOOR)
    parser.add_argument("--tested-floor", type=int, default=DEFAULT_TESTED_FLOOR)
    parser.add_argument(
        "--out",
        default=str(ROOT / "engine" / "audits" / f"school_coverage_run_queue_{date.today().isoformat()}"),
    )
    args = parser.parse_args()
    plan = plan_queue(args.limit, args.linked_floor, args.tested_floor)
    out_base = Path(args.out)
    write_outputs(plan, out_base)
    print(f"Wrote {out_base.with_suffix('.json')}")
    print(f"Wrote {out_base.with_suffix('.md')}")
    print(f"Wrote {out_base.with_suffix('.ids')}")
    print(json.dumps(plan["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
