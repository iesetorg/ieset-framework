#!/usr/bin/env python3
"""Audit stale legacy panel sign labels without rerunning or promoting results.

This reads specifications, diagnostics, and a fixed historical Git snapshot.
It never opens data vintages or estimates a coefficient. The current runner
fails closed on an unpinned generic sign; this audit does not adjudicate claims.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path

import yaml

from run_panel_fe import infer_claim_direction


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "engine/audits/legacy_panel_sign_inference_2026-10-09.json"
OUT_MD = ROOT / "engine/audits/legacy_panel_sign_inference_2026-10-09.md"
OLD_RUN_COMMIT = "e786a95e676c9d6283c123682d43bf54dbacd73b"
GENERIC_RULE = "the treatment coefficient has the predicted sign at p<0.10"


def old_diagnostics(hypothesis_id: str) -> dict | None:
    result = subprocess.run(
        ["git", "show", f"{OLD_RUN_COMMIT}:engine/runs/{hypothesis_id}/diagnostics.json"],
        cwd=ROOT, capture_output=True, check=False,
    )
    return json.loads(result.stdout) if result.returncode == 0 else None


def build() -> dict:
    records = []
    for path in sorted((ROOT / "hypotheses").glob("*/*.yaml")):
        spec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(spec, dict) or not spec.get("hypothesis_id"):
            continue
        rule = str((spec.get("falsification") or {}).get("rule") or "").lower()
        if GENERIC_RULE not in rule:
            continue
        hypothesis_id = str(spec["hypothesis_id"])
        diagnostics_path = ROOT / "engine/runs" / hypothesis_id / "diagnostics.json"
        if not diagnostics_path.is_file():
            continue
        diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
        if diagnostics.get("runner") != "scripts/run_panel_fe.py":
            continue
        old = old_diagnostics(hypothesis_id)
        outcome = (spec.get("variables") or {}).get("outcome") or []
        outcome_name = outcome[0].get("name") if outcome and isinstance(outcome[0], dict) else None
        stored = diagnostics.get("claim_direction_inferred")
        current_runner_direction = infer_claim_direction(spec, outcome_name)
        historical_direction = old.get("claim_direction_inferred") if old else None
        historical_verdict = old.get("verdict_label") if old else None
        current_verdict = diagnostics.get("verdict_label")
        estimate = diagnostics.get("estimate") or {}
        records.append({
            "hypothesis_id": hypothesis_id,
            "spec_path": str(path.relative_to(ROOT)),
            "current_run_path": str(diagnostics_path.relative_to(ROOT)),
            "historical_run_commit": OLD_RUN_COMMIT if old else None,
            "historical_direction": historical_direction,
            "stored_direction": stored,
            "direction_under_repaired_runner": current_runner_direction,
            "historical_verdict": historical_verdict,
            "stored_verdict": current_verdict,
            "historical_to_stored_direction_changed": historical_direction is not None and historical_direction != stored,
            "stored_vs_repaired_runner_direction_changed": stored != current_runner_direction,
            "historical_to_stored_verdict_changed": historical_verdict is not None and historical_verdict != current_verdict,
            "stored_estimate_coefficient": estimate.get("coefficient"),
            "stored_estimate_p_value": estimate.get("p_value"),
            "audit_status": "manual_direction_and_run_review_required",
        })
    records.sort(key=lambda row: row["hypothesis_id"])
    historical = [row for row in records if row["historical_run_commit"]]
    return {
        "schema": "ieset-legacy-panel-sign-audit-v1",
        "status": "review_queue_not_verdict_correction",
        "historical_run_commit": OLD_RUN_COMMIT,
        "selection_rule": "Exact generic predicted-sign rule and current run_panel_fe diagnostics; no data values opened.",
        "interpretation": (
            "A p-value cutoff in the generic rule was previously parsed as a negative coefficient sign. "
            "The repaired runner fails closed for this unpinned generic rule. Review and explicitly "
            "pin each original claim direction before any new run or result correction. "
            "Legacy same-commit records remain outside the public evidence ledger."
        ),
        "summary": {
            "current_generic_records": len(records),
            "also_present_in_historical_snapshot": len(historical),
            "historical_to_stored_direction_changed": sum(row["historical_to_stored_direction_changed"] for row in historical),
            "stored_vs_repaired_runner_direction_changed": sum(row["stored_vs_repaired_runner_direction_changed"] for row in records),
            "historical_to_stored_verdict_changed": sum(row["historical_to_stored_verdict_changed"] for row in historical),
            "current_stored_verdicts": dict(sorted(Counter(str(row["stored_verdict"]) for row in records).items())),
        },
        "records": records,
    }


def markdown(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# Legacy panel sign inference audit",
        "",
        "This is a metadata-only review queue, **not a corrected verdict set or graduation**. "
        "The generic legacy rule mentioned a treatment coefficient and then `p<0.10`. "
        "The former parser could read that p-value inequality as a negative coefficient sign. "
        "The parser now requires an inequality directly attached to the coefficient token "
        "and fails closed on this unpinned generic rule.",
        "",
        f"- Current generic-rule panel records: **{summary['current_generic_records']}**",
        f"- Also in historical snapshot `{OLD_RUN_COMMIT[:12]}`: **{summary['also_present_in_historical_snapshot']}**",
        f"- Historical-to-stored inferred direction changes: **{summary['historical_to_stored_direction_changed']}**",
        f"- Stored directions differing from the fail-closed runner: **{summary['stored_vs_repaired_runner_direction_changed']}**",
        f"- Historical-to-stored verdict label changes: **{summary['historical_to_stored_verdict_changed']}**",
        "",
        "A claim sentence such as ‘higher tax burden predicts lower participation’ needs a manually pinned sign. "
        "The current runner returns an unknown direction for these generic rules, so a future rerun cannot "
        "award SUPPORT or REFUTATION by text inference. A human must review the original claim and frozen rule "
        "before changing any old verdict. "
        "The legacy runs remain same-commit and archived; this audit adds no school credit.",
        "",
        "## Highest-risk examples",
        "",
        "| Hypothesis | Historical sign/verdict | Stored sign/verdict | Current runner sign |",
        "| --- | --- | --- | --- |",
    ]
    examples = [
        "market_income_school_completion",
        "market_reform_female_education",
        "market_entry_uniform_code_productivity",
        "payroll_tax_labor_force_participation",
    ]
    by_id = {row["hypothesis_id"]: row for row in report["records"]}
    for hypothesis_id in examples:
        row = by_id.get(hypothesis_id)
        if row is None:
            continue
        lines.append(
            f"| `{hypothesis_id}` | {row['historical_direction'] or '—'}/{row['historical_verdict'] or '—'} "
            f"| {row['stored_direction'] or '—'}/{row['stored_verdict'] or '—'} "
            f"| {row['direction_under_repaired_runner'] or '—'} |"
        )
    lines += ["", "All selected IDs and their paths, stored estimates, and label changes are in the JSON report.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = build()
    artifacts = {OUT_JSON: json.dumps(report, indent=2, ensure_ascii=False) + "\n", OUT_MD: markdown(report)}
    for path, content in artifacts.items():
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"stale audit: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    print(
        f"legacy sign audit: {report['summary']['current_generic_records']} generic records, "
        f"{report['summary']['stored_vs_repaired_runner_direction_changed']} stored/current-runner direction differences"
    )


if __name__ == "__main__":
    main()
