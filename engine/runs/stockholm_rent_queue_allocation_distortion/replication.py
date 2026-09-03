#!/usr/bin/env python3
"""Replication entrypoint for stockholm_rent_queue_allocation_distortion.

Re-runs the derived-panel checklist evaluator over the same pinned panels;
verdict and metrics are recomputed, not stored.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from run_derived_panel_checklist import run

if __name__ == "__main__":
    result = run('stockholm_rent_queue_allocation_distortion')
    print(result["verdict"], "-", result["reason"])
