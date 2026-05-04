#!/usr/bin/env python3
"""Replication wrapper for `boric_chile_2022_2026_constitutional_rejection_market_continuity`.

Delegates to the canonical IESET methodology runner recorded for this run.
This preserves one source of estimation logic while making the run artifact
directly reproducible from engine/runs/boric_chile_2022_2026_constitutional_rejection_market_continuity/.
"""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from _replication_runner import rerun

HYPOTHESIS_ID = 'boric_chile_2022_2026_constitutional_rejection_market_continuity'
RUNNER = 'scripts/run_synth_did.py'


if __name__ == "__main__":
    raise SystemExit(rerun(__file__, HYPOTHESIS_ID, RUNNER))
