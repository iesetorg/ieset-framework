#!/usr/bin/env python3
"""Replicate this descriptive run from the preregistered hypothesis spec."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from run_descriptive import run_one

if __name__ == '__main__':
    print(run_one('trade_lib_mercosur_1991_intra_bloc_trade', force=True))
