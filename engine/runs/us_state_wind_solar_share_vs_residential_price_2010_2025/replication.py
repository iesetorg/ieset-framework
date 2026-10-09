#!/usr/bin/env python3
"""Replicate us_state_wind_solar_share_vs_residential_price_2010_2025 (X-sourced batch 1). Re-runs the committed runner and prints this hypothesis's result."""
from pathlib import Path
import json
import runpy

ROOT = Path(__file__).resolve().parents[3]

if __name__ == "__main__":
    runpy.run_path(str(ROOT / "prereg/x_sourced_2026-10-09/scripts/run_x_hypotheses.py"), run_name="__main__")
    print(json.dumps(json.loads((ROOT / "prereg/x_sourced_2026-10-09/runs/us_state_wind_solar_share_vs_residential_price_2010_2025/results.json").read_text()), indent=1))
