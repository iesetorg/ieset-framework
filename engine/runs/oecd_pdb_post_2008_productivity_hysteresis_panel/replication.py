#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from promote_oecd_pdb_batch03_2026_05_12 import run_one

if __name__ == '__main__':
    print(run_one('oecd_pdb_post_2008_productivity_hysteresis_panel'))
