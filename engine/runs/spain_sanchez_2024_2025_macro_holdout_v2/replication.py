#!/usr/bin/env python3
"""Read-only exact replay of the Spain holdout packet."""
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_spain_sanchez_2024_2025_macro_holdout_v2.py'), '--check'], cwd=root))
