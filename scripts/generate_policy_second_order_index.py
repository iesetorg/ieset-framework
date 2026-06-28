#!/usr/bin/env python3
"""Build a policy-level second-order measurement requirements index.

This is the consumable companion to audit_second_order_measurement.py. The audit
answers "where are the gaps?"; this index gives policy browsers, run planners,
and data agents a stable lookup table:

* which second-order layers each policy inherits from its axes,
* whether it has an explicit policy evaluation_design,
* which source families and fetchers are needed, and
* which movements inherit unresolved second-order design work.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import audit_second_order_measurement as audit


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "engine" / "policy_second_order_requirements_index.json"
OUT_MD = ROOT / "engine" / "policy_second_order_requirements_index.md"


def source_family_details(
    family_ids: list[str],
    families: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for family_id in family_ids:
        rec = families.get(family_id) or {}
        out.append(
            {
                "family_id": family_id,
                "name": rec.get("name"),
                "readiness": rec.get("readiness"),
                "priority": rec.get("priority"),
                "publisher_refs": rec.get("publisher_refs") or [],
                "existing_fetchers": rec.get("existing_fetchers") or [],
            }
        )
    return out


def compact_policy_row(
    row: dict[str, Any],
    families: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    inherited = row.get("axis_inherited_requirements") or {}
    source_family_ids = inherited.get("source_families") or []
    return {
        "policy_id": row.get("id"),
        "path": row.get("path"),
        "status": row.get("status"),
        "control_focus": bool(row.get("control_focus")),
        "axes": row.get("axes") or [],
        "has_evaluation_design": bool(row.get("has_evaluation_design")),
        "evaluation_design_status": row.get("evaluation_design_status"),
        "explicit_design_features": row.get("design_features") or [],
        "explicit_known_data_gaps": row.get("known_data_gaps") or [],
        "required_layers": inherited.get("required_layers") or [],
        "preferred_designs": inherited.get("preferred_designs") or [],
        "canonical_outcomes": inherited.get("canonical_outcomes") or [],
        "source_readiness_counts": inherited.get("source_readiness_counts") or {},
        "source_families": source_family_details(source_family_ids, families),
    }


def compact_movement_row(
    row: dict[str, Any],
    families: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    inherited = row.get("axis_inherited_requirements") or {}
    source_family_ids = inherited.get("source_families") or []
    return {
        "movement_id": row.get("id"),
        "path": row.get("path"),
        "status": row.get("status"),
        "control_focus": bool(row.get("control_focus")),
        "axes": row.get("axes") or [],
        "policies_in_audit": row.get("policies_in_audit") or [],
        "policies_with_design": row.get("policies_with_design") or [],
        "policies_with_axis_requirements": row.get("policies_with_axis_requirements") or [],
        "required_layers": inherited.get("required_layers") or [],
        "preferred_designs": inherited.get("preferred_designs") or [],
        "source_readiness_counts": inherited.get("source_readiness_counts") or {},
        "source_families": source_family_details(source_family_ids, families),
    }


def build_index(scope: str = "all") -> dict[str, Any]:
    axis_index = audit.load_axis_second_order_index()
    families = audit.load_second_order_source_families()
    policies = audit.audit_policies(scope, axis_index=axis_index, families=families)
    movements = audit.audit_movements(policies, scope, axis_index=axis_index, families=families)
    policy_axis = audit.aggregate_policy_axis_requirements(policies)

    source_counts: Counter[str] = Counter()
    for row in policies:
        inherited = row.get("axis_inherited_requirements") or {}
        source_counts.update(inherited.get("source_readiness_counts") or {})

    policy_rows = [compact_policy_row(row, families) for row in policies]
    movement_rows = [compact_movement_row(row, families) for row in movements]
    missing_design = [
        row
        for row in policy_rows
        if row["evaluation_design_status"] == "axis_inherited_missing_explicit_design"
    ]
    missing_design.sort(
        key=lambda row: (
            not row["control_focus"],
            row["status"] != "canonical",
            row["status"] != "candidate",
            -len(row["required_layers"]),
            row["policy_id"] or "",
        )
    )

    return {
        "generated_by": "scripts/generate_policy_second_order_index.py",
        "scope": scope,
        "summary": {
            "policy_count": len(policy_rows),
            "movement_count": len(movement_rows),
            "policies_with_axis_requirements": policy_axis["policies_with_axis_requirements"],
            "policies_with_explicit_evaluation_design": sum(1 for row in policy_rows if row["has_evaluation_design"]),
            "policies_missing_explicit_design_but_axis_requirements": policy_axis[
                "policies_missing_explicit_design_but_axis_requirements"
            ],
            "evaluation_design_status_counts": policy_axis["evaluation_design_status_counts"],
            "source_readiness_policy_mentions": policy_axis["source_readiness_policy_mentions"],
            "required_layer_policy_mentions": policy_axis["required_layer_policy_mentions"],
        },
        "policy_design_queue": missing_design,
        "policies": policy_rows,
        "movements": movement_rows,
    }


def write_outputs(payload: dict[str, Any]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    summary = payload["summary"]
    lines = [
        "# Policy Second-order Requirements Index",
        "",
        "This generated index expands each policy's axis coding into second-order measurement requirements.",
        "",
        "## Summary",
        "",
        f"- Policies indexed: {summary['policy_count']}",
        f"- Movements indexed: {summary['movement_count']}",
        f"- Policies with axis-inherited requirements: {summary['policies_with_axis_requirements']}",
        f"- Policies with explicit evaluation_design: {summary['policies_with_explicit_evaluation_design']}",
        f"- Policies missing explicit design despite axis requirements: {summary['policies_missing_explicit_design_but_axis_requirements']}",
        f"- Evaluation-design status counts: `{json.dumps(summary['evaluation_design_status_counts'], sort_keys=True)}`",
        f"- Source readiness mentions: `{json.dumps(summary['source_readiness_policy_mentions'], sort_keys=True)}`",
        "",
        "## Most Common Required Layers",
        "",
    ]
    for layer, count in sorted(
        summary["required_layer_policy_mentions"].items(),
        key=lambda item: (-item[1], item[0]),
    )[:20]:
        lines.append(f"- `{layer}` ({count})")

    lines.extend(
        [
            "",
            "## Explicit Design Backlog",
            "",
            "| policy | status | axes | required layers | source readiness |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["policy_design_queue"][:200]:
        axes = ", ".join(row["axes"][:4])
        if len(row["axes"]) > 4:
            axes += ", ..."
        layers = ", ".join(row["required_layers"][:5])
        if len(row["required_layers"]) > 5:
            layers += ", ..."
        readiness = json.dumps(row["source_readiness_counts"], sort_keys=True)
        lines.append(
            f"| `{row['policy_id']}` | {row['status']} | {axes} | {layers} | `{readiness}` |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n")


def main() -> int:
    payload = build_index(scope="all")
    write_outputs(payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
