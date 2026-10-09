#!/usr/bin/env python3
"""Read-only field replay of the Atlanta Fed wage-quartile result."""
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_atlanta_fed_wage_quartile_growth_gap_2024_2026.py'), '--check'], cwd=root))
