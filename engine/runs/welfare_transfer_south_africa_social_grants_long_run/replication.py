#!/usr/bin/env python3
"""Replication wrapper for `welfare_transfer_south_africa_social_grants_long_run`.

Delegates to the canonical IESET methodology runner recorded for this run.
This preserves one source of estimation logic while making the run artifact
directly reproducible from engine/runs/welfare_transfer_south_africa_social_grants_long_run/.
"""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from _replication_runner import rerun

HYPOTHESIS_ID = 'welfare_transfer_south_africa_social_grants_long_run'
RUNNER = 'scripts/run_did_callaway_santanna.py'


if __name__ == "__main__":
    raise SystemExit(rerun(__file__, HYPOTHESIS_ID, RUNNER))
