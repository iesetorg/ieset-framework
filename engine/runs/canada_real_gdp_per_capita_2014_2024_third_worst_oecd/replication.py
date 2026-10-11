#!/usr/bin/env python3
"""Replicate canada_real_gdp_per_capita_2014_2024_third_worst_oecd (X-sourced batch 2). Re-runs the committed runner and prints this hypothesis's result."""
from pathlib import Path
import json
import runpy

ROOT = Path(__file__).resolve().parents[3]

if __name__ == "__main__":
    runpy.run_path(str(ROOT / "prereg/x_sourced_2026-10-09_batch2/scripts/run_batch2.py"), run_name="__main__")
    print(json.dumps(json.loads((ROOT / "prereg/x_sourced_2026-10-09_batch2/runs/canada_real_gdp_per_capita_2014_2024_third_worst_oecd/results.json").read_text()), indent=1))
