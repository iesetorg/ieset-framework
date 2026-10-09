#!/usr/bin/env python3
"""Read-only pinned replication for oecd_epl_low_education_unemployment_panel_1985_2019."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from promote_welfare_labour_minwage_batches_07_09_a4_2026_05_12 import reproduce_one

if __name__ == '__main__':
    reproduce_one('oecd_epl_low_education_unemployment_panel_1985_2019')
