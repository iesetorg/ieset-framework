#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_us_state_minimum_wage_bite_teen_employment_non_alabama_2026_v2.py'), '--check'], cwd=root))
