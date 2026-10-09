#!/usr/bin/env python3
"""Read-only exact replay of eurozone_distribution_2008_2014_direct_measures_v2."""
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_eurozone_distribution_direct_measures_v2.py'), '--check'], cwd=root))
