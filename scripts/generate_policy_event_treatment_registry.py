#!/usr/bin/env python3
"""Generate a policy event and treatment-definition registry.

Second-order tests need a treatment map before they need clever estimators:
effective dates, treated units, exempt units, comparison markets, and the axes
that define what changed. This script derives the first pass from policy specs
so event-study, DiD, border, and triple-difference upgrades can see what is
already declared and what still needs hand coding.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import yaml

import audit_second_order_measurement as second_order


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "engine" / "policy_event_treatment_registry.json"
OUT_MD = ROOT / "engine" / "policy_event_treatment_registry.md"

FULL_DATE_RE = re.compile(r"\b(18|19|20|21)\d{2}-\d{2}-\d{2}\b")
YEAR_MONTH_RE = re.compile(r"\b(18|19|20|21)\d{2}-\d{2}\b")
YEAR_RE = re.compile(r"\b(18|19|20|21)\d{2}\b")

COMPARATIVE_DESIGNS = {
    "controlled_vs_uncontrolled_units",
    "controlled_vs_uncontrolled_categories",
    "treated_vs_untreated_units",
    "eligible_vs_ineligible_groups",
    "phase_in_or_threshold_comparison",
    "adjacent_market_comparison",
    "border_comparison",
    "triple_difference",
}


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text()) or {}


def iter_policy_specs() -> list[tuple[Path, dict[str, Any]]]:
    paths = sorted(
        path
        for path in (ROOT / "policies").glob("*.yaml")
        if not path.name.startswith("_")
    )
    return [(path, load_yaml(path)) for path in paths]


def date_tokens(values: list[Any]) -> dict[str, list[str]]:
    text = "\n".join(str(value) for value in values if value is not None)
    full_dates = sorted(set(match.group(0) for match in FULL_DATE_RE.finditer(text)))
    year_months = sorted(
        set(match.group(0) for match in YEAR_MONTH_RE.finditer(text))
        - {value[:7] for value in full_dates}
    )
    years = sorted(
        set(match.group(0) for match in YEAR_RE.finditer(text))
        - {value[:4] for value in full_dates}
        - {value[:4] for value in year_months}
    )
    return {
        "full_dates": full_dates,
        "year_months": year_months,
        "years": years,
    }


def timeframe_tokens(timeframe: dict[str, Any]) -> dict[str, list[str]]:
    values = [timeframe.get("start"), timeframe.get("end"), timeframe.get("enacted_date")]
    return date_tokens(values)


def event_date_tokens(design: dict[str, Any]) -> dict[str, list[str]]:
    return date_tokens(design.get("event_dates") or [])


def timing_status(timeframe: dict[str, Any], design: dict[str, Any]) -> str:
    event_tokens = event_date_tokens(design)
    frame_tokens = timeframe_tokens(timeframe)
    if event_tokens["full_dates"]:
        return "event_dated"
    if frame_tokens["full_dates"]:
        return "enacted_date_only"
    if event_tokens["year_months"]:
        return "event_month_dated"
    if frame_tokens["year_months"]:
        return "timeframe_month_dated"
    if timeframe.get("start"):
        return "year_period_only"
    return "missing_timing"


def comparison_structure_status(design: dict[str, Any]) -> str:
    regulated = bool(design.get("regulated_units"))
    comparison = bool(
        design.get("exempt_or_uncontrolled_units")
        or design.get("comparison_markets")
        or design.get("distributional_groups")
    )
    features = set(design.get("design_features") or [])
    comparative = bool(features.intersection(COMPARATIVE_DESIGNS))
    if regulated and comparison and comparative:
        return "declared_treated_comparison_design"
    if regulated and comparison:
        return "declared_treated_and_comparison_units"
    if regulated:
        return "declared_treated_units_only"
    if comparative:
        return "comparative_feature_without_units"
    return "axis_only_no_unit_split"


def readiness_flags(
    *,
    status: str,
    design: dict[str, Any],
    axes: list[str],
    inherited: dict[str, Any],
) -> list[str]:
    comparison_status = comparison_structure_status(design)
    features = set(design.get("design_features") or [])
    has_full_timing = status in {"event_dated", "enacted_date_only"}
    has_any_design = bool(design)
    has_units = comparison_status in {
        "declared_treated_comparison_design",
        "declared_treated_and_comparison_units",
    }

    flags: list[str] = []
    if axes:
        flags.append("axis_coded_treatment")
    if has_full_timing:
        flags.append("ready_for_event_study_timing")
    else:
        flags.append("needs_exact_event_dates")
    if has_units:
        flags.append("ready_for_controlled_comparison_structure")
    elif has_any_design:
        flags.append("needs_comparison_unit_detail")
    else:
        flags.append("needs_treated_and_comparison_unit_coding")
    if "triple_difference" in features and has_full_timing and has_units:
        flags.append("ready_for_triple_difference_structure")
    elif "triple_difference" in (inherited.get("preferred_designs") or []):
        flags.append("candidate_for_triple_difference_after_unit_coding")
    if inherited.get("has_axis_requirements"):
        flags.append("has_axis_inherited_second_order_requirements")
    if design.get("known_data_gaps"):
        flags.append("known_microdata_gaps_declared")
    if has_full_timing and has_units:
        flags.append("ready_for_comparative_event_design")
    return flags


def measurement_blockers(flags: list[str]) -> list[str]:
    blockers: list[str] = []
    if "needs_exact_event_dates" in flags:
        blockers.append("needs_exact_event_dates")
    if "needs_treated_and_comparison_unit_coding" in flags:
        blockers.append("needs_treated_and_comparison_unit_coding")
    if "needs_comparison_unit_detail" in flags:
        blockers.append("needs_comparison_unit_detail")
    if "known_microdata_gaps_declared" in flags:
        blockers.append("known_microdata_gaps_declared")
    return blockers


def source_family_details(
    family_ids: list[str],
    families: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family_id in family_ids:
        rec = families.get(family_id) or {}
        rows.append(
            {
                "family_id": family_id,
                "name": rec.get("name"),
                "readiness": rec.get("readiness"),
                "priority": rec.get("priority"),
                "existing_fetchers": rec.get("existing_fetchers") or [],
                "publisher_refs": rec.get("publisher_refs") or [],
            }
        )
    return rows


def compact_policy_row(
    path: Path,
    doc: dict[str, Any],
    axis_index: dict[str, dict[str, Any]],
    families: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    timeframe = doc.get("timeframe") or {}
    design = doc.get("evaluation_design") or {}
    axes_moved = doc.get("axes_moved") or []
    axes = sorted(
        str(axis.get("axis"))
        for axis in axes_moved
        if isinstance(axis, dict) and axis.get("axis")
    )
    inherited = second_order.inherited_axis_requirements(axes, axis_index, families)
    timing = timing_status(timeframe, design)
    flags = readiness_flags(
        status=timing,
        design=design,
        axes=axes,
        inherited=inherited,
    )
    blockers = measurement_blockers(flags)

    return {
        "policy_id": doc.get("policy_id"),
        "path": str(path.relative_to(ROOT)),
        "status": doc.get("status"),
        "title": doc.get("title"),
        "countries": doc.get("countries") or [],
        "scope": doc.get("scope") or "national",
        "timeframe": {
            "start": timeframe.get("start"),
            "end": timeframe.get("end"),
            "enacted_date": timeframe.get("enacted_date"),
        },
        "timeframe_date_tokens": timeframe_tokens(timeframe),
        "event_date_tokens": event_date_tokens(design),
        "timing_status": timing,
        "axes": axes,
        "axis_movements": [
            {
                "axis": axis.get("axis"),
                "direction": axis.get("direction"),
                "magnitude": axis.get("magnitude"),
                "intended": axis.get("intended"),
            }
            for axis in axes_moved
            if isinstance(axis, dict)
        ],
        "control_focus": second_order.is_price_or_rent_control(doc),
        "linked_hypotheses": doc.get("linked_hypotheses") or [],
        "linked_hypotheses_inferred": doc.get("linked_hypotheses_inferred") or [],
        "has_evaluation_design": bool(design),
        "design_features": design.get("design_features") or [],
        "comparison_structure_status": comparison_structure_status(design),
        "regulated_units": design.get("regulated_units") or [],
        "exempt_or_uncontrolled_units": design.get("exempt_or_uncontrolled_units") or [],
        "comparison_markets": design.get("comparison_markets") or [],
        "second_order_outcomes": design.get("second_order_outcomes") or [],
        "distributional_groups": design.get("distributional_groups") or [],
        "known_data_gaps": design.get("known_data_gaps") or [],
        "required_layers": inherited.get("required_layers") or [],
        "preferred_designs": inherited.get("preferred_designs") or [],
        "canonical_outcomes": inherited.get("canonical_outcomes") or [],
        "source_readiness_counts": inherited.get("source_readiness_counts") or {},
        "source_families": source_family_details(inherited.get("source_families") or [], families),
        "readiness_flags": flags,
        "measurement_blockers": blockers,
        "registry_readiness": "partial_design_ready" if not blockers else "needs_coding_or_data",
    }


def build_registry() -> dict[str, Any]:
    axis_index = second_order.load_axis_second_order_index()
    families = second_order.load_second_order_source_families()
    rows = [
        compact_policy_row(path, doc, axis_index, families)
        for path, doc in iter_policy_specs()
    ]
    rows.sort(
        key=lambda row: (
            row["registry_readiness"] != "partial_design_ready",
            not row["has_evaluation_design"],
            not row["control_focus"],
            row["status"] != "canonical",
            row["status"] != "candidate",
            row["policy_id"] or "",
        )
    )

    timing_counts = Counter(row["timing_status"] for row in rows)
    comparison_counts = Counter(row["comparison_structure_status"] for row in rows)
    blocker_counts = Counter()
    readiness_counts = Counter()
    design_feature_counts = Counter()
    source_readiness_counts = Counter()
    source_family_counts = Counter()
    for row in rows:
        blocker_counts.update(row["measurement_blockers"])
        readiness_counts.update(row["readiness_flags"])
        design_feature_counts.update(row["design_features"])
        source_readiness_counts.update(row["source_readiness_counts"])
        source_family_counts.update(family["family_id"] for family in row["source_families"])

    return {
        "generated_by": "scripts/generate_policy_event_treatment_registry.py",
        "generated_at": date.today().isoformat(),
        "summary": {
            "policy_count": len(rows),
            "policies_with_evaluation_design": sum(1 for row in rows if row["has_evaluation_design"]),
            "policies_with_full_event_timing": sum(
                1
                for row in rows
                if row["timing_status"] in {"event_dated", "enacted_date_only"}
            ),
            "policies_ready_for_comparative_event_design": sum(
                1 for row in rows if "ready_for_comparative_event_design" in row["readiness_flags"]
            ),
            "policies_ready_for_triple_difference_structure": sum(
                1 for row in rows if "ready_for_triple_difference_structure" in row["readiness_flags"]
            ),
            "policies_needing_exact_event_dates": blocker_counts.get("needs_exact_event_dates", 0),
            "timing_status_counts": dict(timing_counts),
            "comparison_structure_status_counts": dict(comparison_counts),
            "readiness_flag_counts": dict(readiness_counts),
            "measurement_blocker_counts": dict(blocker_counts),
            "design_feature_counts": dict(design_feature_counts),
            "axis_source_readiness_counts": dict(source_readiness_counts),
            "axis_source_family_counts_top": source_family_counts.most_common(25),
        },
        "policies": rows,
    }


def write_outputs(payload: dict[str, Any]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    summary = payload["summary"]
    lines = [
        "# Policy Event and Treatment Registry",
        "",
        "This generated registry turns policy YAMLs into a treatment map for second-order testing: timing, treated units, exemptions, comparison markets, design features, and unresolved blockers.",
        "",
        "## Summary",
        "",
        f"- Policies indexed: {summary['policy_count']}",
        f"- Policies with explicit evaluation_design: {summary['policies_with_evaluation_design']}",
        f"- Policies with exact event or enacted dates: {summary['policies_with_full_event_timing']}",
        f"- Policies ready for comparative event design: {summary['policies_ready_for_comparative_event_design']}",
        f"- Policies ready for triple-difference structure: {summary['policies_ready_for_triple_difference_structure']}",
        f"- Timing status counts: `{json.dumps(summary['timing_status_counts'], sort_keys=True)}`",
        f"- Comparison structure counts: `{json.dumps(summary['comparison_structure_status_counts'], sort_keys=True)}`",
        f"- Measurement blockers: `{json.dumps(summary['measurement_blocker_counts'], sort_keys=True)}`",
        f"- Axis source readiness: `{json.dumps(summary['axis_source_readiness_counts'], sort_keys=True)}`",
        "",
        "## Ready Design Seeds",
        "",
        "| policy | status | timing | comparison structure | designs | blockers |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    ready_rows = [
        row
        for row in payload["policies"]
        if "ready_for_comparative_event_design" in row["readiness_flags"]
    ]
    for row in ready_rows[:100]:
        designs = ", ".join(row["design_features"][:5])
        if len(row["design_features"]) > 5:
            designs += ", ..."
        blockers = ", ".join(row["measurement_blockers"]) or "none"
        lines.append(
            f"| `{row['policy_id']}` | {row['status']} | {row['timing_status']} | "
            f"{row['comparison_structure_status']} | {designs} | {blockers} |"
        )

    lines.extend(
        [
            "",
            "## Treatment Coding Queue",
            "",
            "| policy | status | axes | timing | blockers |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    queue = [
        row
        for row in payload["policies"]
        if row["measurement_blockers"]
    ]
    queue.sort(
        key=lambda row: (
            "needs_treated_and_comparison_unit_coding" not in row["measurement_blockers"],
            "needs_exact_event_dates" not in row["measurement_blockers"],
            not row["control_focus"],
            row["policy_id"] or "",
        )
    )
    for row in queue[:200]:
        axes = ", ".join(row["axes"][:4])
        if len(row["axes"]) > 4:
            axes += ", ..."
        blockers = ", ".join(row["measurement_blockers"])
        lines.append(
            f"| `{row['policy_id']}` | {row['status']} | {axes} | {row['timing_status']} | {blockers} |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n")


def main() -> int:
    payload = build_registry()
    write_outputs(payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
