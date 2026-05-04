#!/usr/bin/env python3
"""Audit whether schools have comparable hypothesis coverage.

The scoreboard should compare school performance only after each school has a
roughly comparable opportunity set. This audit measures that opportunity set
without changing any verdicts or school scores.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from audit_scoreboard_outcomes import load_yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LINKED_FLOOR = 100
DEFAULT_TESTED_FLOOR = 60
STRETCH_LINKED_FLOOR = 125
STRETCH_TESTED_FLOOR = 80
STUB_RULE_MARKER = "when this stub is promoted from draft"


def load_axis_index() -> dict[str, list[dict[str, Any]]]:
    path = ROOT / "hypotheses" / "_axis_index.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text()) or {}
    return data.get("index") or {}


def build_web_hypothesis_index() -> dict[str, dict[str, Any]]:
    """Mirror the web loader's parse gate: malformed/no-id YAML is not in atlas."""
    hypotheses: dict[str, dict[str, Any]] = {}
    hypothesis_root = ROOT / "hypotheses"
    for topic_dir in sorted(hypothesis_root.iterdir()):
        if not topic_dir.is_dir() or topic_dir.name == "steelman":
            continue
        for path in sorted(topic_dir.glob("*.yaml")):
            hypothesis = load_yaml(path)
            if hypothesis.get("_parse_error"):
                continue
            hypothesis_id = hypothesis.get("hypothesis_id")
            if not hypothesis_id:
                continue
            hypotheses[hypothesis_id] = hypothesis
    return hypotheses


def primary_axis(axis_index: dict[str, list[dict[str, Any]]], hypothesis_id: str) -> str:
    entries = axis_index.get(hypothesis_id) or []
    if not entries:
        return "unclassified"
    return str(entries[0].get("axis") or "unclassified")


def has_web_public_verdict(hypothesis_id: str, hypotheses: dict[str, dict[str, Any]]) -> bool:
    """Mirror web/lib/content.ts:isHypothesisPubliclyVisible for coverage counts."""
    hypothesis = hypotheses.get(hypothesis_id) or {}
    run_dir = ROOT / "engine" / "runs" / hypothesis_id
    diagnostics_path = run_dir / "diagnostics.json"
    replication_path = run_dir / "replication.py"
    if not diagnostics_path.exists() or not replication_path.exists():
        return False

    try:
        diagnostics = json.loads(
            diagnostics_path.read_text(),
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"non-standard JSON constant: {value}")
            ),
        )
    except Exception:
        return False

    verdict = (diagnostics.get("verdict") or "").lower().strip()
    if not verdict:
        return False
    if verdict.startswith(("inconclusive_data_pending", "blocked", "error", "no verdict")):
        return False

    falsification = hypothesis.get("falsification") or {}
    rule = (falsification.get("rule") or "").lower()
    if STUB_RULE_MARKER not in rule:
        return True

    note_text = f"{hypothesis.get('notes') or ''} {hypothesis.get('methodology_note') or ''}".lower()
    return any(
        marker in note_text
        for marker in ("dispositive", "sharpened", "primary (dispositive")
    )


def audit_coverage(linked_floor: int, tested_floor: int) -> dict[str, Any]:
    hypotheses = build_web_hypothesis_index()
    axis_index = load_axis_index()

    rows: list[dict[str, Any]] = []
    for path in sorted((ROOT / "positions").glob("*.yaml")):
        if path.name.startswith("_"):
            continue

        position = load_yaml(path)
        position_id = position.get("position_id") or path.stem
        school = position.get("school") or position.get("short_name") or position_id
        claims = position.get("falsifiable_specific_claims") or []

        linked_ids: list[str] = []
        missing_ids: set[str] = set()
        for claim in claims:
            hypothesis_id = claim.get("linked_hypothesis_id")
            if not hypothesis_id:
                continue
            if hypothesis_id in hypotheses:
                linked_ids.append(hypothesis_id)
            else:
                missing_ids.add(hypothesis_id)

        unique_linked = set(linked_ids)
        unique_tested = {
            hypothesis_id
            for hypothesis_id in unique_linked
            if has_web_public_verdict(hypothesis_id, hypotheses)
        }
        unique_pending = unique_linked - unique_tested
        pending_axes = Counter(primary_axis(axis_index, hypothesis_id) for hypothesis_id in unique_pending)
        tested_axes = Counter(primary_axis(axis_index, hypothesis_id) for hypothesis_id in unique_tested)

        linked_count = len(unique_linked)
        tested_count = len(unique_tested)
        linked_gap = max(0, linked_floor - linked_count)
        tested_gap = max(0, tested_floor - tested_count)
        status = "balanced_v1" if linked_gap == 0 and tested_gap == 0 else "under_covered"

        rows.append(
            {
                "position_id": position_id,
                "school": school,
                "total_claims": len(claims),
                "unique_hypotheses": linked_count,
                "unique_tested": tested_count,
                "unique_pending": len(unique_pending),
                "missing_hypotheses": sorted(missing_ids),
                "duplicate_claim_links": len(linked_ids) - linked_count,
                "linked_gap_to_floor": linked_gap,
                "tested_gap_to_floor": tested_gap,
                "stretch_linked_gap": max(0, STRETCH_LINKED_FLOOR - linked_count),
                "stretch_tested_gap": max(0, STRETCH_TESTED_FLOOR - tested_count),
                "tested_share": tested_count / linked_count if linked_count else 0.0,
                "status": status,
                "top_pending_axes": pending_axes.most_common(5),
                "top_tested_axes": tested_axes.most_common(5),
            }
        )

    rows.sort(
        key=lambda row: (
            row["status"] != "under_covered",
            -(row["linked_gap_to_floor"] + row["tested_gap_to_floor"]),
            row["unique_tested"],
            row["unique_hypotheses"],
        )
    )

    linked_counts = [row["unique_hypotheses"] for row in rows]
    tested_counts = [row["unique_tested"] for row in rows]
    balanced = [row for row in rows if row["status"] == "balanced_v1"]

    return {
        "generated_at": date.today().isoformat(),
        "methodology": {
            "principle": "Coverage balance measures opportunity set only. It does not alter verdicts, school predictions, polarity, or scores.",
            "v1_floor": {
                "unique_hypotheses": linked_floor,
                "unique_tested": tested_floor,
            },
            "stretch_floor": {
                "unique_hypotheses": STRETCH_LINKED_FLOOR,
                "unique_tested": STRETCH_TESTED_FLOOR,
            },
            "unit": "Unique existing hypothesis IDs linked from each school's falsifiable claims, counted as tested only when the web scorer's public-visibility gate sees a canonical diagnostics.verdict.",
        },
        "summary": {
            "schools": len(rows),
            "balanced_v1": len(balanced),
            "under_covered": len(rows) - len(balanced),
            "linked_range": [min(linked_counts), max(linked_counts)] if linked_counts else [0, 0],
            "tested_range": [min(tested_counts), max(tested_counts)] if tested_counts else [0, 0],
            "total_linked_gap_to_floor": sum(row["linked_gap_to_floor"] for row in rows),
            "total_tested_gap_to_floor": sum(row["tested_gap_to_floor"] for row in rows),
            "total_stretch_linked_gap": sum(row["stretch_linked_gap"] for row in rows),
            "total_stretch_tested_gap": sum(row["stretch_tested_gap"] for row in rows),
        },
        "schools": rows,
    }


