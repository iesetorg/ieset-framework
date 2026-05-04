#!/usr/bin/env python3
"""Replication wrapper for `friedman_negative_income_tax_labour_supply_smaller_than_predicted`.

Delegates to the canonical IESET methodology runner recorded for this run.
This preserves one source of estimation logic while making the run artifact
directly reproducible from engine/runs/friedman_negative_income_tax_labour_supply_smaller_than_predicted/.
"""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from _replication_runner import rerun

HYPOTHESIS_ID = 'friedman_negative_income_tax_labour_supply_smaller_than_predicted'
RUNNER = 'scripts/run_did_callaway_santanna.py'


if __name__ == "__main__":
    raise SystemExit(rerun(__file__, HYPOTHESIS_ID, RUNNER))
