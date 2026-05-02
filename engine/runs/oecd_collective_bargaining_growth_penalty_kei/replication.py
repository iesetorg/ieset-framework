#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[3]
ns = runpy.run_path(str(ROOT / "scripts" / "generate_oecd_labour_wave.py"))
config = next(c for c in ns["CONFIGS"] if c["id"] == "oecd_collective_bargaining_growth_penalty_kei")
ns["run_one"](config)
