#!/usr/bin/env python3
"""Report evidence-tier conversion blockers without changing a verdict or gate.

The queue is a review aid. In particular, an explicit legacy ``verdict_label``
is a candidate for reconciliation, not proof that the underlying run is sound.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import audit_evidence_tiers

ROOT = Path(__file__).resolve().parents[1]
NON_RESULTS = ("inconclusive", "blocked", "error", "no verdict")


def explicit_result_label(hypothesis_id: str) -> str | None:
    path = ROOT / "engine" / "runs" / hypothesis_id / "diagnostics.json"
    if not path.is_file():
        return None
    try:
        diagnostics = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(diagnostics, dict):
        return None
    label = str(diagnostics.get("verdict_label") or "").strip()
    if not label or label.lower().startswith(NON_RESULTS):
        return None
    return label


def primary_path(record: dict[str, Any]) -> str:
    """Assign one first action; all simultaneous exclusions remain in JSON."""
    reasons = set(record.get("exclusion_reasons") or [])
    if record.get("public_visible"):
        return "public_visible"
    if record.get("registration_status") != "verified":
        return "new_prospective_v2_run_required"
    if reasons & {
        "integrity_detector_flagged",
        "audit_quarantined_pending_v2",
        "audit_verdict_rescore_pending_v2",
    }:
        return "integrity_reconcile_and_rerun"
    if "estimator_floor_failed" in reasons:
        return "estimator_repair_and_rerun"
    if "non_result_verdict" in reasons or "run_missing" in reasons:
        return "data_or_design_rerun"
    if "falsification_rule_unsharpened" in reasons:
        return "prospective_rule_version_required"
    if "verdict_missing" in reasons:
        if explicit_result_label(str(record["hypothesis_id"])):
            return "explicit_label_reconciliation_review"
        return "missing_result_rerun"
    if "replication_missing" in reasons:
        return "replication_path_review"
    return "other_manual_review"


def build() -> dict[str, Any]:
    ledger = audit_evidence_tiers.build()
    records = ledger["records"]
    queue: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        path = primary_path(record)
        if path == "public_visible":
            continue
        item = {
            "hypothesis_id": record["hypothesis_id"],
            "registration_status": record["registration_status"],
            "exclusion_reasons": record["exclusion_reasons"],
        }
        if path == "explicit_label_reconciliation_review":
            item["existing_verdict_label"] = explicit_result_label(
                str(record["hypothesis_id"])
            )
        queue[path].append(item)

    for items in queue.values():
        items.sort(key=lambda item: str(item["hypothesis_id"]))
    counts = Counter({path: len(items) for path, items in queue.items()})
    return {
        "schema": "ieset-hypothesis-conversion-funnel-v1",
        "source": "scripts/audit_evidence_tiers.py::build (live source specs and runs)",
        "method": (
            "One first-action path per archived record. Simultaneous blockers are "
            "retained in exclusion_reasons. Queue membership does not grant "
            "a verdict, registration credit, or scoreboard eligibility."
        ),
        "summary": {
            "hypotheses": len(records),
            "public_visible": ledger["summary"]["public_visible"],
            "tier_counts": ledger["summary"]["tier_counts"],
            "registration_counts": ledger["summary"]["registration_counts"],
            "verified_archive": sum(
                row["registration_status"] == "verified" and not row["public_visible"]
                for row in records
            ),
            "primary_path_counts": dict(sorted(counts.items())),
            "exclusion_counts": ledger["summary"]["exclusion_counts"],
        },
        "queue": dict(sorted(queue.items())),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    rows = [
        "# Hypothesis conversion funnel",
        "",
        "This is a local source-and-run audit, not a graduation decision. A previous "
        "scoreboard claim-link total is not a count of independently graduated hypotheses.",
        "",
        f"- Hypotheses: **{summary['hypotheses']:,}**",
        f"- Public visible: **{summary['public_visible']:,}** "
        f"({summary['tier_counts'].get('featured', 0)} featured; "
        f"{summary['tier_counts'].get('calibration', 0)} calibration)",
        f"- Archived with verified registration: **{summary['verified_archive']:,}**",
        "",
        "| First action | Records |",
        "| --- | ---: |",
    ]
    for name, count in summary["primary_path_counts"].items():
        rows.append(f"| `{name}` | {count:,} |")
    rows += [
        "",
        "## Review queues",
        "",
        "An existing `verdict_label` may be copied to a missing canonical verdict "
        "only after checking its run, correction status, and replication path. "
        "Missing replication code requires a reproducible runner review. Estimator "
        "failures and non-results require new runs; legacy same-commit records "
        "require a genuinely prospective v2 registration and run.",
        "",
    ]
    for name in ("explicit_label_reconciliation_review", "replication_path_review"):
        items = report["queue"].get(name, [])
        rows.append(f"### {name.replace('_', ' ').title()} ({len(items)})")
        rows.append("")
        if items:
            rows.extend(f"- `{item['hypothesis_id']}`" for item in items[:30])
            if len(items) > 30:
                rows.append(f"- … {len(items) - 30} more in the JSON queue")
        else:
            rows.append("- None")
        rows.append("")
    rows += [
        "## Evidence boundary",
        "",
        "This report does not alter results or loosen registration, estimator, "
        "replication, falsification, correction, or second-order gates. "
        "Every conversion needs a refreshed evidence ledger and claim-level audit.",
        "",
    ]
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    json_path = ROOT / "engine" / "audits" / f"hypothesis_conversion_funnel_{args.as_of}.json"
    md_path = json_path.with_suffix(".md")
    report = build()
    outputs = {
        json_path: json.dumps(report, indent=2, sort_keys=True) + "\n",
        md_path: render_markdown(report),
    }
    if args.check:
        stale = [path for path, content in outputs.items() if not path.exists() or path.read_text() != content]
        if stale:
            for path in stale:
                print(f"STALE {path.relative_to(ROOT)}")
            return 1
    else:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    print(
        f"{report['summary']['public_visible']} visible / "
        f"{report['summary']['hypotheses']} hypotheses; "
        f"{report['summary']['verified_archive']} verified archived"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
