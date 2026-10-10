#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
subprocess.run([sys.executable, str(root / 'scripts/run_wdi_electricity_schooling_forward_2026.py'), '--verify', *sys.argv[1:]], check=True)
