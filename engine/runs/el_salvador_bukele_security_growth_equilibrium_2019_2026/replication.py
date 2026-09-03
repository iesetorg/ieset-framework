#!/usr/bin/env python3
"""Replication entrypoint for el_salvador_bukele_security_growth_equilibrium_2019_2026.

Re-runs the derived-panel checklist evaluator over the same pinned panels;
verdict and metrics are recomputed, not stored.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from run_derived_panel_checklist import run

if __name__ == "__main__":
    result = run('el_salvador_bukele_security_growth_equilibrium_2019_2026')
    print(result["verdict"], "-", result["reason"])
