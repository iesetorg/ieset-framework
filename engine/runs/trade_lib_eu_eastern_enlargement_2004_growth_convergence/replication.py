#!/usr/bin/env python3
"""Replicate this DiD run from the preregistered hypothesis spec."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from run_did_callaway_santanna import run_one

if __name__ == '__main__':
    print(run_one('trade_lib_eu_eastern_enlargement_2004_growth_convergence', force=True))
