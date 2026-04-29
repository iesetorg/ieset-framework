#!/usr/bin/env python3
"""Enforce invariant 1: pre-registration precedes estimation.

For every hypothesis YAML under hypotheses/<topic>/<id>.yaml, if a corresponding
run directory exists at engine/runs/<id>/, the earliest file mtime in the run
directory must be LATER than the first git commit timestamp of the YAML spec.

Equivalently: the spec must exist in git history before any run artifact was
produced on disk.

Usage:
    python scripts/check_preregistration.py

Exits non-zero if any run predates its spec's first commit.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]


def first_commit_utc(path: Path) -> datetime | None:
    """Return the UTC timestamp of the first commit that introduced `path`, or None."""
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--follow", "--format=%aI", "--", str(path.relative_to(ROOT))],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        print(f"git log failed for {path}: {e.stderr}", file=sys.stderr)
        return None
    if not out:
        return None
    return datetime.fromisoformat(out[-1])


def earliest_run_mtime(run_dir: Path) -> datetime | None:
    files = [p for p in run_dir.rglob("*") if p.is_file()]
    if not files:
        return None
    earliest = min(p.stat().st_mtime for p in files)
    return datetime.fromtimestamp(earliest, tz=timezone.utc)


def main() -> int:
    violations: list[str] = []
    checked = 0
    skipped_untracked = 0

    hyp_root = ROOT / "hypotheses"
    skip = {"conditional_taxonomy", "steelman"}
    hypothesis_dirs = [p for p in hyp_root.iterdir() if p.is_dir() and p.name not in skip] if hyp_root.exists() else []
    yamls = [y for d in hypothesis_dirs for y in d.glob("*.yaml")]

    for yml in yamls:
        with yml.open() as f:
            spec = yaml.safe_load(f)
        if not spec or "hypothesis_id" not in spec:
            continue
        hid = spec["hypothesis_id"]
        run_dir = ROOT / "engine" / "runs" / hid
        if not run_dir.exists():
            continue  # no run yet; nothing to check

        spec_commit_ts = first_commit_utc(yml)
        if spec_commit_ts is None:
            skipped_untracked += 1
            print(f"WARN: {yml} is not in git history; cannot verify pre-registration.", file=sys.stderr)
            continue

        run_ts = earliest_run_mtime(run_dir)
        if run_ts is None:
            continue

        checked += 1
        if run_ts < spec_commit_ts:
            violations.append(
                f"{hid}: run artifact at {run_dir} (earliest mtime {run_ts.isoformat()}) "
                f"predates spec first-commit {spec_commit_ts.isoformat()}"
            )

    if violations:
        print(f"FAIL: {len(violations)} pre-registration violation(s):", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        return 1

    print(f"OK ({checked} hypothesis/run pair(s) verified; {skipped_untracked} untracked spec(s) skipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
