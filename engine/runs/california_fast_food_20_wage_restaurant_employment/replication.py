#!/usr/bin/env python3
"""Replicate california_fast_food_20_wage_restaurant_employment (X-sourced batch 1). Re-runs the committed runner and prints this hypothesis's result."""
from pathlib import Path
import json
import runpy

ROOT = Path(__file__).resolve().parents[3]

if __name__ == "__main__":
    runpy.run_path(str(ROOT / "prereg/x_sourced_2026-10-09/scripts/run_x_hypotheses.py"), run_name="__main__")
    print(json.dumps(json.loads((ROOT / "prereg/x_sourced_2026-10-09/runs/california_fast_food_20_wage_restaurant_employment/results.json").read_text()), indent=1))
