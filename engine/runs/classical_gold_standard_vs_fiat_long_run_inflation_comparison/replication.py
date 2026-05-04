#!/usr/bin/env python3
"""Replication wrapper for `classical_gold_standard_vs_fiat_long_run_inflation_comparison`.

Re-runs the canonical `scripts/run_descriptive.py` pipeline with `--force` so the archived run can
be reproduced without duplicating estimator logic in this directory.
"""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from _replication_runner import rerun

HYPOTHESIS_ID = 'classical_gold_standard_vs_fiat_long_run_inflation_comparison'
RUNNER = 'scripts/run_descriptive.py'


if __name__ == "__main__":
    raise SystemExit(rerun(__file__, HYPOTHESIS_ID, RUNNER))
