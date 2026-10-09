#!/usr/bin/env python3
"""Read-only exact replay of the Argentina core-CPI packet."""
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_argentina_core_inflation_2025_2026_durability_holdout_v2.py'), '--check'], cwd=root))
