#!/usr/bin/env python3
"""Build a deterministic, definition-bearing census of the public corpus."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "engine" / "public_corpus_census.json"
PUBLIC_OUTPUT = ROOT / "web" / "public" / "stats.json"
EVIDENCE_AUDIT = ROOT / "engine" / "evidence_tier_audit.json"
SPEC_RE = re.compile(r"^hypotheses/([^/]+)/[^/]+\.yaml$")
VERDICT_RE = re.compile(
    r"^(?:\*\*)?verdict:?(?:\*\*)?:?\s*(.+)$",
    flags=re.IGNORECASE | re.MULTILINE,
)


def tracked_paths() -> list[str]:
    output = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    return sorted(
        item.decode("utf-8", errors="surrogateescape")
        for item in output.split(b"\0")
        if item
    )


def verdict_bucket(text: str) -> str:
    match = VERDICT_RE.search(text)
    if not match:
        return "missing"
    value = match.group(1).strip().lower()
    if value.startswith("supported_subset"):
        return "supported_subset"
    if value.startswith("inconclusive_data_pending"):
        return "inconclusive_data_pending"
    token = re.split(r"[^a-z_]+", value, maxsplit=1)[0]
    return token or "missing"


def build() -> dict[str, object]:
    paths = tracked_paths()
    run_dirs = {
        path.split("/", 3)[2]
        for path in paths
        if path.startswith("engine/runs/") and len(path.split("/", 3)) == 4
    }
    hypothesis_specs = [
        path
        for path in paths
        if (match := SPEC_RE.match(path))
        and match.group(1) not in {"conditional_taxonomy", "steelman"}
    ]
    conditional_entries = [
        path for path in paths
        if path.startswith("hypotheses/conditional_taxonomy/")
        and path.endswith(".yaml")
    ]
    result_cards = [
        path for path in paths
        if re.match(r"^engine/runs/[^/]+/result_card\.md$", path)
    ]
    verdicts = Counter()
    for path in result_cards:
        verdicts[verdict_bucket((ROOT / path).read_text(errors="replace"))] += 1

    def count(pattern: str) -> int:
        regex = re.compile(pattern)
        return sum(1 for path in paths if regex.match(path))

    position_paths = [
        path
        for path in paths
        if re.match(r"^positions/(?!_)[^/]+\.yaml$", path)
    ]
    position_roles = Counter()
    for path in position_paths:
        try:
            doc = yaml.safe_load((ROOT / path).read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            doc = {}
        role = (
            str(doc.get("scoreboard_role") or "school")
            if isinstance(doc, dict)
            else "school"
        )
        position_roles[role] += 1

    evidence_audit: dict[str, object] = {}
    if EVIDENCE_AUDIT.exists():
        try:
            value = json.loads(EVIDENCE_AUDIT.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                evidence_audit = value
        except (OSError, json.JSONDecodeError):
            pass
    evidence_summary = evidence_audit.get("summary")
    if not isinstance(evidence_summary, dict):
        evidence_summary = {}
    tier_counts = evidence_summary.get("tier_counts")
    registration_counts = evidence_summary.get("registration_counts")
    estimator_failures = evidence_summary.get("estimator_floor_failures")
    exclusion_counts = evidence_summary.get("exclusion_counts")

    return {
        "schema_version": 2,
        "canonical_url": "https://framework.ieset.org/stats.json",
        "repository": "https://github.com/iesetorg/ieset-framework",
        "definitions": {
            "hypothesis_specs": (
                "Tracked hypotheses/<topic>/<id>.yaml files, excluding "
                "conditional_taxonomy and steelman."
            ),
            "run_directories": "Unique tracked engine/runs/<id>/ directories.",
            "result_card_files": (
                "Tracked engine/runs/<id>/result_card.md files, regardless of "
                "verdict or public-visibility gate."
            ),
            "review_submissions": (
                "Tracked review/submissions/*.md excluding TEMPLATE.md."
            ),
            "completed_review_logs": (
                "Tracked review/log/*.md excluding README.md. Internal audit "
                "notes are not counted as external peer review."
            ),
            "positions": (
                "Tracked positions/*.yaml school or benchmark records, "
                "excluding underscore-prefixed derived indexes."
            ),
            "ranked_schools": (
                "Position records with scoreboard_role=school."
            ),
            "benchmark_controls": (
                "Position records with scoreboard_role=benchmark_control; "
                "reported separately and excluded from school rankings."
            ),
            "public_visible_results": (
                "Hypotheses passing strict registration, replication, "
                "falsification-rule, verdict, and estimator-floor gates."
            ),
            "featured_evidence": (
                "Public-visible causal records without screening markers."
            ),
            "calibration_evidence": (
                "Public-visible lower-identification or screening-grade records."
            ),
            "archive_records": (
                "Inspectable records that do not clear all public evidence gates."
            ),
            "reference_set": (
                "Hand-audited exemplars; not peer review and not a substitute "
                "for the evidence tier."
            ),
        },
        "counts": {
            "hypothesis_specs": len(hypothesis_specs),
            "conditional_entries": len(conditional_entries),
            "run_directories": len(run_dirs),
            "result_card_files": len(result_cards),
            "policies": count(r"^policies/[^/]+\.yaml$"),
            "movements": count(r"^movements/[^/]+\.yaml$"),
            "positions": len(position_paths),
            "ranked_schools": position_roles.get("school", 0),
            "benchmark_controls": position_roles.get("benchmark_control", 0),
            "review_submissions": count(
                r"^review/submissions/(?!TEMPLATE\.md$)[^/]+\.md$"
            ),
            "completed_review_logs": count(
                r"^review/log/(?!README\.md$)[^/]+\.md$"
            ),
            "public_visible_results": int(
                evidence_summary.get("public_visible") or 0
            ),
            "featured_evidence": int(
                tier_counts.get("featured", 0)
                if isinstance(tier_counts, dict)
                else 0
            ),
            "calibration_evidence": int(
                tier_counts.get("calibration", 0)
                if isinstance(tier_counts, dict)
                else 0
            ),
            "archive_records": int(
                tier_counts.get("archive", 0)
                if isinstance(tier_counts, dict)
                else 0
            ),
            "reference_set": int(evidence_summary.get("reference_set") or 0),
        },
        "verdict_counts": dict(sorted(verdicts.items())),
        "registration_counts": (
            dict(sorted(registration_counts.items()))
            if isinstance(registration_counts, dict)
            else {}
        ),
        "estimator_floor_failure_counts": (
            dict(sorted(estimator_failures.items()))
            if isinstance(estimator_failures, dict)
            else {}
        ),
        "evidence_exclusion_counts": (
            dict(sorted(exclusion_counts.items()))
            if isinstance(exclusion_counts, dict)
            else {}
        ),
    }


def encoded(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    expected = encoded(build())
    if args.check:
        targets = [output]
        if output.resolve() == DEFAULT_OUTPUT.resolve():
            targets.append(PUBLIC_OUTPUT)
        stale = [
            target
            for target in targets
            if not target.exists()
            or target.read_text(encoding="utf-8") != expected
        ]
        if stale:
            for target in stale:
                print(
                    f"FAIL: {target.relative_to(ROOT)} is stale; run "
                    "python scripts/report_public_census.py",
                    file=sys.stderr,
                )
            return 1
    else:
        targets = [output]
        if output.resolve() == DEFAULT_OUTPUT.resolve():
            targets.append(PUBLIC_OUTPUT)
        for target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(expected, encoding="utf-8")
    print(
        "OK ("
        + ", ".join(str(target.relative_to(ROOT)) for target in targets)
        + ")"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
