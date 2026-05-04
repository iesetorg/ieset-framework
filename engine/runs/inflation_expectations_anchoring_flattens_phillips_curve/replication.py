#!/usr/bin/env python3
"""Replication wrapper for `inflation_expectations_anchoring_flattens_phillips_curve`.

Re-runs the canonical `scripts/run_local_projections.py` pipeline with `--force` so the run artifact can
be reproduced without duplicating methodology code in this directory.
"""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from _replication_runner import rerun

HYPOTHESIS_ID = 'inflation_expectations_anchoring_flattens_phillips_curve'
RUNNER = 'scripts/run_local_projections.py'


if __name__ == "__main__":
    raise SystemExit(rerun(__file__, HYPOTHESIS_ID, RUNNER))
