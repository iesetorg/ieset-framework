#!/usr/bin/env python3
"""Replicate germany_eu_industrial_electricity_price_vs_wind_solar_share (X-sourced batch 2). Re-runs the committed runner and prints this hypothesis's result."""
from pathlib import Path
import json
import runpy

ROOT = Path(__file__).resolve().parents[3]

if __name__ == "__main__":
    runpy.run_path(str(ROOT / "prereg/x_sourced_2026-10-09_batch2/scripts/run_batch2.py"), run_name="__main__")
    print(json.dumps(json.loads((ROOT / "prereg/x_sourced_2026-10-09_batch2/runs/germany_eu_industrial_electricity_price_vs_wind_solar_share/results.json").read_text()), indent=1))
