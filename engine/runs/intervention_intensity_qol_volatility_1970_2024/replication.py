#!/usr/bin/env python3
"""Replicate this panel run from the preregistered hypothesis spec."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from run_panel_fe import run_one

if __name__ == '__main__':
    print(run_one('intervention_intensity_qol_volatility_1970_2024', force=True, persist_preflight_inconclusive=True))
