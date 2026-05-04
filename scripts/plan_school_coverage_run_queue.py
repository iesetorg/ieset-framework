#!/usr/bin/env python3
"""Plan the highest-leverage pending runs for school coverage balance.

This does not create, alter, or score hypotheses. It ranks already-linked,
not-yet-public hypotheses by how many under-covered schools they would help if
they were repaired or run successfully.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from audit_scoreboard_outcomes import load_yaml
from audit_school_coverage_balance import (
    DEFAULT_LINKED_FLOOR,
    DEFAULT_TESTED_FLOOR,
    ROOT,
    STUB_RULE_MARKER,
    build_web_hypothesis_index,
    has_web_public_verdict,
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
) -> dict[str, dict[str, Any]]:
    states: dict[str, dict[str, Any]] = {}
    for path in sorted((ROOT / "positions").glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        position = load_yaml(path)
        position_id = position.get("position_id") or path.stem
        school = position.get("school") or position.get("short_name") or position_id
        claims = position.get("falsifiable_specific_claims") or []

        linked: set[str] = set()
        tested: set[str] = set()
        pending: set[str] = set()
        for claim in claims:
            hypothesis_id = claim.get("linked_hypothesis_id")
            if not hypothesis_id or hypothesis_id not in hypotheses:
                continue
            linked.add(hypothesis_id)
            if has_web_public_verdict(hypothesis_id, hypotheses):
                tested.add(hypothesis_id)
            else:
                pending.add(hypothesis_id)

        states[position_id] = {
            "position_id": position_id,
            "school": school,
            "linked": sorted(linked),
            "tested": sorted(tested),
            "pending": sorted(pending),
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
            "new_hypothesis_gate": "Run/repair existing pending links first. Add new hypotheses only where linked coverage remains below the selected floor after pending runs are exhausted.",
        },
        "summary": {
            "under_covered_schools": len(under_covered),
            "pending_candidates": len(rows),
            "reason_counts": dict(reason_counts),
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
        "- This queue ranks already-linked pending hypotheses by coverage unlocked for under-covered schools.",
        "- It does not change verdicts, school predictions, polarity, or net scores.",
        "- The fastest fair path is to run or repair pending hypotheses before inventing new links.",
        "- New hypotheses are allowed only where linked coverage is still below the selected floor after the pending queue is exhausted.",
        "",
        "## Summary",
        "",
        f"- Under-covered schools: {summary['under_covered_schools']}",
        f"- Pending candidates with coverage benefit: {summary['pending_candidates']}",
        f"- Top blocker types: {blocker_text}",
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
