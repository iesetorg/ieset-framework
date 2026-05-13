#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from promote_eurostat_energy_batch06_2026_05_12 import main

if __name__ == '__main__':
    main()
