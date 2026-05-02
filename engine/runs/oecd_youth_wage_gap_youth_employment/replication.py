#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[3]
ns = runpy.run_path(str(ROOT / "scripts" / "generate_oecd_labour_wave.py"))
config = next(c for c in ns["CONFIGS"] if c["id"] == "oecd_youth_wage_gap_youth_employment")
ns["run_one"](config)
