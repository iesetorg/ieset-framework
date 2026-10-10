#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
runner = root / 'scripts/run_oecd_estate_gift_tax_wid_top1_change5_calibration.py'
subprocess.run([sys.executable, str(runner), '--replay', *sys.argv[1:]], check=True)
