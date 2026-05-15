#!/usr/bin/env python3
"""Rerun only this Singapore LKY checklist run."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_singapore_lky_wave as wave

HYPOTHESIS_ID = "singapore_lky_growth_takeoff_1965_1990"
RUN_DIR = Path(__file__).resolve().parent


def main() -> int:
    study = next((s for s in wave.studies() if s.hid == HYPOTHESIS_ID), None)
    if study is None:
        raise SystemExit(f"unknown study: {HYPOTHESIS_ID}")

    verdict, reason, rows = wave.evaluate(study)
    paths = wave.source_paths(study)

    pd.DataFrame(rows).to_parquet(RUN_DIR / "coefficients.parquet", index=False)
    (RUN_DIR / "chart_data.json").write_text(json.dumps(rows, indent=2) + "\n")
    diagnostics = {
        "hypothesis_id": study.hid,
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "template": "singapore_lky_local_multimetric_checklist",
        "metrics": rows,
        "support_threshold": study.support_threshold,
        "refute_threshold": study.refute_threshold,
        "vintages": {src: str(path.relative_to(wave.ROOT)) for src, path in paths.items()},
        "sha256": {src: wave.sha256(path) for src, path in paths.items()},
        "runner": "engine/runs/singapore_lky_growth_takeoff_1965_1990/replication.py",
    }
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (RUN_DIR / "manifest.yaml").write_text(
        yaml.dump(
            {
                "hypothesis_id": study.hid,
                "status": verdict,
                "reason": reason,
                "vintages": {src: str(path.relative_to(wave.ROOT)) for src, path in paths.items()},
            },
            Dumper=wave.NoAliasDumper,
            sort_keys=False,
        )
    )

    table = pd.DataFrame(rows)
    lines = [
        f"# Result card - {study.hid}",
        "",
        f"**Verdict:** {verdict} - {reason}",
        "",
        "## Pre-registration",
        f"- **Claim:** {study.claim}",
        f"- **Falsification rule:** SUPPORTED if at least {study.support_threshold} of {len(study.metrics)} metrics meet their thresholds; REFUTED if at most {study.refute_threshold} meet after available data are evaluated.",
        f"- **Falsification test:** {study.hid}_local_multimetric_checklist",
        "",
        "## Metric Results",
        "| metric | observed | threshold | status | note |",
        "|---|---:|---|---|---|",
    ]
    for _, row in table[["metric_id", "observed", "threshold", "status", "note"]].iterrows():
        observed = "pending" if pd.isna(row["observed"]) else f"{row['observed']:.3f}"
        note = str(row["note"]).replace("|", "/")
        lines.append(f"| {row['metric_id']} | {observed} | {row['threshold']} | {row['status']} | {note} |")
    lines += [
        "",
        "## Interpretation",
        "This is a pre-registered descriptive checklist over local vintages. It grades whether the observed Singapore pattern clears the stated thresholds; it does not identify a single causal lever inside the LKY-era bundle.",
        "",
        "## Sources",
    ]
    for src, path in paths.items():
        lines.append(f"- `{src}` -> `{path.relative_to(wave.ROOT)}`")
    lines += ["", "## Steelman", f"See `hypotheses/steelman/{study.hid}.md`.", ""]
    (RUN_DIR / "result_card.md").write_text("\n".join(lines))
    print(f"{HYPOTHESIS_ID}: {verdict} - {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
