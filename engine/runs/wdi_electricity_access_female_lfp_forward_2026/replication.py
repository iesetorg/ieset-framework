#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, '-B', str(root / 'scripts/run_wdi_electricity_female_lfp_2026.py'), '--verify']))
