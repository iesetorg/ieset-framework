#!/usr/bin/env python3
"""Replication wrapper for `latam_extra_capital_account_openness_panel_1990_2024`.

Delegates to the canonical IESET methodology runner recorded for this run.
This preserves one source of estimation logic while making the run artifact
directly reproducible from engine/runs/latam_extra_capital_account_openness_panel_1990_2024/.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HYPOTHESIS_ID = 'latam_extra_capital_account_openness_panel_1990_2024'
RUNNER = 'scripts/rerun_latam_capital_interaction_frozen.py'


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[3]
    raise SystemExit(subprocess.call(
        [sys.executable, str(root / RUNNER), HYPOTHESIS_ID, "--check"], cwd=root,
    ))
