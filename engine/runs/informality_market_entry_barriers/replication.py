#!/usr/bin/env python3
"""Replication wrapper for `informality_market_entry_barriers`.

Delegates to the canonical IESET panel-FE runner while keeping the
run-level reproducibility entrypoint inside this artifact directory.
"""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from _replication_runner import rerun

HYPOTHESIS_ID = "informality_market_entry_barriers"
RUNNER = "scripts/run_panel_fe.py"


if __name__ == "__main__":
    raise SystemExit(rerun(__file__, HYPOTHESIS_ID, RUNNER))
