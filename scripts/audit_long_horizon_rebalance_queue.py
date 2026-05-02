#!/usr/bin/env python3
"""Audit the exact 100 long-horizon market-vs-developmentalist backlog."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / "engine" / "long_horizon_market_vs_developmentalist_hypothesis_backlog.md"
RUNS = ROOT / "engine" / "runs"


def load_backlog_ids() -> list[str]:
    text = BACKLOG.read_text()
    ids: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^\d+\.\s+`([^`]+)`:", line)
        if match:
            ids.append(match.group(1))
    return ids


def load_verdict(hypothesis_id: str) -> str | None:
    path = RUNS / hypothesis_id / "diagnostics.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return "invalid_json"
    return str(data.get("verdict", "missing_verdict")).lower()


def verdict_bucket(verdict: str) -> str:
    verdict = verdict.strip().lower()
    if verdict.startswith("supported"):
        return "supported"
    if verdict.startswith("refuted"):
        return "refuted"
    if verdict.startswith("partial"):
        return "partial"
    if verdict.startswith("inconclusive"):
        return "inconclusive"
    return verdict or "missing_verdict"


def blocker_bucket(verdict: str) -> str | None:
    verdict = verdict.lower()
    if not verdict.startswith("inconclusive"):
        return None
    if "interaction term" in verdict:
        return "interaction_not_constructible"
    if "no treatment variable loaded" in verdict:
        return "missing_treatment"
    if "no outcome variable loaded" in verdict:
        return "missing_outcome"
    if "insufficient observations" in verdict:
        return "insufficient_observations"
    return "other_inconclusive"


def main() -> int:
    ids = load_backlog_ids()
    completed: dict[str, str] = {}
    missing: list[str] = []
    spec_paths = {path.stem: path for path in (ROOT / "hypotheses").glob("**/*.yaml")}
    missing_with_spec: list[str] = []
    missing_without_spec: list[str] = []

    for hypothesis_id in ids:
        verdict = load_verdict(hypothesis_id)
        if verdict is None:
            missing.append(hypothesis_id)
            if hypothesis_id in spec_paths:
                missing_with_spec.append(hypothesis_id)
            else:
                missing_without_spec.append(hypothesis_id)
        else:
            completed[hypothesis_id] = verdict

    blockers = Counter()
    for verdict in completed.values():
        bucket = blocker_bucket(verdict)
        if bucket:
            blockers[bucket] += 1

    payload = {
        "backlog_file": str(BACKLOG.relative_to(ROOT)),
        "backlog_count": len(ids),
        "with_diagnostics": len(completed),
        "missing_diagnostics": len(missing),
        "missing_with_spec": len(missing_with_spec),
        "missing_without_spec": len(missing_without_spec),
        "verdict_counts": dict(Counter(verdict_bucket(v) for v in completed.values())),
        "inconclusive_blocker_counts": dict(blockers),
        "missing_ids": missing,
        "missing_with_spec_ids": missing_with_spec,
        "missing_without_spec_ids": missing_without_spec,
        "completed_ids": completed,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
