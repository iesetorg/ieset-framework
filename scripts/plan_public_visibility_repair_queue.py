#!/usr/bin/env python3
"""Plan repairs for hypothesis runs hidden by the public-visibility gate.

This does not change verdicts or scores. It mirrors the frontend visibility
rules and ranks non-public hypotheses by how much repair work would unlock:
linked school predictions first, then already-run artifacts that likely need
replication-file or diagnostics cleanup.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKIP_TOPIC_DIRS = {"conditional_taxonomy", "steelman", "country_year_ideology"}
STUB_RULE_MARKER = "when this stub is promoted from draft"


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text())
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        return {"_parse_error": str(exc)}


def strict_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
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


def load_hypotheses() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    hyp_root = ROOT / "hypotheses"
    for topic_dir in sorted(hyp_root.iterdir()):
        if not topic_dir.is_dir() or topic_dir.name in SKIP_TOPIC_DIRS:
            continue
        for path in sorted(topic_dir.glob("*.yaml")):
            if path.name.startswith("_"):
                continue
            doc = load_yaml(path)
            hypothesis_id = doc.get("hypothesis_id")
            if hypothesis_id:
                doc["_file"] = str(path.relative_to(ROOT))
                out[hypothesis_id] = doc
    return out


def load_axis_index() -> dict[str, list[dict[str, Any]]]:
    path = ROOT / "hypotheses" / "_axis_index.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text()) or {}
    return data.get("index") or {}


def primary_axis(axis_index: dict[str, list[dict[str, Any]]], hypothesis_id: str) -> str:
    entries = axis_index.get(hypothesis_id) or []
    if not entries:
        return "unclassified"
    return str(entries[0].get("axis") or "unclassified")


def collect_school_links(hypotheses: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    links: dict[str, dict[str, Any]] = {
        hypothesis_id: {"school_ids": set(), "claim_count": 0}
        for hypothesis_id in hypotheses
    }
    for path in sorted((ROOT / "positions").glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        position = load_yaml(path)
        position_id = position.get("position_id") or path.stem
        claims = position.get("falsifiable_specific_claims") or []
        for claim in claims:
            hypothesis_id = claim.get("linked_hypothesis_id")
            if hypothesis_id not in links:
                continue
            links[hypothesis_id]["school_ids"].add(position_id)
            links[hypothesis_id]["claim_count"] += 1

    out: dict[str, dict[str, Any]] = {}
    for hypothesis_id, entry in links.items():
        out[hypothesis_id] = {
            "school_ids": sorted(entry["school_ids"]),
            "school_count": len(entry["school_ids"]),
            "claim_count": entry["claim_count"],
        }
    return out


def visibility_status(hypothesis_id: str, hypothesis: dict[str, Any]) -> dict[str, Any]:
    run_dir = ROOT / "engine" / "runs" / hypothesis_id
    diagnostics_path = run_dir / "diagnostics.json"
    replication_path = run_dir / "replication.py"
    result_card_path = run_dir / "result_card.md"

    diagnostics: dict[str, Any] | None = None
    diagnostics_error: str | None = None
    verdict = ""
    if diagnostics_path.exists():
        diagnostics, diagnostics_error = strict_json(diagnostics_path)
        if diagnostics:
            verdict = str(diagnostics.get("verdict") or "").strip()

    reason = "public_visible"
    if not run_dir.exists():
        reason = "needs_run_dir"
    elif not diagnostics_path.exists():
        reason = "needs_diagnostics"
    elif diagnostics_error:
        reason = "repair_invalid_diagnostics_json"
    elif not verdict:
        reason = "needs_canonical_verdict"
    elif verdict.lower().startswith(("inconclusive", "blocked", "error", "no verdict")):
        reason = "needs_successful_rerun"
    elif not replication_path.exists():
        reason = "needs_replication_py"
    else:
        falsification = hypothesis.get("falsification") or {}
        rule = str(falsification.get("rule") or "").lower()
        if STUB_RULE_MARKER in rule:
            note_text = f"{hypothesis.get('notes') or ''} {hypothesis.get('methodology_note') or ''}".lower()
            if not any(
                marker in note_text
                for marker in ("dispositive", "sharpened", "primary (dispositive")
            ):
                reason = "needs_sharpened_rule"

    return {
        "public_visible": reason == "public_visible",
        "reason": reason,
        "verdict": verdict,
        "verdict_label": (diagnostics or {}).get("verdict_label") if diagnostics else None,
        "template": (diagnostics or {}).get("template") if diagnostics else None,
        "runner": (diagnostics or {}).get("runner") if diagnostics else None,
        "has_run_dir": run_dir.exists(),
        "has_diagnostics": diagnostics_path.exists(),
        "has_replication_py": replication_path.exists(),
        "has_result_card": result_card_path.exists(),
        "diagnostics_error": diagnostics_error,
    }


def repair_effort(reason: str) -> str:
    return {
        "needs_replication_py": "medium",
        "needs_successful_rerun": "high",
        "needs_run_dir": "high",
        "needs_diagnostics": "medium",
        "repair_invalid_diagnostics_json": "low",
        "needs_canonical_verdict": "medium",
        "needs_sharpened_rule": "research",
    }.get(reason, "unknown")


def priority_score(row: dict[str, Any]) -> float:
    score = 0.0
    score += 100.0 if row["school_count"] else 0.0
    score += 12.0 * row["school_count"]
    score += 1.5 * row["claim_count"]
    if row["has_diagnostics"] and row["has_result_card"]:
        score += 20.0
    if row["reason"] == "needs_replication_py":
        score += 15.0
    if row["reason"] == "repair_invalid_diagnostics_json":
        score += 12.0
    if row["reason"] == "needs_successful_rerun":
        score += 5.0
    if row["primary_axis"] == "unclassified":
        score -= 25.0
    return round(score, 3)


def build_plan(limit: int) -> dict[str, Any]:
    hypotheses = load_hypotheses()
    axis_index = load_axis_index()
    school_links = collect_school_links(hypotheses)

    rows: list[dict[str, Any]] = []
    for hypothesis_id, hypothesis in hypotheses.items():
        status = visibility_status(hypothesis_id, hypothesis)
        if status["public_visible"]:
            continue
        links = school_links[hypothesis_id]
        row = {
            "hypothesis_id": hypothesis_id,
            "file": hypothesis.get("_file"),
            "claim": hypothesis.get("claim") or hypothesis.get("title") or hypothesis_id,
            "topic": hypothesis.get("topic") or "uncategorised",
            "evidence_type": hypothesis.get("evidence_type") or "missing",
            "primary_axis": primary_axis(axis_index, hypothesis_id),
            "reason": status["reason"],
            "repair_effort": repair_effort(status["reason"]),
            "school_ids": links["school_ids"],
            "school_count": links["school_count"],
            "claim_count": links["claim_count"],
            "verdict": status["verdict"],
            "verdict_label": status["verdict_label"],
            "template": status["template"],
            "runner": status["runner"],
            "has_run_dir": status["has_run_dir"],
            "has_diagnostics": status["has_diagnostics"],
            "has_replication_py": status["has_replication_py"],
            "has_result_card": status["has_result_card"],
            "diagnostics_error": status["diagnostics_error"],
        }
        row["priority_score"] = priority_score(row)
        rows.append(row)

    rows.sort(
        key=lambda row: (
            row["priority_score"],
            row["school_count"],
            row["has_diagnostics"],
            row["has_result_card"],
            row["hypothesis_id"],
        ),
        reverse=True,
    )

    reason_counts = Counter(row["reason"] for row in rows)
    effort_counts = Counter(row["repair_effort"] for row in rows)
    axis_counts = Counter(row["primary_axis"] for row in rows)
    topic_counts = Counter(row["topic"] for row in rows)
    linked_rows = [row for row in rows if row["school_count"] > 0]

    return {
        "generated_at": date.today().isoformat(),
        "methodology": {
            "principle": "Rank hypotheses hidden by the public-visibility gate without changing verdicts, scores, or links.",
            "visibility_gate": "A public run needs diagnostics.verdict, no blocked/pending/error prefix, a replication.py, and a sharpened non-stub falsification rule or sharpening note.",
            "priority": "School-linked hidden runs rank first; already-run artifacts with diagnostics/result cards rank ahead of from-scratch runs.",
        },
        "summary": {
            "hidden_hypotheses": len(rows),
            "school_linked_hidden_hypotheses": len(linked_rows),
            "school_linked_hidden_claims": sum(row["claim_count"] for row in linked_rows),
            "reason_counts": dict(reason_counts),
            "effort_counts": dict(effort_counts),
            "top_axes": axis_counts.most_common(20),
            "top_topics": topic_counts.most_common(20),
        },
        "queue": rows[:limit],
    }


def format_schools(row: dict[str, Any], max_items: int = 5) -> str:
    schools = row["school_ids"][:max_items]
    suffix = f" +{len(row['school_ids']) - max_items}" if len(row["school_ids"]) > max_items else ""
    return ", ".join(f"`{school}`" for school in schools) + suffix if schools else "-"


def write_outputs(plan: dict[str, Any], out_base: Path) -> None:
    out_base.parent.mkdir(parents=True, exist_ok=True)
    out_base.with_suffix(".json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    out_base.with_suffix(".ids").write_text(
        "\n".join(row["hypothesis_id"] for row in plan["queue"]) + "\n"
    )

    summary = plan["summary"]
    lines = [
        "# Public Visibility Repair Queue",
        "",
        f"Generated: {plan['generated_at']}",
        "",
        "## Methodology Gate",
        "",
        "- This queue does not change verdicts, school links, or scoreboard scores.",
        "- It mirrors the frontend public-visibility gate and ranks hidden hypotheses by likely repair leverage.",
        "- School-linked hidden runs rank first because repairing them can unlock already-registered predictions without inventing new claims.",
        "",
        "## Summary",
        "",
        f"- Hidden hypotheses: {summary['hidden_hypotheses']}",
        f"- School-linked hidden hypotheses: {summary['school_linked_hidden_hypotheses']}",
        f"- School-linked hidden claim rows: {summary['school_linked_hidden_claims']}",
        f"- Reason counts: `{summary['reason_counts']}`",
        f"- Effort counts: `{summary['effort_counts']}`",
        "",
        "## Top Repair Queue",
        "",
        "| priority | hypothesis | reason | effort | axis | topic | schools | artifacts |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in plan["queue"][:100]:
        artifacts = []
        if row["has_diagnostics"]:
            artifacts.append("diagnostics")
        if row["has_result_card"]:
            artifacts.append("result_card")
        if row["has_replication_py"]:
            artifacts.append("replication")
        artifact_text = ", ".join(artifacts) if artifacts else "none"
        lines.append(
            f"| {row['priority_score']:.1f} | `{row['hypothesis_id']}` | {row['reason']} | "
            f"{row['repair_effort']} | `{row['primary_axis']}` | {row['topic']} | "
            f"{format_schools(row)} | {artifact_text} |"
        )

    out_base.with_suffix(".md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument(
        "--out-base",
        type=Path,
        default=ROOT / "engine" / "audits" / f"public_visibility_repair_queue_{date.today().isoformat()}",
    )
    args = parser.parse_args()

    plan = build_plan(args.limit)
    write_outputs(plan, args.out_base)
    print(f"Wrote {args.out_base.with_suffix('.json')}")
    print(f"Wrote {args.out_base.with_suffix('.md')}")
    print(f"Wrote {args.out_base.with_suffix('.ids')}")
    print(json.dumps(plan["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
