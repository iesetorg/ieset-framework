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

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "engine" / "public_corpus_census.json"
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

    return {
        "schema_version": 1,
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
        },
        "counts": {
            "hypothesis_specs": len(hypothesis_specs),
            "conditional_entries": len(conditional_entries),
            "run_directories": len(run_dirs),
            "result_card_files": len(result_cards),
            "policies": count(r"^policies/[^/]+\.yaml$"),
            "movements": count(r"^movements/[^/]+\.yaml$"),
            "positions": count(r"^positions/[^/]+\.yaml$"),
            "review_submissions": count(
                r"^review/submissions/(?!TEMPLATE\.md$)[^/]+\.md$"
            ),
            "completed_review_logs": count(
                r"^review/log/(?!README\.md$)[^/]+\.md$"
            ),
        },
        "verdict_counts": dict(sorted(verdicts.items())),
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
        actual = output.read_text() if output.exists() else ""
        if actual != expected:
            print(
                f"FAIL: {output.relative_to(ROOT)} is stale; run "
                "python scripts/report_public_census.py",
                file=sys.stderr,
            )
            return 1
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(expected)
    print(f"OK ({output.relative_to(ROOT)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
