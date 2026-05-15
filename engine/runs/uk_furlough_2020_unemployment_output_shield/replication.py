#!/usr/bin/env python3
"""Rerun only this run's UK furlough event-window artifacts."""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_national_event_wave import CASES, manifest_for, verdict_for

HYPOTHESIS_ID = "uk_furlough_2020_unemployment_output_shield"
RUN_DIR = Path(__file__).resolve().parent


def main() -> int:
    case = next((c for c in CASES if c.hypothesis_id == HYPOTHESIS_ID), None)
    if case is None:
        raise SystemExit(f"unknown case: {HYPOTHESIS_ID}")

    metrics = case.metrics_fn()
    run_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    verdict = verdict_for(metrics, case.support_threshold, case.refute_threshold)
    count = sum(m.passed for m in metrics)

    diagnostics = {
        "hypothesis_id": case.hypothesis_id,
        "verdict": verdict,
        "metrics_passed": count,
        "metrics_total": len(metrics),
        "support_threshold": case.support_threshold,
        "refute_threshold": case.refute_threshold,
        "falsification_rule_text": case.rule,
        "metrics": [
            {
                "metric_id": m.metric_id,
                "description": m.description,
                "threshold": m.threshold,
                "window": m.window,
                "source": m.source,
                "value": None if math.isnan(m.value) else m.value,
                "passed": m.passed,
                "details": m.details,
            }
            for m in metrics
        ],
    }
    (RUN_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2), encoding="utf-8"
    )
    (RUN_DIR / "manifest.yaml").write_text(
        yaml.safe_dump(
            manifest_for(case, metrics, run_utc),
            sort_keys=False,
            allow_unicode=False,
        ),
        encoding="utf-8",
    )

    rows = "\n".join(
        f"| {m.metric_id} | {m.value:.3f} | {m.threshold} | "
        f"{'yes' if m.passed else 'no'} | {m.details} |"
        for m in metrics
    )
    (RUN_DIR / "result_card.md").write_text(
        f"# Result card - {case.hypothesis_id}\n\n"
        f"**Verdict:** {verdict} - {count}/{len(metrics)} metrics passed "
        f"(support >= {case.support_threshold}; refute <= {case.refute_threshold}).\n\n"
        f"## Claim\n\n{case.claim}\n\n"
        "## Metrics\n\n"
        "| Metric | Value | Threshold | Pass | Details |\n"
        "|---|---:|---|:---:|---|\n"
        f"{rows}\n\n"
        "## Interpretation\n\n"
        "This is a compact predeclared event-window verdict using local cached "
        "national-statistics vintages. It is strong for timing and magnitude, "
        "but not a full causal structural decomposition.\n\n"
        "## Provenance\n\nSee `manifest.yaml` for exact vintage files and "
        "SHA-256 hashes. Re-run with `replication.py`.\n",
        encoding="utf-8",
    )
    print(f"{HYPOTHESIS_ID}: {verdict} - {count}/{len(metrics)} metrics passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
