#!/usr/bin/env python3
"""Replicate this descriptive run from the preregistered hypothesis spec."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from run_descriptive import run_one

if __name__ == '__main__':
    print(run_one('asia_japan_abenomics_retrospective_2013_2023', force=True))
