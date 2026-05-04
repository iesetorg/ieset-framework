#!/usr/bin/env python3
"""Backfill run-local replication.py wrappers for real-verdict artifacts.

This script repairs the public-visibility gate's `needs_replication_py`
condition without changing any verdict, school link, polarity, score, or
result-card text. A wrapper is only generated when:

- the run already has diagnostics.json and a non-pending real verdict;
- the run does not already have replication.py;
- the recorded/canonical runner is one of the generic reproducible runners.

The generated wrapper delegates to engine/runs/_replication_runner.py, which
reruns the canonical methodology script with the hypothesis id and --force.
"""
from __future__ import annotations

import argparse
import json
import stat
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "engine" / "runs"
sys.path.insert(0, str(Path(__file__).resolve().parent))

import plan_public_visibility_repair_queue


DEFAULT_OUT_BASE = (
    ROOT
    / "engine"
    / "audits"
    / f"replication_wrapper_backfill_{date.today().isoformat()}"
)

RUNNER_BY_TEMPLATE = {
    "panel_fe": "scripts/run_panel_fe.py",
    "panel_fe_decomposition": "scripts/run_panel_fe.py",
    "descriptive": "scripts/run_descriptive.py",
    "event_study": "scripts/run_event_study.py",
    "did_callaway_santanna": "scripts/run_did_callaway_santanna.py",
    "did_chaisemartin": "scripts/run_did_callaway_santanna.py",
    "synth_did": "scripts/run_synth_did.py",
    "synthetic_control": "scripts/run_synth_did.py",
    "local_projections": "scripts/run_local_projections.py",
    "cointegration_vecm": "scripts/run_cointegration_vecm.py",
    "multi_metric_checklist": "scripts/run_multi_metric_checklist.py",
}

ALLOWED_RUNNERS = set(RUNNER_BY_TEMPLATE.values())
REAL_PREFIXES = (
    "SUPPORTED",
    "REFUTED",
    "PARTIAL",
    "MIXED",
    "WEAKLY",
    "WEAKENED",
    "NOT SUPPORTED",
    "NOT_SUPPORTED",
)
PENDING_PREFIXES = ("INCONCLUSIVE", "BLOCKED", "ERROR", "NO VERDICT")


def verdict_text(row: dict[str, Any], diagnostics: dict[str, Any]) -> str:
    return str(
        row.get("verdict_label")
        or diagnostics.get("verdict_label")
        or row.get("verdict")
        or diagnostics.get("verdict")
        or ""
    ).strip()


def is_real_verdict(text: str) -> bool:
    upper = text.upper().lstrip()
    if not upper:
        return False
    if upper.startswith(PENDING_PREFIXES):
        return False
    return any(upper.startswith(prefix) for prefix in REAL_PREFIXES)


def load_plan(limit: int | None) -> dict[str, Any]:
    # Use a high internal limit so the backfill can see all hidden rows.
    return plan_public_visibility_repair_queue.build_plan(limit or 10000)


def wrapper_text(hypothesis_id: str, runner: str) -> str:
    return f'''#!/usr/bin/env python3
"""Replication wrapper for `{hypothesis_id}`.

Delegates to the canonical IESET methodology runner recorded for this run.
This preserves one source of estimation logic while making the run artifact
directly reproducible from engine/runs/{hypothesis_id}/.
"""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from _replication_runner import rerun

HYPOTHESIS_ID = {hypothesis_id!r}
RUNNER = {runner!r}


if __name__ == "__main__":
    raise SystemExit(rerun(__file__, HYPOTHESIS_ID, RUNNER))
'''


def candidate_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        row
        for row in plan.get("queue", [])
        if row.get("reason") == "needs_replication_py"
    ]
    rows.sort(
        key=lambda row: (
            -int(row.get("school_count") or 0),
            -int(row.get("claim_count") or 0),
            -float(row.get("priority_score") or 0),
            str(row.get("hypothesis_id") or ""),
        )
    )
    return rows


