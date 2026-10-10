#!/usr/bin/env python3
"""Exact replay of the precommitted V-Dem geographic holdout."""
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_vdem_rule_of_law_corruption_holdout_v2.py'), '--check'], cwd=root))
