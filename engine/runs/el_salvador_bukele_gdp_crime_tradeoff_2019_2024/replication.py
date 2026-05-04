#!/usr/bin/env python3
"""Replication wrapper for `el_salvador_bukele_gdp_crime_tradeoff_2019_2024`.

Re-runs the canonical `scripts/run_synth_did.py` pipeline with `--force` so the run artifact can
be reproduced without duplicating methodology code in this directory.
"""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from _replication_runner import rerun

HYPOTHESIS_ID = 'el_salvador_bukele_gdp_crime_tradeoff_2019_2024'
RUNNER = 'scripts/run_synth_did.py'


if __name__ == "__main__":
    raise SystemExit(rerun(__file__, HYPOTHESIS_ID, RUNNER))
