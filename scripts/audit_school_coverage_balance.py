#!/usr/bin/env python3
"""Audit linked, public, school-scored and directional school coverage.

The evidence-tier ledger controls public visibility. A run directory with a
verdict is not itself a tested scoreboard claim. This audit reads the live
ledger and the same verdict/prediction rules as the scoreboard outcome audit;
it never changes a prediction, verdict, link or score.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from audit_scoreboard_outcomes import (
    hypothesis_public_verdict,
    live_evidence_index,
    load_yaml,
    position_outcome,
    verdict_class,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LINKED_FLOOR = 100
DEFAULT_TESTED_FLOOR = 60
STRETCH_LINKED_FLOOR = 125
STRETCH_TESTED_FLOOR = 80
DIRECTIONAL_TARGET = 200
STUB_RULE_MARKER = "when this stub is promoted from draft"
DIRECTIONAL_OUTCOMES = {
    "supports_position", "refutes_position", "partial_supports", "partial_refutes"
}


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
    """Legacy raw-run helper used by older planners, not this school audit.

    It predates the evidence-tier gate and must never be used to describe a
    scoreboard-tested claim. Keep its API for existing planner imports.
    """
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
    except (OSError, ValueError):
        return False
    verdict = (diagnostics.get("verdict") or "").lower().strip()
    if not verdict or verdict.startswith(("inconclusive", "blocked", "error", "no verdict")):
        return False
    falsification = hypothesis.get("falsification") or {}
    rule = (falsification.get("rule") or "").lower()
    if STUB_RULE_MARKER not in rule:
        return True
    note_text = f"{hypothesis.get('notes') or ''} {hypothesis.get('methodology_note') or ''}".lower()
    return any(marker in note_text for marker in ("dispositive", "sharpened", "primary (dispositive"))


def audit_coverage(
    linked_floor: int,
    tested_floor: int,
    *,
    directional_target: int = DIRECTIONAL_TARGET,
    evidence_index: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    hypotheses = build_web_hypothesis_index()
    axis_index = load_axis_index()
    # Rebuild the authoritative ledger from current source and Git history.
    # The generated JSON can be stale after even a single evidence repair.
    if evidence_index is None:
        evidence_index = live_evidence_index()
    coverage_index: dict[tuple[str, int], dict[str, Any]] = {}
    for hypothesis in hypotheses.values():
        for coverage in hypothesis.get("covers_claims") or []:
            try:
                key = (coverage["position_id"], int(coverage["claim_index"]))
            except (KeyError, TypeError, ValueError):
                continue
            coverage_index[key] = coverage
    verdict_cache: dict[str, tuple[bool, str | None]] = {}

    rows: list[dict[str, Any]] = []
    benchmark_controls: list[dict[str, Any]] = []
    directional_queue: dict[str, list[dict[str, Any]]] = {}
    for path in sorted((ROOT / "positions").glob("*.yaml")):
        if path.name.startswith("_"):
            continue

        position = load_yaml(path)
        position_id = position.get("position_id") or path.stem
        school = position.get("school") or position.get("short_name") or position_id
        role = position.get("scoreboard_role") or "school"
        claims = position.get("falsifiable_specific_claims") or []

        linked_ids: list[str] = []
        missing_ids: set[str] = set()
        public_ids: set[str] = set()
        eligible_ids: set[str] = set()
        tested_ids: set[str] = set()
        neutral_ids: set[str] = set()
        directional_linked: set[str] = set()
        directional_scored: set[str] = set()
        scoreboard_tested_claims = 0
        scoreboard_directional_claims = 0
        public_score_holds: set[str] = set()
        blockers_by_hypothesis: dict[str, set[str]] = defaultdict(set)
        queue_by_hypothesis: dict[str, dict[str, Any]] = {}

        for claim_index, claim in enumerate(claims):
            hypothesis_id = claim.get("linked_hypothesis_id")
            if not hypothesis_id:
                continue
            if hypothesis_id not in hypotheses:
                missing_ids.add(hypothesis_id)
                continue
            linked_ids.append(hypothesis_id)
            if hypothesis_id not in verdict_cache:
                verdict_cache[hypothesis_id] = hypothesis_public_verdict(
                    hypothesis_id, hypotheses, evidence_index
                )
            is_public, verdict = verdict_cache[hypothesis_id]
            evidence = evidence_index.get(hypothesis_id) or {}
            is_eligible = is_public and evidence.get("school_score_eligible") is not False
            coverage = coverage_index.get((position_id, claim_index)) or {}
            prediction = coverage.get("school_prediction") or claim.get("school_prediction")
            polarity = coverage.get("polarity") or claim.get("claim_polarity") or "aligned"
            outcome = (
                position_outcome(verdict_class(verdict), prediction, polarity)
                if is_eligible else "untested"
            )
            if is_public:
                public_ids.add(hypothesis_id)
            if is_eligible:
                eligible_ids.add(hypothesis_id)
            elif is_public:
                public_score_holds.add(hypothesis_id)
            if outcome != "untested":
                tested_ids.add(hypothesis_id)
                scoreboard_tested_claims += 1
            if outcome == "partial":
                neutral_ids.add(hypothesis_id)
            if prediction not in {"supported", "falsified"}:
                continue
            directional_linked.add(hypothesis_id)
            if outcome in DIRECTIONAL_OUTCOMES:
                directional_scored.add(hypothesis_id)
                scoreboard_directional_claims += 1
                continue
            if not is_public:
                reasons = evidence.get("exclusion_reasons") or ["not_public_unspecified"]
            elif not is_eligible:
                reasons = ["school_score_eligible_false"]
            else:
                reasons = ["neutral_result"]
            blockers_by_hypothesis[hypothesis_id].update(reasons)
            queue_by_hypothesis[hypothesis_id] = {
                "hypothesis_id": hypothesis_id,
                "claim_index": claim_index,
                "prediction": prediction,
                "outcome": outcome,
                "evidence_tier": evidence.get("tier") or "unrecorded",
                "registration_status": evidence.get("registration_status") or "unrecorded",
                "axis": primary_axis(axis_index, hypothesis_id),
            }

        unique_linked = set(linked_ids)
        unique_pending = unique_linked - tested_ids
        pending_axes = Counter(primary_axis(axis_index, hypothesis_id) for hypothesis_id in unique_pending)
        tested_axes = Counter(primary_axis(axis_index, hypothesis_id) for hypothesis_id in tested_ids)
        archive_ids = {hypothesis_id for hypothesis_id in unique_linked if
                       (evidence_index.get(hypothesis_id) or {}).get("tier") == "archive"}
        archive_reasons = Counter(
            reason for hypothesis_id in archive_ids
            for reason in (evidence_index[hypothesis_id].get("exclusion_reasons") or [])
        )
        blocker_counts = Counter(
            reason for reasons in blockers_by_hypothesis.values() for reason in reasons
        )
        for hypothesis_id, item in queue_by_hypothesis.items():
            item["blockers"] = sorted(blockers_by_hypothesis[hypothesis_id])
        if role != "benchmark_control":
            directional_queue[position_id] = sorted(
                queue_by_hypothesis.values(),
                key=lambda item: (
                    item["registration_status"] != "verified",
                    len(item["blockers"]),
                    item["hypothesis_id"],
                ),
            )

        linked_count = len(unique_linked)
        tested_count = len(tested_ids)
        linked_gap = max(0, linked_floor - linked_count)
        tested_gap = max(0, tested_floor - tested_count)
        status = "balanced_v1" if linked_gap == 0 and tested_gap == 0 else "under_covered"

        row = {
                "position_id": position_id,
                "school": school,
                "scoreboard_role": role,
                "total_claims": len(claims),
                "unique_hypotheses": linked_count,
                "unique_public": len(public_ids),
                "unique_school_score_eligible": len(eligible_ids),
                "unique_tested": tested_count,
                "unique_pending": len(unique_pending),
                "unique_neutral_tested": len(neutral_ids),
                "unique_directional_linked": len(directional_linked),
                "unique_directional_scored": len(directional_scored),
                "scoreboard_tested_claims": scoreboard_tested_claims,
                "scoreboard_directional_scored_claims": scoreboard_directional_claims,
                "directional_gap_to_target": max(0, directional_target - len(directional_scored)),
                "minimum_new_directional_claims_for_target": max(0, directional_target - len(directional_linked)),
                "unique_archived": len(archive_ids),
                "public_school_score_holds": len(public_score_holds),
                "archive_exclusion_reasons": dict(sorted(archive_reasons.items())),
                "directional_blockers": dict(sorted(blocker_counts.items())),
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
        if role == "benchmark_control":
            benchmark_controls.append(row)
        else:
            rows.append(row)

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
    directional_counts = [row["unique_directional_scored"] for row in rows]
    balanced = [row for row in rows if row["status"] == "balanced_v1"]

    return {
        "generated_at": date.today().isoformat(),
        "methodology": {
            "principle": "Coverage measures existing opportunity and eligible evidence without altering verdicts, predictions, polarity, links or scores.",
            "v1_floor": {
                "unique_hypotheses": linked_floor,
                "unique_tested": tested_floor,
            },
            "stretch_floor": {
                "unique_hypotheses": STRETCH_LINKED_FLOOR,
                "unique_tested": STRETCH_TESTED_FLOOR,
            },
            "directional_target": directional_target,
            "unit": "Coverage counts unique existing hypothesis IDs per ranked school; separate scoreboard claim-row counts retain duplicate links. Tested requires current evidence-ledger public visibility, school-score eligibility and a scored verdict. Directional requires a non-neutral scored outcome.",
            "blocker_count_rule": "Reasons can overlap within an archived hypothesis; counts are not additive. Legacy same-commit runs require genuinely prospective new tests, not relabeling.",
        },
        "summary": {
            "schools": len(rows),
            "benchmark_controls": len(benchmark_controls),
            "balanced_v1": len(balanced),
            "under_covered": len(rows) - len(balanced),
            "linked_range": [min(linked_counts), max(linked_counts)] if linked_counts else [0, 0],
            "tested_range": [min(tested_counts), max(tested_counts)] if tested_counts else [0, 0],
            "directional_scored_range": [min(directional_counts), max(directional_counts)] if directional_counts else [0, 0],
            "total_directional_gap_to_target": sum(row["directional_gap_to_target"] for row in rows),
            "minimum_new_directional_claims_for_target": sum(row["minimum_new_directional_claims_for_target"] for row in rows),
            "total_linked_gap_to_floor": sum(row["linked_gap_to_floor"] for row in rows),
            "total_tested_gap_to_floor": sum(row["tested_gap_to_floor"] for row in rows),
            "total_stretch_linked_gap": sum(row["stretch_linked_gap"] for row in rows),
            "total_stretch_tested_gap": sum(row["stretch_tested_gap"] for row in rows),
        },
        "schools": rows,
        "benchmark_controls": benchmark_controls,
        "directional_queue": directional_queue,
    }


def format_axes(items: list[list[Any]] | list[tuple[Any, Any]]) -> str:
    if not items:
        return "-"
    return ", ".join(f"{axis} ({count})" for axis, count in items[:3])


def format_counts(counts: dict[str, int], limit: int = 3) -> str:
    if not counts:
        return "-"
    return ", ".join(
        f"{reason} ({count})"
        for reason, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    )


def write_outputs(audit: dict[str, Any], out_base: Path) -> None:
    out_base.parent.mkdir(parents=True, exist_ok=True)
    summary_payload = {key: value for key, value in audit.items() if key != "directional_queue"}
    out_base.with_suffix(".json").write_text(
        json.dumps(summary_payload, indent=2, sort_keys=True) + "\n"
    )
    with out_base.with_suffix(".csv").open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow((
            "position_id", "hypothesis_id", "claim_index", "prediction",
            "outcome", "evidence_tier", "registration_status", "axis", "blockers",
        ))
        for row in audit["schools"]:
            position_id = row["position_id"]
            for candidate in audit["directional_queue"][position_id]:
                writer.writerow((
                    position_id,
                    candidate["hypothesis_id"],
                    candidate["claim_index"],
                    candidate["prediction"],
                    candidate["outcome"],
                    candidate["evidence_tier"],
                    candidate["registration_status"],
                    candidate["axis"],
                    ";".join(candidate["blockers"]),
                ))

    summary = audit["summary"]
    floor = audit["methodology"]["v1_floor"]
    stretch = audit["methodology"]["stretch_floor"]
    if (
        floor["unique_hypotheses"] == DEFAULT_LINKED_FLOOR
        and floor["unique_tested"] == DEFAULT_TESTED_FLOOR
    ):
        floor_label = "V1"
        balanced_status_label = "balanced_v1"
    elif (
        floor["unique_hypotheses"] == STRETCH_LINKED_FLOOR
        and floor["unique_tested"] == STRETCH_TESTED_FLOOR
    ):
        floor_label = "Stretch"
        balanced_status_label = "balanced_stretch"
    else:
        floor_label = "Selected"
        balanced_status_label = "balanced_selected"
    method_lines = [
        "# School Coverage Balance Audit",
        "",
        f"Generated: {audit['generated_at']}",
        "",
        "## Methodology Gate",
        "",
        "- This is a coverage and repair queue, not a school ranking or a change to verdicts and scores.",
        "- The unit is unique existing hypothesis IDs linked from a school's falsifiable claims.",
        "- The scoreboard itself counts prediction rows. Its claim-row totals are also reported so duplicate links do not create a false audit mismatch.",
        "- A tested link must pass the current evidence-tier public gate and school-score gate and have a scored verdict. A visible run file alone does not qualify.",
        "- A directional scored link has a school forecast and a non-neutral support, refutation or directional partial outcome; a `mixed` forecast and neutral partial do not qualify.",
        "- Archived runs whose spec and result first appeared in one commit cannot become preregistered by relabeling; they require a genuinely prospective test.",
        f"- {floor_label} balanced means at least `{floor['unique_hypotheses']}` unique linked hypotheses and `{floor['unique_tested']}` score-eligible tested hypotheses.",
    ]
    if floor_label != "Stretch":
        method_lines.append(
            f"- Stretch balanced means at least `{stretch['unique_hypotheses']}` unique linked hypotheses and `{stretch['unique_tested']}` unique tested hypotheses."
        )
    lines = method_lines + [
        "",
        "## Summary",
        "",
        f"- Ranked schools tracked: {summary['schools']} (benchmark controls excluded: {summary['benchmark_controls']})",
        f"- {floor_label} balanced schools: {summary['balanced_v1']}",
        f"- Under-covered schools: {summary['under_covered']}",
        f"- Unique linked hypothesis range: {summary['linked_range'][0]}-{summary['linked_range'][1]}",
        f"- Unique score-eligible tested hypothesis range: {summary['tested_range'][0]}-{summary['tested_range'][1]}",
        f"- Unique directional scored hypothesis range: {summary['directional_scored_range'][0]}-{summary['directional_scored_range'][1]}",
        f"- Total gap to {audit['methodology']['directional_target']} directional scored links per school: {summary['total_directional_gap_to_target']}",
        f"- Theoretical minimum new directional claims even if every existing directional link passes: {summary['minimum_new_directional_claims_for_target']}",
        f"- {floor_label} linked deficit remaining: {summary['total_linked_gap_to_floor']}",
        f"- {floor_label} tested deficit remaining: {summary['total_tested_gap_to_floor']}",
        "",
        f"## {floor_label} Coverage Queue",
        "",
        "| school | linked IDs | public IDs | eligible IDs | tested IDs | scoreboard tested claims | directional scored IDs | pending IDs | link gap | test gap | status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]

    for row in audit["schools"]:
        display_status = (
            balanced_status_label if row["status"] == "balanced_v1" else row["status"]
        )
        lines.append(
            f"| `{row['position_id']}` | {row['unique_hypotheses']} | {row['unique_public']} | "
            f"{row['unique_school_score_eligible']} | {row['unique_tested']} | "
            f"{row['scoreboard_tested_claims']} | {row['unique_directional_scored']} | "
            f"{row['unique_pending']} | "
            f"{row['linked_gap_to_floor']} | {row['tested_gap_to_floor']} | {display_status} |"
        )

    lines += [
        "",
        f"## Path to {audit['methodology']['directional_target']} Directional Scored Tests per School",
        "",
        "The gap is a forecast-score coverage target. It is not strict attribution-aware school credit; second-order measurement gates remain separate.",
        "Blocker counts overlap when an archived result fails more than one gate. The full hypothesis-by-hypothesis queue and exact reasons are in the paired CSV.",
        "",
        "| school | directional linked | scored | gap to 200 | minimum new directional claims | archived links | top blockers |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in audit["schools"]:
        lines.append(
            f"| `{row['position_id']}` | {row['unique_directional_linked']} | "
            f"{row['unique_directional_scored']} | {row['directional_gap_to_target']} | "
            f"{row['minimum_new_directional_claims_for_target']} | {row['unique_archived']} | "
            f"{format_counts(row['directional_blockers'])} |"
        )
    lines += [
        "",
        "## First Existing Candidates by School",
        "",
        "This is a triage order, not permission to reclassify results. A verified preregistration with another blocker appears first; older same-commit studies require new frozen specifications and genuinely new data or holdouts.",
        "",
    ]
    for row in audit["schools"]:
        school_id = row["position_id"]
        lines.append(f"### `{school_id}`")
        lines.append("")
        candidates = audit["directional_queue"][school_id][:8]
        if not candidates:
            lines.append("No existing directional candidate remains.")
        else:
            for candidate in candidates:
                reasons = ", ".join(candidate["blockers"])
                lines.append(
                    f"- `{candidate['hypothesis_id']}` ({candidate['axis']}): {reasons}."
                )
        lines.append("")
    lines += [
        "## Research Sequence",
        "",
        "1. Audit each school-specific forecast, mechanism and polarity against the original claim before a test is designed. Keep `mixed` forecasts neutral unless a new precommitted claim is authored.",
        "2. Repair verified, genuinely runnable archival candidates only when the recorded data and estimator support the claim. Preserve failed and inconclusive results.",
        "3. For legacy same-commit studies, freeze a new specification before a genuinely new source vintage or holdout test. Keep the older result archived.",
        "4. Add new school-distinctive directional hypotheses where existing directional capacity is below target. Require an explicit falsifier, data source, scope, comparator and multiple-testing family.",
        "5. Rebuild the evidence ledger, school audit and scoreboard, then verify strict second-order gates independently before making a school-level inference.",
    ]

    out_base.with_suffix(".md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--linked-floor", type=int, default=DEFAULT_LINKED_FLOOR)
    parser.add_argument("--tested-floor", type=int, default=DEFAULT_TESTED_FLOOR)
    parser.add_argument("--directional-target", type=int, default=DIRECTIONAL_TARGET)
    parser.add_argument(
        "--out",
        default=str(ROOT / "engine" / "audits" / f"school_coverage_balance_{date.today().isoformat()}"),
    )
    args = parser.parse_args()
    audit = audit_coverage(
        args.linked_floor, args.tested_floor,
        directional_target=args.directional_target,
    )
    out_base = Path(args.out)
    write_outputs(audit, out_base)
    print(f"Wrote {out_base.with_suffix('.json')}")
    print(f"Wrote {out_base.with_suffix('.md')}")
    print(f"Wrote {out_base.with_suffix('.csv')}")
    print(json.dumps(audit["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
