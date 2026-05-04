#!/usr/bin/env python3
"""Replication wrapper for `privatisation_method_mass_voucher_vs_trade_sale`.

Delegates to the canonical IESET methodology runner recorded for this run.
This preserves one source of estimation logic while making the run artifact
directly reproducible from engine/runs/privatisation_method_mass_voucher_vs_trade_sale/.
"""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from _replication_runner import rerun

HYPOTHESIS_ID = 'privatisation_method_mass_voucher_vs_trade_sale'
RUNNER = 'scripts/run_panel_fe.py'


if __name__ == "__main__":
    raise SystemExit(rerun(__file__, HYPOTHESIS_ID, RUNNER))
