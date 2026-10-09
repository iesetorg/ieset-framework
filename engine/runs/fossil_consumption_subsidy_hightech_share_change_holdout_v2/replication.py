#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_fossil_consumption_subsidy_hightech_share_change_holdout_v2.py'), '--check'], cwd=root))
