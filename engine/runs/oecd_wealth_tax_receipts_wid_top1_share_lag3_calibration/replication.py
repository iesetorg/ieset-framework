#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
runner = root / 'scripts/run_oecd_wealth_tax_wid_top1_calibration.py'
subprocess.run([sys.executable, str(runner), '--replay', *sys.argv[1:]], check=True)
