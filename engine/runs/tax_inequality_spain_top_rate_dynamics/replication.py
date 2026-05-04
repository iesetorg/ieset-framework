#!/usr/bin/env python3
"""Replication wrapper for `tax_inequality_spain_top_rate_dynamics`.

Re-runs the canonical `scripts/run_local_projections.py` pipeline with `--force`
so the archived run can be reproduced without duplicating estimator logic.
"""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from _replication_runner import rerun

HYPOTHESIS_ID = "tax_inequality_spain_top_rate_dynamics"
RUNNER = "scripts/run_local_projections.py"


if __name__ == "__main__":
    raise SystemExit(rerun(__file__, HYPOTHESIS_ID, RUNNER))
