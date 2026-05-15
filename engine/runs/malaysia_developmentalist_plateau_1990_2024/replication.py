#!/usr/bin/env python3
"""Replication wrapper for `malaysia_developmentalist_plateau_1990_2024`.

Delegates to the canonical IESET methodology runner recorded for this run.
This keeps the data-pending artifact reproducible from its run directory
without duplicating shared estimation logic.
"""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from _replication_runner import rerun

HYPOTHESIS_ID = "malaysia_developmentalist_plateau_1990_2024"
RUNNER = "scripts/run_panel_fe.py"


if __name__ == "__main__":
    raise SystemExit(rerun(__file__, HYPOTHESIS_ID, RUNNER))
