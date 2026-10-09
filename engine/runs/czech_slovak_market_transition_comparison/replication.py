#!/usr/bin/env python3
"""Replication wrapper for `czech_slovak_market_transition_comparison`.

Delegates to the canonical IESET methodology runner recorded for this run.
This preserves one source of estimation logic while making the run artifact
directly reproducible from engine/runs/czech_slovak_market_transition_comparison/.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HYPOTHESIS_ID = 'czech_slovak_market_transition_comparison'
RUNNER = 'scripts/rerun_czech_slovak_frozen.py'


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[3]
    raise SystemExit(subprocess.call(
        [sys.executable, str(root / RUNNER), HYPOTHESIS_ID, "--check"], cwd=root,
    ))
