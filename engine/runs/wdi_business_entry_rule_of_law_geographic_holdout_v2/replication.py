#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call(
    [sys.executable, str(root / 'scripts/run_business_entry_rule_of_law_geographic_holdout_v2.py'), '--run', '--force'], cwd=root
))
