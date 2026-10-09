#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_minimum_wage_median_youth_unemployment_2020_2024_v2.py'), '--check'], cwd=root))
