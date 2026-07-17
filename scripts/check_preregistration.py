#!/usr/bin/env python3
"""Enforce that a hypothesis spec commit strictly precedes its first run commit.

The check uses git topology, not checkout mtimes. Filesystem mtimes are reset by
fresh checkouts and therefore cannot prove pre-registration.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "engine" / "preregistration_index.json"
DEFAULT_LEGACY = ROOT / "engine" / "preregistration_legacy_exceptions.json"
SPEC_RE = re.compile(r"^hypotheses/([^/]+)/([^/]+)\.yaml$")
SKIP_TOPICS = {"conditional_taxonomy", "steelman"}


@dataclass(frozen=True)
class Addition:
    commit: str
    committed_at: str


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=check,
    )


def first_additions() -> tuple[dict[str, Addition], dict[str, Addition]]:
    """Return first-addition records for tracked paths and run directories."""
    output = git(
        "log",
        "--diff-filter=A",
        "--reverse",
        "--topo-order",
        "--name-only",
        "--format=COMMIT %H|%cI",
        "HEAD",
    ).stdout
    paths: dict[str, Addition] = {}
    runs: dict[str, Addition] = {}
    current: Addition | None = None
    for raw in output.splitlines():
        if raw.startswith("COMMIT "):
            commit, committed_at = raw.removeprefix("COMMIT ").split("|", 1)
            current = Addition(commit=commit, committed_at=committed_at)
            continue
        path = raw.strip()
        if not path or current is None:
            continue
        paths.setdefault(path, current)
        if path.startswith("engine/runs/"):
            parts = path.split("/", 3)
            if len(parts) >= 3 and parts[2]:
                runs.setdefault(parts[2], current)
    return paths, runs


def is_strict_ancestor(older: str, newer: str) -> bool:
    if older == newer:
        return False
    result = git("merge-base", "--is-ancestor", older, newer, check=False)
    return result.returncode == 0


def tracked_paths() -> set[str]:
    output = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    return {
        item.decode("utf-8", errors="surrogateescape")
        for item in output.split(b"\0")
        if item
    }


def load_legacy_exceptions(path: Path) -> set[str]:
    if not path.exists():
        return set()
    payload = json.loads(path.read_text())
    values = payload.get("hypothesis_ids", [])
    return {str(value) for value in values}


def build_index(
    legacy_exceptions: set[str],
) -> tuple[dict[str, object], list[str], set[str]]:
    paths, runs = first_additions()
    tracked = tracked_paths()
    registrations: dict[str, dict[str, object]] = {}
    violations: list[str] = []
    same_commit_ids: set[str] = set()

    for path in sorted(tracked):
        match = SPEC_RE.match(path)
        if not match or match.group(1) in SKIP_TOPICS:
            continue
        if path not in paths:
            violations.append(f"{path}: tracked spec has no first-addition commit")
            continue
        hypothesis_id = match.group(2)
        spec = paths[path]
        run = runs.get(hypothesis_id)
        if run is None:
            status = "registered_no_run"
        elif spec.commit == run.commit:
            status = "legacy_same_commit"
            same_commit_ids.add(hypothesis_id)
            if hypothesis_id not in legacy_exceptions:
                violations.append(
                    f"{hypothesis_id}: spec and run first appear together in "
                    f"{spec.commit[:12]} and are not in the frozen legacy baseline"
                )
        elif is_strict_ancestor(spec.commit, run.commit):
            status = "verified"
        else:
            status = "invalid_history"
            violations.append(
                f"{hypothesis_id}: spec {spec.commit[:12]} is not an ancestor "
                f"of first run commit {run.commit[:12]}"
            )
        registrations[hypothesis_id] = {
            "path": path,
            "spec_commit": spec.commit,
            "spec_committed_at": spec.committed_at,
            "run_first_commit": run.commit if run else None,
            "run_committed_at": run.committed_at if run else None,
            "status": status,
            "verified": status == "verified",
        }

    index: dict[str, object] = {
        "schema_version": 1,
        "definition": (
            "The first commit adding the spec must be a strict git ancestor of "
            "the first commit adding any artifact under its run directory."
        ),
        "registrations": registrations,
    }
    return index, violations, same_commit_ids


def encoded(index: dict[str, object]) -> str:
    return json.dumps(index, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-index", action="store_true")
    parser.add_argument("--check-index", action="store_true")
    parser.add_argument("--write-legacy-baseline", action="store_true")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--legacy", type=Path, default=DEFAULT_LEGACY)
    args = parser.parse_args()

    legacy_path = args.legacy if args.legacy.is_absolute() else ROOT / args.legacy
    legacy_exceptions = load_legacy_exceptions(legacy_path)
    index, violations, same_commit_ids = build_index(legacy_exceptions)
    if args.write_legacy_baseline:
        baseline = {
            "schema_version": 1,
            "definition": (
                "Historical hypothesis IDs whose spec and first run artifact "
                "entered git in the same commit. These are unverified legacy "
                "records, not valid pre-registrations."
            ),
            "hypothesis_ids": sorted(same_commit_ids),
        }
        legacy_path.parent.mkdir(parents=True, exist_ok=True)
        legacy_path.write_text(
            json.dumps(baseline, indent=2, sort_keys=True) + "\n"
        )
        legacy_exceptions = same_commit_ids
        index, violations, same_commit_ids = build_index(legacy_exceptions)
    registrations = index["registrations"]
    assert isinstance(registrations, dict)
    verified = sum(
        1 for row in registrations.values()
        if isinstance(row, dict) and row["status"] == "verified"
    )
    legacy = sum(
        1 for row in registrations.values()
        if isinstance(row, dict) and row["status"] == "legacy_same_commit"
    )

    if violations:
        print(
            f"FAIL: {len(violations)} pre-registration violation(s):",
            file=sys.stderr,
        )
        for violation in violations:
            print(f"  {violation}", file=sys.stderr)
        return 1

    expected = encoded(index)
    index_path = args.index if args.index.is_absolute() else ROOT / args.index
    if args.check_index:
        actual = index_path.read_text() if index_path.exists() else ""
        if actual != expected:
            print(
                f"FAIL: {index_path.relative_to(ROOT)} is stale; run "
                "python scripts/check_preregistration.py --write-index",
                file=sys.stderr,
            )
            return 1
    if args.write_index:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(expected)

    print(
        f"OK ({verified} strict pre-registration pair(s); {legacy} legacy "
        f"same-commit pair(s); {len(registrations) - verified - legacy} "
        "spec(s) have no run)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
