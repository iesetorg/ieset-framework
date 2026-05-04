#!/usr/bin/env python3
"""Replication wrapper for `china_growth_health_services_shift_1990_2023`.

Re-runs the canonical `scripts/run_multi_metric_checklist.py` pipeline with `--force` so the run artifact can
be reproduced without duplicating methodology code in this directory.
"""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from _replication_runner import rerun

HYPOTHESIS_ID = 'china_growth_health_services_shift_1990_2023'
RUNNER = 'scripts/run_multi_metric_checklist.py'


if __name__ == "__main__":
    raise SystemExit(rerun(__file__, HYPOTHESIS_ID, RUNNER))
