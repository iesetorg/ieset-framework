#!/usr/bin/env python3
"""Read-only exact replay of the pinned historical result packet."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from promote_cross_school_next50_2026_05_12 import reproduce_one

print(json.dumps(reproduce_one('cross_school_smaller_government_growth_1990_2023'), sort_keys=True))
