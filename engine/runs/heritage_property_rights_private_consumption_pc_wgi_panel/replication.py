#!/usr/bin/env python3
"""Replication wrapper for `heritage_property_rights_private_consumption_pc_wgi_panel`.

Delegates to the canonical IESET panel runner for the registered WGI/WDI
heritage-graduation specification.
"""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from _replication_runner import rerun

HYPOTHESIS_ID = 'heritage_property_rights_private_consumption_pc_wgi_panel'
RUNNER = "scripts/run_panel_fe.py"


if __name__ == "__main__":
    raise SystemExit(rerun(__file__, HYPOTHESIS_ID, RUNNER))
