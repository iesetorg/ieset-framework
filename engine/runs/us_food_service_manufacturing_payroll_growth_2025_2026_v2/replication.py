#!/usr/bin/env python3
"""Read-only field replay of the national BLS payroll packet."""
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_us_food_service_manufacturing_payroll_growth_2025_2026_v2.py'), '--check'], cwd=root))
