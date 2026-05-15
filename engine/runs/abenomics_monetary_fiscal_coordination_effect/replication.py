#!/usr/bin/env python3
"""Replicate this event-study run from the preregistered hypothesis spec."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.run_event_study import run_one

if __name__ == '__main__':
    print(run_one('abenomics_monetary_fiscal_coordination_effect', force=True))
