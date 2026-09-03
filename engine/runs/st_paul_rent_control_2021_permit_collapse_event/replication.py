#!/usr/bin/env python3
"""Replication entrypoint for st_paul_rent_control_2021_permit_collapse_event.

Re-runs the derived-panel checklist evaluator over the same pinned panels;
verdict and metrics are recomputed, not stored.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from run_derived_panel_checklist import run

if __name__ == "__main__":
    result = run('st_paul_rent_control_2021_permit_collapse_event')
    print(result["verdict"], "-", result["reason"])
