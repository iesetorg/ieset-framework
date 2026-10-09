#!/usr/bin/env python3
"""Read-only pinned replication for eurostat_nuclear_retention_industrial_price_panel."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from promote_eurostat_energy_batch06_2026_05_12 import reproduce_one

if __name__ == '__main__':
    reproduce_one('eurostat_nuclear_retention_industrial_price_panel')
