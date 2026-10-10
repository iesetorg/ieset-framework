#!/usr/bin/env python3
"""Exact replay of the frozen 12-cell JST family; supply lawful local parquet."""
from pathlib import Path
import subprocess
import sys
runner = Path(__file__).resolve().parents[3] / 'scripts/run_jst_term_spread_macro_2026.py'
raise SystemExit(subprocess.call([sys.executable, str(runner), 'verify', *sys.argv[1:]]))
