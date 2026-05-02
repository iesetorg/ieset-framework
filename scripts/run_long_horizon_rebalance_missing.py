#!/usr/bin/env python3
"""Run missing diagnostics for the exact long-horizon rebalance backlog."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / "engine" / "long_horizon_market_vs_developmentalist_hypothesis_backlog.md"
RUNS = ROOT / "engine" / "runs"


def backlog_ids() -> list[str]:
    ids: list[str] = []
    for line in BACKLOG.read_text().splitlines():
        match = re.match(r"^\d+\.\s+`([^`]+)`:", line)
        if match:
            ids.append(match.group(1))
    return ids


def missing_ids() -> list[str]:
    return [
        hypothesis_id
        for hypothesis_id in backlog_ids()
        if not (RUNS / hypothesis_id / "diagnostics.json").exists()
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Run at most this many missing IDs.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ids = missing_ids()
    if args.limit:
        ids = ids[: args.limit]

    if args.dry_run:
        print(json.dumps(ids, indent=2))
        return 0

    results: dict[str, int] = {}
    for index, hypothesis_id in enumerate(ids, start=1):
        print(f"[{index}/{len(ids)}] {hypothesis_id}", flush=True)
        proc = subprocess.run(
            [sys.executable, "scripts/run_panel_fe.py", hypothesis_id],
            cwd=ROOT,
            text=True,
            check=False,
        )
        results[hypothesis_id] = proc.returncode

    print(json.dumps(results, indent=2, sort_keys=True))
    return 0 if all(code == 0 for code in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
