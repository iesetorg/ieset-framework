#!/usr/bin/env python3
"""Replication wrapper for `usd_issuer_solvency_no_default_post_1971`.

Delegates to the canonical IESET methodology runner recorded for this run.
This preserves one source of estimation logic while making the run artifact
directly reproducible from engine/runs/usd_issuer_solvency_no_default_post_1971/.
"""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from _replication_runner import rerun

HYPOTHESIS_ID = 'usd_issuer_solvency_no_default_post_1971'
RUNNER = 'scripts/run_descriptive.py'


if __name__ == "__main__":
    raise SystemExit(rerun(__file__, HYPOTHESIS_ID, RUNNER))
