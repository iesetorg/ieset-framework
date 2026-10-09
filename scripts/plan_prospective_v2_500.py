#!/usr/bin/env python3
"""Prioritize legacy hypotheses for *review* before prospective v2 tests.

This script never writes specifications, runs, or verdicts. A selected case is
only a research-work item. Its existing result is known to the analyst, so a
future v2 must disclose that fact and register a genuinely new design or
independent validation sample before any new estimation.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import yaml

import audit_evidence_tiers


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "engine" / "preregistration_index.json"
DECISIVE_OR_PARTIAL = {"supported", "refuted", "partial"}
PANEL_TEMPLATES = {"panel_fe", "panel_fe_decomposition", "local_projections"}


def as_positive_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) and number >= 0 else None


def loaded_sources(diagnostics: dict[str, Any]) -> list[str]:
    status = diagnostics.get("data_status") or {}
    if not isinstance(status, dict):
        return []
    loaded = status.get("variables_loaded") or []
    if not isinstance(loaded, list):
        return []
    return sorted({
        str(item["source"])
        for item in loaded
        if isinstance(item, dict) and item.get("source")
    })


def missing_variables(diagnostics: dict[str, Any]) -> list[str]:
    status = diagnostics.get("data_status") or {}
    if not isinstance(status, dict):
        return []
    missing = status.get("variables_missing") or status.get("missing_series") or []
    if not isinstance(missing, list):
        return [str(missing)]
    return sorted({str(item) for item in missing})


def inspect(record: dict[str, Any], registrations: dict[str, Any]) -> dict[str, Any]:
    hypothesis_id = str(record["hypothesis_id"])
    registration = registrations[hypothesis_id]
    spec_path = ROOT / str(registration["path"])
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    run_dir = ROOT / "engine" / "runs" / hypothesis_id
    diagnostics_path = run_dir / "diagnostics.json"
    try:
        diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        diagnostics = {}

    estimator = spec.get("estimator") or {}
    template = str(estimator.get("template") or "missing") if isinstance(estimator, dict) else "missing"
    estimate = diagnostics.get("estimate") or {}
    estimate = estimate if isinstance(estimate, dict) else {}
    n_obs = as_positive_number(estimate.get("n_obs"))
    n_units = as_positive_number(estimate.get("n_countries", estimate.get("n_units")))
    old_label = str(diagnostics.get("verdict_label") or diagnostics.get("verdict") or "")
    old_bucket = audit_evidence_tiers.verdict_bucket(old_label)
    missing = missing_variables(diagnostics)
    screening = list(record.get("screening_flags") or [])
    estimator_failures = list(record.get("estimator_floor_failures") or [])
    integrity = list(record.get("integrity_detector_findings") or [])
    exclusions = list(record.get("exclusion_reasons") or [])
    old_status = str(spec.get("status") or "missing")
    runner = str(diagnostics.get("runner") or "")

    flags: list[str] = []
    if old_status != "pre_registered":
        flags.append("old_spec_requires_full_design_review")
    if old_bucket not in DECISIVE_OR_PARTIAL:
        flags.append("old_result_not_canonical")
    if missing:
        flags.append("missing_variables")
    if estimator_failures:
        flags.append("estimator_floor_failure")
    if integrity or any(value.startswith("audit_") for value in exclusions):
        flags.append("integrity_or_correction_review")
    if "falsification_rule_unsharpened" in exclusions:
        flags.append("falsification_rule_unsharpened")
    if screening:
        flags.append("screening_or_proxy_design")
    if runner == "scripts/run_heritage_market_cross_section.py":
        flags.append("heritage_cross_section_direct_measure_review")
    if template in PANEL_TEMPLATES and n_obs is not None and n_obs < 30:
        flags.append("small_panel_sample_review")
    if template in PANEL_TEMPLATES and n_units is not None and n_units < 5:
        flags.append("few_panel_units_review")
    if not (run_dir / "replication.py").is_file():
        flags.append("old_replication_missing")
    if not (run_dir / "manifest.yaml").is_file():
        flags.append("old_manifest_missing")
    if not (run_dir / "evidence_packet.yaml").is_file():
        flags.append("old_evidence_packet_missing")

    # Scores order human review only. They are deliberately independent of the
    # prior coefficient sign, p-value, and public school score.
    score = {"pre_registered": 15, "candidate": 7, "draft": 0}.get(old_status, 0)
    score += 8 if old_bucket in DECISIVE_OR_PARTIAL else 0
    score += 6 if not missing else -12
    score += 6 if "old_replication_missing" not in flags else -8
    score += 3 if "old_manifest_missing" not in flags else 0
    score += 3 if "old_evidence_packet_missing" not in flags else 0
    score += 3 if loaded_sources(diagnostics) else 0
    score -= 20 if estimator_failures else 0
    score -= 25 if "integrity_or_correction_review" in flags else 0
    score -= 15 if "falsification_rule_unsharpened" in flags else 0
    score -= 8 if screening else 0
    score -= 8 if "heritage_cross_section_direct_measure_review" in flags else 0
    score -= 12 if "small_panel_sample_review" in flags else 0
    score -= 12 if "few_panel_units_review" in flags else 0

    if "integrity_or_correction_review" in flags:
        next_action = "resolve integrity finding and correction disposition before designing v2"
    elif "estimator_floor_failure" in flags or "few_panel_units_review" in flags:
        next_action = "design a valid estimator and adequate sample before preregistration"
    elif missing:
        next_action = "obtain direct missing measures, then specify a prospective validation design"
    elif "screening_or_proxy_design" in flags or "heritage_cross_section_direct_measure_review" in flags:
        next_action = "replace broad proxy with claim-specific measures and trajectory design"
    elif old_bucket not in DECISIVE_OR_PARTIAL:
        next_action = "repair data or design, then preregister a new validation test"
    else:
        next_action = "review old test and specify independent holdout or new design"

    return {
        "hypothesis_id": hypothesis_id,
        "topic": str(spec.get("topic") or spec_path.parent.name),
        "spec_path": str(spec_path.relative_to(ROOT)),
        "old_spec_status": old_status,
        "old_evidence_type": str(spec.get("evidence_type") or "missing"),
        "old_estimator_template": template,
        "old_result_bucket": old_bucket,
        "old_run_dir": str(run_dir.relative_to(ROOT)),
        "old_runner": runner or None,
        "old_n_obs": n_obs,
        "old_n_units": n_units,
        "old_loaded_sources": loaded_sources(diagnostics),
        "old_missing_variables": missing,
        "old_estimator_failures": estimator_failures,
        "old_integrity_findings": integrity,
        "review_flags": flags,
        "next_action": next_action,
        "review_priority_score": score,
        "new_spec_registered": False,
        "new_run_completed": False,
        "graduated": False,
    }


def build(target: int) -> dict[str, Any]:
    registrations = json.loads(INDEX.read_text(encoding="utf-8"))["registrations"]
    ledger = audit_evidence_tiers.build()
    legacy = [
        record for record in ledger["records"]
        if record["registration_status"] == "legacy_same_commit"
    ]
    rows = [inspect(record, registrations) for record in legacy]
    rows.sort(key=lambda row: (-row["review_priority_score"], row["hypothesis_id"]))
    for rank, row in enumerate(rows, 1):
        row["review_rank"] = rank
        row["selected_for_target_500_review"] = rank <= target
    selected = rows[:target]
    return {
        "schema": "ieset-prospective-v2-review-queue-v1",
        "purpose": (
            "Rank legacy_same_commit hypotheses for independent prospective v2 "
            "design review. Selection is neither a preregistration nor a graduation."
        ),
        "selection_rule": (
            "Sort by inspectable old record completeness and method-risk flags; "
            "never use old coefficient direction, p-value, or scoreboard benefit."
        ),
        "required_before_new_graduation": [
            "Audit the old claim, outcome, sources, method, and any integrity finding.",
            "Write a materially specified follow-up with a new hypothesis ID and steelman; disclose that the old result was seen.",
            "Define an independent holdout, new data vintage, or genuinely revised estimand and fixed falsification rule.",
            "Commit the new spec in git; only then estimate and commit run artifacts in a later commit.",
            "Validate registration history, data provenance, replication, estimator floor, correction state, and second-order measurement.",
            "Run evidence-tier and claim-level audits before any public/scoreboard credit.",
        ],
        "summary": {
            "legacy_pool": len(rows),
            "review_target": target,
            "selected": len(selected),
            "new_graduations_created": 0,
            "selected_old_spec_status": dict(sorted(Counter(row["old_spec_status"] for row in selected).items())),
            "selected_old_result_bucket": dict(sorted(Counter(row["old_result_bucket"] for row in selected).items())),
            "selected_topic": dict(sorted(Counter(row["topic"] for row in selected).items())),
            "selected_review_flags": dict(sorted(Counter(flag for row in selected for flag in row["review_flags"]).items())),
        },
        "cases": rows,
    }


def markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    selected = report["cases"][:summary["selected"]]
    lines = [
        "# Prospective v2 review queue for 500 legacy hypotheses",
        "",
        "This is a prioritized audit queue, not 500 preregistrations or graduations. "
        "Every selected case already has an old run whose result may have been seen. "
        "The old same-commit history cannot be repaired by rerunning that ID.",
        "",
        f"- Legacy pool: **{summary['legacy_pool']:,}**",
        f"- Selected for design review: **{summary['selected']:,}**",
        "- New strict registrations: **0**",
        "- New run results: **0**",
        "- New graduations from this queue: **0**",
        "",
        "## Selected old-spec status",
        "",
        "| Status | Cases |",
        "| --- | ---: |",
    ]
    lines += [f"| `{key}` | {count:,} |" for key, count in summary["selected_old_spec_status"].items()]
    lines += ["", "## Review flags", "", "| Flag | Cases |", "| --- | ---: |"]
    lines += [f"| `{key}` | {count:,} |" for key, count in summary["selected_review_flags"].items()]
    lines += [
        "",
        "## First 40 review cases",
        "",
        "| Rank | Hypothesis | Topic | Old result | Next action |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for row in selected[:40]:
        lines.append(
            f"| {row['review_rank']} | `{row['hypothesis_id']}` | {row['topic']} | "
            f"{row['old_result_bucket']} | {row['next_action']} |"
        )
    lines += [
        "",
        "All 500 selected cases and the 820 remaining legacy cases are in the JSON "
        "artifact; the selected 500 also have a compact CSV.",
        "",
        "## Required sequence",
        "",
    ]
    lines += [f"{rank}. {step}" for rank, step in enumerate(report["required_before_new_graduation"], 1)]
    lines += [
        "",
        "Review priority is based on old artifact completeness and recorded method risks. "
        "It is not a probability of replication and never uses the old coefficient "
        "direction, p-value, or any expected school-score change.",
        "",
    ]
    return "\n".join(lines)


def csv_text(rows: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    fields = [
        "review_rank", "hypothesis_id", "topic", "old_spec_status", "old_evidence_type",
        "old_estimator_template", "old_result_bucket", "old_n_obs", "old_n_units",
        "review_priority_score", "review_flags", "next_action", "spec_path", "old_run_dir",
    ]
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({
            field: ";".join(row[field]) if field == "review_flags" else row[field]
            for field in fields
        })
    return output.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--target", type=int, default=500)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = build(args.target)
    if not 0 < args.target <= report["summary"]["legacy_pool"]:
        parser.error("target must be between 1 and the legacy pool size")
    stem = f"prospective_v2_{args.target}_review_queue_{args.as_of}"
    base = ROOT / "engine" / "audits" / stem
    outputs = {
        base.with_suffix(".json"): json.dumps(report, indent=2, sort_keys=True) + "\n",
        base.with_suffix(".md"): markdown(report),
        base.with_suffix(".csv"): csv_text(report["cases"][:args.target]),
    }
    if args.check:
        stale = [path for path, content in outputs.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
        for path in stale:
            print(f"STALE {path.relative_to(ROOT)}")
        return 1 if stale else 0
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"{len(report['cases'])} legacy cases audited; {args.target} selected for review; 0 new graduations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
