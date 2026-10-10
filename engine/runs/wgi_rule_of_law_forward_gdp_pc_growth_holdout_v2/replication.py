#!/usr/bin/env python3
"""Exact replay of one precommitted WGI rule-of-law family member."""
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_wgi_rule_of_law_five_year_holdout_2026.py'), '--check', 'wgi_rule_of_law_forward_gdp_pc_growth_holdout_v2'], cwd=root))
