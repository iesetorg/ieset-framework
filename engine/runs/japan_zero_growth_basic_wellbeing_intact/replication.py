#!/usr/bin/env python3
"""Replication wrapper for `japan_zero_growth_basic_wellbeing_intact`.

Delegates to the canonical IESET multi-metric checklist runner so the archived
run is reproducible without duplicating methodology logic here.
"""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from _replication_runner import rerun

HYPOTHESIS_ID = "japan_zero_growth_basic_wellbeing_intact"
RUNNER = "scripts/run_multi_metric_checklist.py"


if __name__ == "__main__":
    raise SystemExit(rerun(__file__, HYPOTHESIS_ID, RUNNER))