def format_axes(items: list[list[Any]] | list[tuple[Any, Any]]) -> str:
    if not items:
        return "-"
    return ", ".join(f"{axis} ({count})" for axis, count in items[:3])


def write_outputs(audit: dict[str, Any], out_base: Path) -> None:
    out_base.parent.mkdir(parents=True, exist_ok=True)
    out_base.with_suffix(".json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")

    summary = audit["summary"]
    floor = audit["methodology"]["v1_floor"]
    stretch = audit["methodology"]["stretch_floor"]
    lines = [
        "# School Coverage Balance Audit",
        "",
        f"Generated: {audit['generated_at']}",
        "",
        "## Methodology Gate",
        "",
        "- Coverage balance measures opportunity set only; it does not change scoreboard verdicts or net scores.",
        "- The unit is unique existing hypothesis IDs linked from a school's falsifiable claims.",
        f"- V1 balanced means at least `{floor['unique_hypotheses']}` unique linked hypotheses and `{floor['unique_tested']}` unique tested hypotheses.",
        f"- Stretch balanced means at least `{stretch['unique_hypotheses']}` unique linked hypotheses and `{stretch['unique_tested']}` unique tested hypotheses.",
        "",
        "## Summary",
        "",
        f"- Schools tracked: {summary['schools']}",
        f"- V1 balanced schools: {summary['balanced_v1']}",
        f"- Under-covered schools: {summary['under_covered']}",
        f"- Unique linked hypothesis range: {summary['linked_range'][0]}-{summary['linked_range'][1]}",
        f"- Unique tested hypothesis range: {summary['tested_range'][0]}-{summary['tested_range'][1]}",
        f"- V1 linked deficit remaining: {summary['total_linked_gap_to_floor']}",
        f"- V1 tested deficit remaining: {summary['total_tested_gap_to_floor']}",
        "",
        "## V1 Coverage Queue",
        "",
        "| school | linked | tested | pending | link gap | run gap | status | top pending axes |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]

    for row in audit["schools"]:
        lines.append(
            f"| `{row['position_id']}` | {row['unique_hypotheses']} | {row['unique_tested']} | "
            f"{row['unique_pending']} | {row['linked_gap_to_floor']} | {row['tested_gap_to_floor']} | "
            f"{row['status']} | {format_axes(row['top_pending_axes'])} |"
        )

    lines += [
        "",
        "## Next Batch Recommendation",
        "",
        "Run existing pending hypotheses first for schools with the largest V1 run gaps. Add new hypotheses only where linked coverage remains below the V1 floor after pending runs are exhausted.",
    ]
    for row in audit["schools"][:10]:
        if row["linked_gap_to_floor"] == 0 and row["tested_gap_to_floor"] == 0:
            continue
        lines.append(
            f"- `{row['position_id']}`: add {row['linked_gap_to_floor']} linked hypotheses and graduate "
            f"{row['tested_gap_to_floor']} tested hypotheses to hit V1."
        )

    out_base.with_suffix(".md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--linked-floor", type=int, default=DEFAULT_LINKED_FLOOR)
    parser.add_argument("--tested-floor", type=int, default=DEFAULT_TESTED_FLOOR)
    parser.add_argument(
        "--out",
        default=str(ROOT / "engine" / "audits" / f"school_coverage_balance_{date.today().isoformat()}"),
    )
    args = parser.parse_args()
    audit = audit_coverage(args.linked_floor, args.tested_floor)
    out_base = Path(args.out)
    write_outputs(audit, out_base)
    print(f"Wrote {out_base.with_suffix('.json')}")
    print(f"Wrote {out_base.with_suffix('.md')}")
    print(json.dumps(audit["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
