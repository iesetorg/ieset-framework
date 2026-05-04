#!/usr/bin/env python3
"""Plan repairs needed to equalize tested scoreboard predictions by school.

This script does not change claims, verdicts, links, or scores. It targets
scoreboard prediction rows: each falsifiable school claim is one prediction.
The plan prefers repairing already-linked hidden claims before recommending
new hypothesis links, so equalization does not bend the scoring mechanism.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from audit_scoreboard_outcomes import build_hypothesis_index, hypothesis_public_verdict, load_yaml
from plan_public_visibility_repair_queue import primary_axis, visibility_status


ROOT = Path(__file__).resolve().parents[1]


def load_axis_index() -> dict[str, list[dict[str, Any]]]:
    path = ROOT / "hypotheses" / "_axis_index.yaml"
    if not path.exists():
        return {}
    import yaml

    data = yaml.safe_load(path.read_text()) or {}
    return data.get("index") or {}


def reason_effort(reason: str) -> int:
    """Lower is easier; used only for queue ordering."""
    return {
        "needs_replication_py": 1,
        "needs_sharpened_rule": 2,
        "needs_diagnostics": 2,
        "repair_invalid_diagnostics_json": 2,
        "needs_canonical_verdict": 3,
        "needs_successful_rerun": 4,
        "needs_run_dir": 5,
        "needs_linked_hypothesis": 6,
    }.get(reason, 9)


def build_plan(target: int) -> dict[str, Any]:
    hypotheses, _coverage_index = build_hypothesis_index()
    axis_index = load_axis_index()

    school_rows: list[dict[str, Any]] = []
    repair_queue: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()
    school_reason_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for path in sorted((ROOT / "positions").glob("*.yaml")):
        if path.name.startswith("_"):
            continue

        position = load_yaml(path)
        position_id = position.get("position_id") or path.stem
        school = position.get("school") or position.get("short_name") or position_id
        claims = position.get("falsifiable_specific_claims") or []

        tested = 0
        hidden_linked = 0
        unlinked = 0
        duplicate_links = 0
        linked_ids: list[str] = []
        top_axes: Counter[str] = Counter()

        for claim_index, claim in enumerate(claims):
            hypothesis_id = claim.get("linked_hypothesis_id")
            if not hypothesis_id:
                reason = "needs_linked_hypothesis"
                unlinked += 1
                reason_counts[reason] += 1
                school_reason_counts[position_id][reason] += 1
                continue

            linked_ids.append(hypothesis_id)
            hypothesis = hypotheses.get(hypothesis_id) or {}
            is_public, verdict = hypothesis_public_verdict(hypothesis_id, hypotheses)
            if is_public:
                tested += 1
                continue

            hidden_linked += 1
            status = visibility_status(hypothesis_id, hypothesis)
            reason = status["reason"]
            axis = primary_axis(axis_index, hypothesis_id)
            top_axes[axis] += 1
            reason_counts[reason] += 1
            school_reason_counts[position_id][reason] += 1
            repair_queue.append(
                {
                    "position_id": position_id,
                    "school": school,
                    "claim_index": claim_index,
                    "hypothesis_id": hypothesis_id,
                    "reason": reason,
                    "primary_axis": axis,
                    "topic": hypothesis.get("topic") or "uncategorised",
                    "verdict": verdict,
                    "runner": status.get("runner"),
                    "has_replication_py": status.get("has_replication_py"),
                    "claim": str(claim.get("claim") or "")[:260],
                }
            )

        duplicate_links = len(linked_ids) - len(set(linked_ids))
        gap = max(0, target - tested)
        existing_repair_capacity = min(gap, hidden_linked)
        new_link_or_new_hypothesis_gap = max(0, gap - hidden_linked)

        school_rows.append(
            {
                "position_id": position_id,
                "school": school,
                "total_claims": len(claims),
                "tested_predictions": tested,
                "untested_predictions": len(claims) - tested,
                "hidden_linked_predictions": hidden_linked,
                "unlinked_predictions": unlinked,
                "duplicate_claim_links": duplicate_links,
                "target_tested_predictions": target,
                "tested_gap_to_target": gap,
                "repair_existing_hidden_to_target": existing_repair_capacity,
                "new_link_or_new_hypothesis_gap_after_repairs": new_link_or_new_hypothesis_gap,
                "top_hidden_axes": top_axes.most_common(5),
                "top_blockers": school_reason_counts[position_id].most_common(6),
            }
        )

    gap_by_school = {row["position_id"]: row["tested_gap_to_target"] for row in school_rows}
    repair_queue.sort(
        key=lambda row: (
            gap_by_school.get(row["position_id"], 0),
            -reason_effort(row["reason"]),
            row["primary_axis"],
            row["hypothesis_id"],
        ),
        reverse=True,
    )
    school_rows.sort(
        key=lambda row: (
            row["tested_gap_to_target"],
            row["tested_predictions"] * -1,
            row["position_id"],
        ),
        reverse=True,
    )

    return {
        "generated_at": date.today().isoformat(),
        "target_tested_predictions": target,
        "methodology": {
            "unit": "Scoreboard prediction rows, not net scores and not unique hypothesis IDs.",
            "principle": "Repair existing hidden linked claims first; add new links only after current registered claims cannot reach the target.",
            "non_goals": "This plan does not select links by observed verdict and does not alter school_prediction, polarity, or result cards.",
        },
        "summary": {
            "schools": len(school_rows),
            "current_tested_range": [
                min(row["tested_predictions"] for row in school_rows),
                max(row["tested_predictions"] for row in school_rows),
            ],
            "total_tested_gap_to_target": sum(row["tested_gap_to_target"] for row in school_rows),
            "repair_existing_hidden_to_target": sum(row["repair_existing_hidden_to_target"] for row in school_rows),
            "new_link_or_new_hypothesis_gap_after_repairs": sum(
                row["new_link_or_new_hypothesis_gap_after_repairs"] for row in school_rows
            ),
            "reason_counts": dict(reason_counts),
        },
        "schools": school_rows,
        "repair_queue": repair_queue,
    }


def format_pairs(pairs: list[list[Any]] | list[tuple[Any, Any]]) -> str:
    if not pairs:
        return "-"
    return ", ".join(f"{key} ({value})" for key, value in pairs)


def write_outputs(plan: dict[str, Any], out_base: Path, limit: int) -> None:
    out_base.parent.mkdir(parents=True, exist_ok=True)
    out_base.with_suffix(".json").write_text(json.dumps(plan, indent=2) + "\n")

    summary = plan["summary"]
    target = plan["target_tested_predictions"]
    lines = [
        "# School Tested Equalization Plan",
        "",
        f"Generated: {plan['generated_at']}",
        f"Target tested prediction rows per school: `{target}`",
        "",
        "## Methodology Gate",
        "",
        "- Unit is scoreboard prediction rows, not net scores and not unique hypothesis IDs.",
        "- Existing hidden linked claims are repaired before any new links are recommended.",
        "- The plan does not change verdicts, polarity, school predictions, or score weights.",
        "",
        "## Summary",
        "",
        f"- Schools tracked: {summary['schools']}",
        f"- Current tested range: {summary['current_tested_range'][0]}-{summary['current_tested_range'][1]}",
        f"- Total tested gap to target: {summary['total_tested_gap_to_target']}",
        f"- Gap fillable by repairing existing hidden linked claims: {summary['repair_existing_hidden_to_target']}",
        f"- New link/new hypothesis gap after repairs: {summary['new_link_or_new_hypothesis_gap_after_repairs']}",
        f"- Blocker counts: `{summary['reason_counts']}`",
        "",
        "## School Gaps",
        "",
        "| school | tested | untested | hidden linked | unlinked | gap | repair existing | new link gap | top blockers | top axes |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in plan["schools"]:
        lines.append(
            f"| `{row['position_id']}` | {row['tested_predictions']} | {row['untested_predictions']} | "
            f"{row['hidden_linked_predictions']} | {row['unlinked_predictions']} | "
            f"{row['tested_gap_to_target']} | {row['repair_existing_hidden_to_target']} | "
            f"{row['new_link_or_new_hypothesis_gap_after_repairs']} | "
            f"{format_pairs(row['top_blockers'])} | {format_pairs(row['top_hidden_axes'])} |"
        )

    lines += [
        "",
        "## First Repair Queue",
        "",
        "| school | claim | hypothesis | reason | axis | runner |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    for row in plan["repair_queue"][:limit]:
        lines.append(
            f"| `{row['position_id']}` | {row['claim_index']} | `{row['hypothesis_id']}` | "
            f"`{row['reason']}` | `{row['primary_axis']}` | `{row['runner'] or '-'}` |"
        )

    lines += [
        "",
        "## First Repair IDs",
        "",
        "Use this list for bounded rerun/repair waves; repeated IDs can affect multiple schools.",
    ]
    seen: set[str] = set()
    for row in plan["repair_queue"]:
        hypothesis_id = row["hypothesis_id"]
        if hypothesis_id in seen:
            continue
        seen.add(hypothesis_id)
        lines.append(f"- `{hypothesis_id}`")
        if len(seen) >= limit:
            break

    out_base.with_suffix(".md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=100)
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument(
        "--out",
        default=f"engine/audits/school_tested_equalization_{date.today().isoformat()}",
    )
    args = parser.parse_args()

    plan = build_plan(args.target)
    out_base = ROOT / args.out
    write_outputs(plan, out_base, args.limit)
    print(f"Wrote {out_base.with_suffix('.json')}")
    print(f"Wrote {out_base.with_suffix('.md')}")
    print(json.dumps(plan["summary"], indent=2))


if __name__ == "__main__":
    main()