def evaluate_row(row: dict[str, Any]) -> dict[str, Any]:
    hid = str(row.get("hypothesis_id") or "")
    run_dir = RUNS / hid
    diag_path = run_dir / "diagnostics.json"
    replication_path = run_dir / "replication.py"
    diagnostics: dict[str, Any] = {}
    if diag_path.exists():
        try:
            diagnostics = json.loads(diag_path.read_text())
        except Exception as exc:
            return {**row, "action": "skip", "skip_reason": f"diagnostics parse failed: {exc}"}
    else:
        return {**row, "action": "skip", "skip_reason": "missing diagnostics.json"}

    verdict = verdict_text(row, diagnostics)
    if not is_real_verdict(verdict):
        return {**row, "action": "skip", "skip_reason": f"not a real verdict: {verdict}"}
    if replication_path.exists():
        return {**row, "action": "skip", "skip_reason": "replication.py already exists"}

    runner = str(row.get("runner") or diagnostics.get("runner") or "").strip()
    template = str(row.get("template") or diagnostics.get("template") or "").strip()
    if not runner and template in RUNNER_BY_TEMPLATE:
        runner = RUNNER_BY_TEMPLATE[template]
    if runner not in ALLOWED_RUNNERS:
        return {
            **row,
            "action": "skip",
            "skip_reason": f"unsupported runner/template: {runner or '-'} / {template or '-'}",
        }
    if not (ROOT / runner).exists():
        return {**row, "action": "skip", "skip_reason": f"runner missing on disk: {runner}"}

    return {
        **row,
        "action": "create",
        "runner": runner,
        "verdict_checked": verdict,
        "replication_path": str(replication_path.relative_to(ROOT)),
    }


def write_wrapper(row: dict[str, Any]) -> None:
    path = ROOT / row["replication_path"]
    path.write_text(wrapper_text(row["hypothesis_id"], row["runner"]))
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def write_audit(rows: list[dict[str, Any]], out_base: Path, apply: bool) -> None:
    out_base.parent.mkdir(parents=True, exist_ok=True)
    created = [row for row in rows if row["action"] == "create"]
    skipped = [row for row in rows if row["action"] == "skip"]
    report = {
        "generated_at": date.today().isoformat(),
        "applied": apply,
        "counts": {
            "created": len(created) if apply else 0,
            "would_create": len(created),
            "skipped": len(skipped),
            "candidates": len(rows),
        },
        "created_or_planned": created,
        "skipped": skipped,
    }
    out_base.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Replication Wrapper Backfill",
        "",
        f"Generated: {date.today().isoformat()}",
        f"- Applied: `{apply}`",
        f"- Candidates: {len(rows)}",
        f"- Would create: {len(created)}",
        f"- Created: {len(created) if apply else 0}",
        f"- Skipped: {len(skipped)}",
        "",
        "## Created Or Planned",
        "",
    ]
    if not created:
        lines.append("- none")
    else:
        for row in created[:300]:
            lines.append(
                f"- `{row['hypothesis_id']}` via `{row['runner']}` "
                f"-> `{row['replication_path']}`"
            )
        if len(created) > 300:
            lines.append(f"- ... {len(created) - 300} more")
    if skipped:
        lines.extend(["", "## Skipped", ""])
        for row in skipped[:80]:
            lines.append(f"- `{row.get('hypothesis_id')}`: {row.get('skip_reason')}")
        if len(skipped) > 80:
            lines.append(f"- ... {len(skipped) - 80} more")
    out_base.with_suffix(".md").write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Actually write wrappers.")
    parser.add_argument("--limit", type=int, default=None, help="Limit candidate rows after sorting.")
    parser.add_argument("--out-base", type=Path, default=DEFAULT_OUT_BASE)
    args = parser.parse_args()

    plan = load_plan(None)
    raw_rows = candidate_rows(plan)
    if args.limit is not None:
        raw_rows = raw_rows[: args.limit]
    evaluated = [evaluate_row(row) for row in raw_rows]
    if args.apply:
        for row in evaluated:
            if row["action"] == "create":
                write_wrapper(row)
    write_audit(evaluated, args.out_base, args.apply)
    created = sum(1 for row in evaluated if row["action"] == "create")
    skipped = sum(1 for row in evaluated if row["action"] == "skip")
    print(
        json.dumps(
            {
                "candidates": len(evaluated),
                "would_create": created,
                "created": created if args.apply else 0,
                "skipped": skipped,
                "audit": str(args.out_base.with_suffix(".json")),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
